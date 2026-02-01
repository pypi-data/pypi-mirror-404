import os
import re
import sys
import timeit
from pathlib import PurePosixPath

import h5py
import numpy as np
import psutil
from mpi4py import MPI
from tqdm import tqdm

#from .rgd import rgd ## no!
from .gradient import gradient
from .h5 import h5_chunk_sizer, h5_print_contents
from .utils import even_print, format_time_string

# ======================================================================

def _calc_turb_budget_xpln(self, **kwargs):
    '''
    calculate budget of turbulent kinetic energy (k)
    -----
    - dimensional [SI]
    - designed for analyzing unsteady, thin planes in [x]
    -----
    SI units of terms are [kg/(m·s³)] or [kg m^-1 s^-3]
    normalize with
    * ν / u**4 / ρ --> *[ kg^-1 m s^3]
    or
    / ( u**4 * ρ / ν ) --> /[kg m^-1 s^-3]
    -----
    Pirozzoli Grasso Gatski (2004)
    Direct numerical simulation and analysis of a spatially evolving supersonic turbulent boundary layer at M=2.25
    https://doi.org/10.1063/1.1637604
    -----
    Gaurini Moser Shariff Wray (2000)
    Direct numerical simulation of a supersonic turbulent boundary layer at Mach 2.5
    https://doi.org/10.1017/S0022112000008466
    '''
    
    rgd_meta = type(self) ## workaround for using rgd()
    
    if (self.rank==0):
        verbose = True
    else:
        verbose = False
    
    if verbose: print('\n'+'rgd.calc_turb_budget_xpln()'+'\n'+72*'-')
    t_start_func = timeit.default_timer()
    
    if (self.fsubtype!='unsteady'):
        raise RuntimeError(f"file subtype must be 'unsteady' but is '{str(self.fsubtype)}'")
    
    if not self.usingmpi:
        raise ValueError('rgd.calc_turb_budget_xpln() currently only works in MPI mode')
    
    rx = kwargs.get('rx',1)
    ry = kwargs.get('ry',1)
    rz = kwargs.get('rz',1)
    rt = kwargs.get('rt',1)
    
    ## number of subdivisions per rank [t] range
    ct = kwargs.get( 'ct' , int((self.nt//self.n_ranks)//4) )
    if not isinstance(ct,int) or (ct<1):
        raise TypeError('ct should be a positive non-zero int')
    
    # st = kwargs.get('st',1)
    # if not isinstance(st,int) or (st<1):
    #     raise TypeError('st should be a positive non-zero int')
    # if (self.nt%st!=0):
    #     raise ValueError('nt not divisible by st')
    
    force = kwargs.get('force',False)
    
    fn_h5_mean = kwargs.get('fn_h5_mean',None)
    fn_h5_out  = kwargs.get('fn_h5_out',None)
    
    save_unsteady      = kwargs.get('save_unsteady',False)
    fn_h5_out_unsteady = kwargs.get('fn_h5_out_unsteady',None)
    
    acc          = kwargs.get('acc', 6)
    edge_stencil = kwargs.get('edge_stencil', 'half')
    
    chunk_kb         = kwargs.get('chunk_kb',4*1024) ## h5 chunk size: default 4 [MB]
    chunk_constraint = kwargs.get('chunk_constraint',(1,None,None,None)) ## the 'constraint' parameter for sizing h5 chunks
    chunk_base       = kwargs.get('chunk_base',2)
    
    ## only distribute data in [t]
    if (rx!=1):
        raise AssertionError('rx!=1')
    if (ry!=1):
        raise AssertionError('ry!=1')
    if (rz!=1):
        raise AssertionError('rz!=1')
    
    if not isinstance(rt,int) or (rt<1):
        raise ValueError('rt should be a positive non-zero int')
    
    if (rx*ry*rz*rt != self.n_ranks):
        raise AssertionError('rx*ry*rz*rt != self.n_ranks')
    if (rx>self.nx):
        raise AssertionError('rx>self.nx')
    if (ry>self.ny):
        raise AssertionError('ry>self.ny')
    if (rz>self.nz):
        raise AssertionError('rz>self.nz')
    if (rt>self.nt):
        raise AssertionError('rt>self.nt')
    
    # ===
    
    rtl_ = np.array_split(np.arange(self.nt,dtype=np.int64),rt)
    rtl = [[b[0],b[-1]+1] for b in rtl_ ]
    rt1,rt2 = rtl[self.rank]
    ntr = rt2 - rt1
    
    if (ntr<1):
        print(f'rank {self.rank:d} ntr < 1')
        self.comm.Abort(1)
    if (ntr<ct):
        print(f'rank {self.rank:d} ntr < ct')
        self.comm.Abort(1)
    
    ## [t] sub chunk range --> ctl = list of ranges in rt1:rt2
    ctl_ = np.array_split( np.arange(rt1,rt2) , ct )
    ctl = [[b[0],b[-1]+1] for b in ctl_ ]
    
    ## check that no sub ranges are <=1
    for a_ in [ ctl_[1]-ctl_[0] for ctl_ in ctl ]:
        if (a_ <= 1):
            #raise ValueError
            print(f'rank {self.rank:d} has [t] a chunk subrange <= 1')
            self.comm.Abort(1)
    
    ## the average sub [t] chunk size on this rank
    #avg_ntc = np.mean( [ ctl_[1]-ctl_[0] for ctl_ in ctl ] )
    #min_ntc =     min( [ ctl_[1]-ctl_[0] for ctl_ in ctl ] )
    #max_ntc =     max( [ ctl_[1]-ctl_[0] for ctl_ in ctl ] )
    
    ## get all ntcs
    my_ntcs = [ ctl_[1]-ctl_[0] for ctl_ in ctl ]
    G = self.comm.gather([ self.rank , my_ntcs ], root=0)
    G = self.comm.bcast(G, root=0)
    
    allntcs = []
    for G_ in G:
        allntcs += G_[1]
    allntcs = np.array( allntcs , dtype=np.int64 )
    
    avg_ntc = np.mean( allntcs , dtype=np.float64 )
    min_ntc = allntcs.min()
    max_ntc = allntcs.max()
    
    if 1: ## check that [t] sub-chunk ranges are correct
        
        mytimeindices = []
        for ctl_ in ctl:
            ct1, ct2 = ctl_
            mytimeindices += [ ti_ for ti_ in self.ti[ct1:ct2] ]
        
        G = self.comm.gather([ self.rank , mytimeindices ], root=0)
        G = self.comm.bcast(G, root=0)
        
        alltimeindices = []
        for G_ in G:
            alltimeindices += G_[1]
        alltimeindices = np.array( sorted(alltimeindices), dtype=np.int64 )
        
        if not np.array_equal( alltimeindices , self.ti ):
            raise AssertionError
        if not np.array_equal( alltimeindices , np.arange(self.nt, dtype=np.int64) ):
            raise AssertionError
    
    self.comm.Barrier()
    
    ## mean file name (for reading)
    if (fn_h5_mean is None):
        fname_path = os.path.dirname(self.fname)
        fname_base = os.path.basename(self.fname)
        fname_root, fname_ext = os.path.splitext(fname_base)
        fname_mean_h5_base = fname_root+'_mean.h5'
        #fn_h5_mean = os.path.join(fname_path, fname_mean_h5_base)
        fn_h5_mean = str(PurePosixPath(fname_path, fname_mean_h5_base))
        #fn_h5_mean = Path(fname_path, fname_mean_h5_base)
    
    if not os.path.isfile(fn_h5_mean):
        raise FileNotFoundError('%s not found!'%fn_h5_mean)
    
    ## turb_budget .h5 file name (for writing) --> AVERAGED
    if (fn_h5_out is None):
        fname_path = os.path.dirname(self.fname)
        fname_base = os.path.basename(self.fname)
        fname_root, fname_ext = os.path.splitext(fname_base)
        fname_root = re.findall(r'io\S+_mpi_[0-9]+', fname_root)[0]
        fn_h5_out_base = fname_root+'_turb_budget.h5'
        fn_h5_out = str(PurePosixPath(fname_path, fn_h5_out_base))
    
    if os.path.isfile(fn_h5_out) and (force is False):
        raise ValueError(f'{fn_h5_out} already present & force=False')
    
    ## turb_budget .h5 file name (for writing) --> UNSTEADY
    if save_unsteady:
        if (fn_h5_out_unsteady is None):
            fname_path = os.path.dirname(self.fname)
            fname_base = os.path.basename(self.fname)
            fname_root, fname_ext = os.path.splitext(fname_base)
            fname_root = re.findall(r'io\S+_mpi_[0-9]+', fname_root)[0]
            fn_h5_out_unsteady_base = fname_root+'_turb_budget_unsteady.h5'
            fn_h5_out_unsteady = str(PurePosixPath(fname_path, fn_h5_out_unsteady_base))
        
        if os.path.isfile(fn_h5_out_unsteady) and (force is False):
            raise ValueError(f'{fn_h5_out_unsteady} already present & force=False')
    
    if verbose: even_print('fn_h5'      , self.fname )
    if verbose: even_print('fn_h5_mean' , fn_h5_mean )
    if verbose: even_print('fn_h5_out'  , fn_h5_out  )
    if verbose: print(72*'-')
    if verbose: even_print('save unsteady' , str(save_unsteady) )
    if verbose and save_unsteady:
        even_print('unsteady file' , fn_h5_out_unsteady )
    if verbose: print(72*'-')
    
    # ===
    
    if verbose: even_print('nx' , f'{self.nx:d}' )
    if verbose: even_print('ny' , f'{self.ny:d}' )
    if verbose: even_print('nz' , f'{self.nz:d}' )
    if verbose: even_print('nt' , f'{self.nt:d}' )
    if verbose: print(72*'-')
    if verbose: even_print('rt'  , f'{rt:d}' )
    if verbose: even_print('ct'  , f'{ct:d}' )
    #if verbose: even_print('st'  , f'{st:d}' )
    if verbose: even_print('ntr' , f'{ntr:d}' )
    if verbose: even_print('avg [t] chunk nt' , f'{avg_ntc:0.6f}' )
    if verbose: even_print('min [t] chunk nt' , f'{min_ntc:d}' )
    if verbose: even_print('max [t] chunk nt' , f'{max_ntc:d}' )
    if verbose: print(72*'-')
    
    # === init outfiles
    
    #if verbose: print(72*'*')
    if verbose: print(fn_h5_out)
    if verbose: print(len(fn_h5_out)*'-')
    
    ## initialize file: turbulent kinetic energy budget, AVERAGED
    #with rgd(fn_h5_out, 'w', force=force, driver='mpio', comm=self.comm) as f1:
    with rgd_meta(fn_h5_out, 'w', force=force, driver='mpio', comm=self.comm) as f1:
        
        f1.init_from_rgd(self.fname, t_info=False)
        
        ## set some top-level attributes
        #f1.attrs['duration_avg'] = duration_avg ## duration of mean
        f1.attrs['duration_avg'] = self.t[-1] - self.t[0]
        #f1_mean.attrs['duration_avg'] = self.duration
        f1.attrs['dt'] = self.t[1] - self.t[0]
        #f1.attrs['fclass'] = 'rgd'
        f1.attrs['fsubtype'] = 'mean'
        
        shape = (1,f1.nz,f1.ny,f1.nx)
        chunks = h5_chunk_sizer(nxi=shape, constraint=chunk_constraint, size_kb=chunk_kb, base=chunk_base, itemsize=8)
        
        data_gb = 8 * 1 * f1.nz*f1.ny*f1.nx / 1024**3
        
        for dss in ['production','dissipation','transport','diffusion','p_dilatation','p_diffusion']:
            
            if verbose:
                even_print('initializing data/%s'%(dss,),'%0.1f [GB]'%(data_gb,))
            
            dset = f1.create_dataset(
                        f'data/{dss}', 
                        shape=shape, 
                        dtype=np.float64,
                        chunks=chunks,
                        #data=np.full(shape,0.,np.float64),
                        )
            
            chunk_kb_ = np.prod(dset.chunks) * dset.dtype.itemsize / 1024. ## actual
            if verbose:
                even_print('chunk shape (t,z,y,x)','%s'%str(dset.chunks))
                even_print('chunk size','%i [KB]'%int(round(chunk_kb_)))
        
        # === replace dims/t array --> take last time of series
        if ('dims/t' in f1):
            del f1['dims/t']
        f1.create_dataset('dims/t', data=np.array([self.t[-1]],dtype=np.float64), )
        
        if hasattr(f1, 'duration_avg'):
            if verbose: even_print('duration_avg', '%0.2f'%f1.duration_avg)
    
    if verbose: print(72*'-')
    
    ## initialize file: turbulent kinetic energy budget, UNSTEADY
    if save_unsteady:
        
        if verbose: print(fn_h5_out_unsteady)
        if verbose: print(len(str(fn_h5_out_unsteady))*'-')
        
        #with rgd(fn_h5_out_unsteady, 'w', force=force, driver='mpio', comm=self.comm) as f1:
        with rgd_meta(fn_h5_out_unsteady, 'w', force=force, driver='mpio', comm=self.comm) as f1:
            
            f1.init_from_rgd(self.fname, t_info=True)
            
            ## set some top-level attributes
            #f1.attrs['duration_avg'] = duration_avg ## duration of mean
            f1.attrs['duration_avg'] = self.t[-1] - self.t[0]
            #f1_mean.attrs['duration_avg'] = self.duration
            f1.attrs['dt'] = self.t[1] - self.t[0]
            #f1.attrs['fclass'] = 'rgd'
            f1.attrs['fsubtype'] = 'unsteady'
            
            shape = (self.nt,f1.nz,f1.ny,f1.nx)
            #chunks = h5_chunk_sizer(nxi=shape, constraint=chunk_constraint, size_kb=chunk_kb, base=chunk_base, itemsize=4)
            chunks = self['data/u'].chunks ## use chunk pattern of this file
            
            data_gb = 4*self.nt*f1.nz*f1.ny*f1.nx / 1024**3
            
            for dss in ['production','dissipation','transport','diffusion']: #,'p_dilatation','p_diffusion']:
                
                if verbose:
                    even_print('initializing data/%s'%(dss,),'%0.1f [GB]'%(data_gb,))
                
                dset = f1.create_dataset(
                            f'data/{dss}', 
                            shape=shape, 
                            dtype=np.float32,
                            chunks=chunks,
                            #data=np.full(shape,0.,np.float32),
                            )
                
                chunk_kb_ = np.prod(dset.chunks) * dset.dtype.itemsize / 1024. ## actual
                if verbose:
                    even_print('chunk shape (t,z,y,x)','%s'%str(dset.chunks))
                    even_print('chunk size','%i [KB]'%int(round(chunk_kb_)))
        
        if verbose: print(72*'-')
    
    self.comm.Barrier()
    
    # ===
    
    ## OPEN the mean file... make sure to close later!
    #hf_mean = rgd(fn_h5_mean, 'r', driver='mpio', comm=self.comm)
    hf_mean = rgd_meta(fn_h5_mean, 'r', driver='mpio', comm=self.comm)
    
    ## verify contents of the mean file
    np.testing.assert_allclose( hf_mean.x       , self.x       , atol=1e-12, rtol=1e-12 )
    np.testing.assert_allclose( hf_mean.y       , self.y       , atol=1e-12, rtol=1e-12 )
    np.testing.assert_allclose( hf_mean.z       , self.z       , atol=1e-12, rtol=1e-12 )
    np.testing.assert_allclose( hf_mean.lchar   , self.lchar   , atol=1e-12, rtol=1e-12 )
    np.testing.assert_allclose( hf_mean.U_inf   , self.U_inf   , atol=1e-12, rtol=1e-12 )
    np.testing.assert_allclose( hf_mean.T_inf   , self.T_inf   , atol=1e-12, rtol=1e-12 )
    np.testing.assert_allclose( hf_mean.rho_inf , self.rho_inf , atol=1e-12, rtol=1e-12 )
    if (hf_mean.fsubtype!='mean'):
        raise ValueError
    
    # ===
    
    data = {} ## dict to be output to .dat file
    
    if ('data_dim' not in hf_mean):
        raise ValueError('group data_dim not present')
    
    ## put all data from 'data_dim' into the dictionary data which will be pickled at the end
    for dsn in hf_mean['data_dim'].keys():
        d_ = np.copy( hf_mean[f'data_dim/{dsn}'][()] )
        if (d_.ndim == 0):
            d_ = float(d_)
        data[dsn] = d_
    
    ## 1D
    #rho_avg = np.copy( hf_mean['data_dim/rho'][()] )
    #u_avg   = np.copy( hf_mean['data_dim/u'][()]   )
    #v_avg   = np.copy( hf_mean['data_dim/v'][()]   )
    #w_avg   = np.copy( hf_mean['data_dim/w'][()]   )
    #T_avg   = np.copy( hf_mean['data_dim/T'][()]   )
    #p_avg   = np.copy( hf_mean['data_dim/p'][()]   )
    
    ## 0D
    u_tau    = float( hf_mean['data_dim/u_tau'][()]    )
    nu_wall  = float( hf_mean['data_dim/nu_wall'][()]  )
    rho_wall = float( hf_mean['data_dim/rho_wall'][()] )
    #T_wall   = float( hf_mean['data_dim/T_wall'][()]   )
    d99      = float( hf_mean['data_dim/d99'][()]      )
    u_99     = float( hf_mean['data_dim/u_99'][()]     )
    Re_tau   = float( hf_mean['data_dim/Re_tau'][()]   )
    Re_theta = float( hf_mean['data_dim/Re_theta'][()] )
    #sc_u_in  = float( hf_mean['data_dim/sc_u_in'][()]  )
    sc_l_in  = float( hf_mean['data_dim/sc_l_in'][()]  )
    sc_t_in  = float( hf_mean['data_dim/sc_t_in'][()]  )
    #sc_u_out = float( hf_mean['data_dim/sc_u_out'][()] )
    #sc_l_out = float( hf_mean['data_dim/sc_l_out'][()] )
    #sc_t_out = float( hf_mean['data_dim/sc_t_out'][()] )
    
    ## 0D scalars
    lchar   = self.lchar   ; data['lchar']   = lchar
    U_inf   = self.U_inf   ; data['U_inf']   = U_inf
    rho_inf = self.rho_inf ; data['rho_inf'] = rho_inf
    T_inf   = self.T_inf   ; data['T_inf']   = T_inf
    
    #data['M_inf'] = self.M_inf
    data['Ma'] = self.Ma
    data['Pr'] = self.Pr
    
    ## read in 1D coordinate arrays & re-dimensionalize
    x = np.copy( self['dims/x'][()] * self.lchar )
    y = np.copy( self['dims/y'][()] * self.lchar )
    z = np.copy( self['dims/z'][()] * self.lchar )
    t = np.copy( self['dims/t'][()] * self.tchar )
    
    ## dimensional [s]
    dt = self.dt * self.tchar
    np.testing.assert_allclose(dt, t[1]-t[0], rtol=1e-14, atol=1e-14)
    
    t_meas = self.duration * self.tchar
    np.testing.assert_allclose(t_meas, t.max()-t.min(), rtol=1e-14, atol=1e-14)
    
    t_eddy = t_meas / ( d99 / u_tau )
    
    ## check if constant Δz (calculate Δz+ later)
    dz0 = np.diff(z)[0]
    if not np.all(np.isclose(np.diff(z), dz0, rtol=1e-7)):
        raise NotImplementedError
    np.testing.assert_allclose(dz0, z[1]-z[0], rtol=1e-14, atol=1e-14)
    
    zrange = z.max() - z.min()
    np.testing.assert_allclose(zrange, z[-1]-z[0], rtol=1e-14, atol=1e-14)
    
    nx = self.nx ; data['nx'] = nx
    ny = self.ny ; data['ny'] = ny
    nz = self.nz ; data['nz'] = nz
    nt = self.nt ; data['nt'] = nt
    
    ## add data to dict that gets output
    data['x'] = x
    data['y'] = y
    data['z'] = z
    data['t'] = t
    data['t_meas'] = t_meas
    data['dt'] = dt
    data['dz0'] = dz0
    data['zrange'] = zrange
    
    if verbose: even_print('Δt/tchar','%0.8f'%(dt/self.tchar))
    if verbose: even_print('Δt','%0.3e [s]'%(dt,))
    if verbose: even_print('duration/tchar','%0.1f'%(self.duration,))
    if verbose: even_print('duration','%0.3e [s]'%(self.duration*self.tchar,))
    if verbose: print(72*'-')
    
    ## report
    if verbose:
        even_print('dt'     , f'{dt     :0.5e} [s]' )
        even_print('t_meas' , f'{t_meas :0.5e} [s]' )
        even_print('dz0'    , f'{dz0    :0.5e} [m]' )
        even_print('zrange' , f'{zrange :0.5e} [m]' )
        print(72*'-')
    
    ## report
    if verbose:
        even_print( 'Reτ'             , f'{Re_tau:0.1f}'           )
        even_print( 'Reθ'             , f'{Re_theta:0.1f}'         )
        even_print( 'δ99'             , f'{d99:0.5e} [m]'          )
        even_print( 'δν=(ν_wall/u_τ)' , f'{sc_l_in:0.5e} [m]'      )
        even_print( 'U_inf'           , f'{self.U_inf:0.3f} [m/s]' )
        even_print( 'uτ'              , f'{u_tau:0.3f} [m/s]'      )
        even_print( 'ν_wall'          , f'{nu_wall:0.5e} [m²/s]'   )
        even_print( 'ρ_wall'          , f'{rho_wall:0.6f} [kg/m³]' )
        even_print( 'Δz+'             , f'{dz0/sc_l_in:0.3f}'      )
        even_print( 'zrange/δ99'      , f'{zrange/d99:0.3f}'       )
        even_print( 'Δt+'             , f'{dt/sc_t_in:0.3f}'       )
        print(72*'-')
    
    ## report
    if verbose:
        even_print('t_meas/(δ99/u_τ) = t_eddy' , '%0.2f'%t_eddy)
        even_print('t_meas/(δ99/u99)'          , '%0.2f'%(t_meas/(d99/u_99)))
        even_print('t_meas/(20·δ99/u99)'       , '%0.2f'%(t_meas/(20*d99/u_99)))
        print(72*'-')
    
    # ===
    
    ## copy AVG [u,v,w] into memory... DIMENSIONAL
    u_re = np.copy( U_inf * hf_mean['data/u'][0,:,:,:].T    ).astype(np.float64)
    v_re = np.copy( U_inf * hf_mean['data/v'][0,:,:,:].T    ).astype(np.float64)
    w_re = np.copy( U_inf * hf_mean['data/w'][0,:,:,:].T    ).astype(np.float64)
    u_fv = np.copy( U_inf * hf_mean['data/u_fv'][0,:,:,:].T ).astype(np.float64)
    v_fv = np.copy( U_inf * hf_mean['data/v_fv'][0,:,:,:].T ).astype(np.float64)
    w_fv = np.copy( U_inf * hf_mean['data/w_fv'][0,:,:,:].T ).astype(np.float64)
    
    p_re = np.copy( rho_inf * U_inf**2 * hf_mean['data/p'][0,:,:,:].T ).astype(np.float64)
    
    ## get Reynolds avg strain tensor elements
    #dudx_re = gradient( u=u_re , x=x , axis=0 , acc=acc , edge_stencil=edge_stencil )[:,:,:,np.newaxis]
    #dudy_re = gradient( u=u_re , x=y , axis=1 , acc=acc , edge_stencil=edge_stencil )[:,:,:,np.newaxis]
    #dudz_re = gradient( u=u_re , x=z , axis=2 , acc=acc , edge_stencil=edge_stencil )[:,:,:,np.newaxis]
    #dvdx_re = gradient( u=v_re , x=x , axis=0 , acc=acc , edge_stencil=edge_stencil )[:,:,:,np.newaxis]
    #dvdy_re = gradient( u=v_re , x=y , axis=1 , acc=acc , edge_stencil=edge_stencil )[:,:,:,np.newaxis]
    #dvdz_re = gradient( u=v_re , x=z , axis=2 , acc=acc , edge_stencil=edge_stencil )[:,:,:,np.newaxis]
    #dwdx_re = gradient( u=w_re , x=x , axis=0 , acc=acc , edge_stencil=edge_stencil )[:,:,:,np.newaxis]
    #dwdy_re = gradient( u=w_re , x=y , axis=1 , acc=acc , edge_stencil=edge_stencil )[:,:,:,np.newaxis]
    #dwdz_re = gradient( u=w_re , x=z , axis=2 , acc=acc , edge_stencil=edge_stencil )[:,:,:,np.newaxis]
    
    ## get Favre avg strain tensor elements
    dudx_fv = gradient( u=u_fv , x=x , axis=0 , acc=acc , edge_stencil=edge_stencil )[:,:,:,np.newaxis]
    dudy_fv = gradient( u=u_fv , x=y , axis=1 , acc=acc , edge_stencil=edge_stencil )[:,:,:,np.newaxis]
    dudz_fv = gradient( u=u_fv , x=z , axis=2 , acc=acc , edge_stencil=edge_stencil )[:,:,:,np.newaxis]
    dvdx_fv = gradient( u=v_fv , x=x , axis=0 , acc=acc , edge_stencil=edge_stencil )[:,:,:,np.newaxis]
    dvdy_fv = gradient( u=v_fv , x=y , axis=1 , acc=acc , edge_stencil=edge_stencil )[:,:,:,np.newaxis]
    dvdz_fv = gradient( u=v_fv , x=z , axis=2 , acc=acc , edge_stencil=edge_stencil )[:,:,:,np.newaxis]
    dwdx_fv = gradient( u=w_fv , x=x , axis=0 , acc=acc , edge_stencil=edge_stencil )[:,:,:,np.newaxis]
    dwdy_fv = gradient( u=w_fv , x=y , axis=1 , acc=acc , edge_stencil=edge_stencil )[:,:,:,np.newaxis]
    dwdz_fv = gradient( u=w_fv , x=z , axis=2 , acc=acc , edge_stencil=edge_stencil )[:,:,:,np.newaxis]
    
    ## accumulators for per-timestep sum, at end gets multiplied by (1/nt) to get average
    unsteady_production_sum   = np.zeros((nx,ny,nz,1), dtype=np.float64, order='C')
    unsteady_dissipation_sum  = np.zeros((nx,ny,nz,1), dtype=np.float64, order='C')
    unsteady_transport_sum    = np.zeros((nx,ny,nz,1), dtype=np.float64, order='C')
    unsteady_diffusion_sum    = np.zeros((nx,ny,nz,1), dtype=np.float64, order='C')
    unsteady_p_diffusion_sum  = np.zeros((nx,ny,nz,1), dtype=np.float64, order='C')
    unsteady_p_dilatation_sum = np.zeros((nx,ny,nz,1), dtype=np.float64, order='C')
    
    # ==============================================================
    # check memory
    # ==============================================================
    
    hostname = MPI.Get_processor_name()
    mem_free_gb = psutil.virtual_memory().free / 1024**3
    G = self.comm.gather([ self.rank , hostname , mem_free_gb ], root=0)
    G = self.comm.bcast(G, root=0)
    
    ## multiple ranks per node
    host_mem = {}
    for rank, host, mem in G:
        if (host not in host_mem) or (mem < host_mem[host]):
            host_mem[host] = mem
    total_free = sum(host_mem.values())
    
    if verbose:
        for key,value in host_mem.items():
            even_print(f'RAM free {key}', f'{int(np.floor(value)):d} [GB]')
        print(72*'-')
        even_print('RAM free (local,min)', f'{int(np.floor(min(host_mem.values()))):d} [GB]')
        even_print('RAM free (global)', f'{int(np.floor(total_free)):d} [GB]')
    
    shape_read = ( nx, ny, nz, max_ntc ) ## local
    if verbose: even_print('read shape (local,max)', f'[{nx:d},{ny:d},{nz:d},{max_ntc:d}]')
    data_gb = np.dtype(np.float64).itemsize * np.prod(shape_read) / 1024**3
    if verbose: even_print('read size (local)', f'{data_gb:0.2f} [GB]')
    if verbose: even_print('read size (global)', f'{int(np.ceil(data_gb*rt)):d} [GB]')
    
    fac = 65
    if verbose: even_print(f'read size (global) ×{fac:d}', f'{int(np.ceil(data_gb*rt*fac)):d} [GB]')
    ram_usage_est = data_gb*rt*fac/total_free
    if verbose: even_print('RAM usage estimate', f'{100*ram_usage_est:0.1f} [%]')
    
    self.comm.Barrier()
    if (ram_usage_est>0.90):
        print('RAM consumption might be too high. exiting.')
        self.comm.Abort(1)
    
    if verbose:
        print(72*'-')
    
    # ==============================================================
    # main loop
    # ==============================================================
    
    if verbose:
        progress_bar = tqdm(
            total=ct,
            ncols=100,
            desc='turb budget',
            leave=True,
            file=sys.stdout,
            mininterval=0.1,
            smoothing=0.,
            #bar_format="\033[B{l_bar}{bar}| {n}/{total} [{percentage:.1f}%] {elapsed}/{remaining}\033[A\n\b",
            bar_format="{l_bar}{bar}| {n}/{total} [{percentage:.1f}%] {elapsed}/{remaining}",
            ascii="░█",
            colour='#FF6600',
            )
    
    ct_counter=0
    for ctl_ in ctl:
        ct_counter += 1
        ct1, ct2 = ctl_
        ntc = ct2 - ct1
        
        G = self.comm.gather([ self.rank , ntc ], root=0)
        G = self.comm.bcast(G, root=0)
        ntc_global = sum( [ g[1] for g in G ] )
        
        if (ct>1):
            if verbose:
                mesg = f'[t] sub chunk {ct_counter:d}/{ct:d}'
                tqdm.write( mesg )
                tqdm.write( '-'*len(mesg) )
                tqdm.write( even_print('nt in chunk', f'{ntc_global:d}', s=True) )
        
        # === read unsteady data
        
        ss1 = ['u','v','w','T','rho','p']
        ss2 = ['uI','vI','wI', 'uII','vII','wII', 'pI'] ## 'TI','rhoI'
        
        ## data buffer
        formats = [ np.float64 for s in ss1+ss2 ]
        shape   = (nx,ny,nz,ntc)
        dd      = np.zeros(shape=shape, dtype={'names':ss1+ss2, 'formats':formats}, order='C')
        
        ## read DIMLESS u,v,w,T,rho,p
        for ss in ss1:
            dset = self['data/%s'%ss]
            self.comm.Barrier()
            t_start = timeit.default_timer()
            with dset.collective:
                dd[ss] = dset[ct1:ct2,:,:,:].T
            self.comm.Barrier()
            t_delta = timeit.default_timer() - t_start
            data_gb = dset.dtype.itemsize * nx*ny*nz * ntc_global / 1024**3
            if verbose:
                tqdm.write( even_print('read: %s'%ss, '%0.3f [GB]  %0.3f [s]  %0.3f [GB/s]'%(data_gb,t_delta,(data_gb/t_delta)), s=True) )
        
        ## re-dimensionalize unsteady data
        dd['u'][:,:,:,:]   *= U_inf
        dd['v'][:,:,:,:]   *= U_inf
        dd['w'][:,:,:,:]   *= U_inf
        dd['T'][:,:,:,:]   *= T_inf
        dd['rho'][:,:,:,:] *= rho_inf
        dd['p'][:,:,:,:]   *= ( rho_inf * U_inf**2 )
        
        ## calculate DIMENSIONAL primes
        dd['uI'][:,:,:,:]  = dd['u'] - u_re[:,:,:,np.newaxis]
        dd['vI'][:,:,:,:]  = dd['v'] - v_re[:,:,:,np.newaxis]
        dd['wI'][:,:,:,:]  = dd['w'] - w_re[:,:,:,np.newaxis]
        dd['uII'][:,:,:,:] = dd['u'] - u_fv[:,:,:,np.newaxis]
        dd['vII'][:,:,:,:] = dd['v'] - v_fv[:,:,:,np.newaxis]
        dd['wII'][:,:,:,:] = dd['w'] - w_fv[:,:,:,np.newaxis]
        dd['pI'][:,:,:,:]  = dd['p'] - p_re[:,:,:,np.newaxis]
        
        if verbose: tqdm.write(72*'-')
        
        data_gb = dd.nbytes / 1024**3
        if verbose:
            tqdm.write(even_print('unsteady data (rank)', f'{data_gb:0.1f} [GB]', s=True))
        
        # === make VIEWS of the numpy structured array for convenience
        
        #u   = dd['u'][:,:,:,:]
        #v   = dd['v'][:,:,:,:]
        #w   = dd['w'][:,:,:,:]
        T   = dd['T'][:,:,:,:]
        #p   = dd['p'][:,:,:,:]
        rho = dd['rho'][:,:,:,:]
        
        uI  = dd['uI'][:,:,:,:]
        vI  = dd['vI'][:,:,:,:]
        wI  = dd['wI'][:,:,:,:]
        uII = dd['uII'][:,:,:,:]
        vII = dd['vII'][:,:,:,:]
        wII = dd['wII'][:,:,:,:]
        pI  = dd['pI'][:,:,:,:]
        
        mu = np.copy( self.C_Suth * T**(3/2) / (T + self.S_Suth) )
        #nu = np.copy( mu / rho )
        
        # dd = None ; del dd
        
        self.comm.Barrier()
        mem_free_gb = psutil.virtual_memory().free/1024**3
        if verbose:
            tqdm.write(even_print('mem free', f'{mem_free_gb:0.1f} [GB]', s=True))
        
        # === get gradients
        
        t_start = timeit.default_timer() ## rank 0 only
        
        #dudx   = gradient(u, x, acc=acc, edge_stencil=edge_stencil, axis=0)
        #dudy   = gradient(u, y, acc=acc, edge_stencil=edge_stencil, axis=1)
        #dudz   = gradient(u, z, acc=acc, edge_stencil=edge_stencil, axis=2)
        #dvdx   = gradient(v, x, acc=acc, edge_stencil=edge_stencil, axis=0)
        #dvdy   = gradient(v, y, acc=acc, edge_stencil=edge_stencil, axis=1)
        #dvdz   = gradient(v, z, acc=acc, edge_stencil=edge_stencil, axis=2)
        #dwdx   = gradient(w, x, acc=acc, edge_stencil=edge_stencil, axis=0)
        #dwdy   = gradient(w, y, acc=acc, edge_stencil=edge_stencil, axis=1)
        #dwdz   = gradient(w, z, acc=acc, edge_stencil=edge_stencil, axis=2)
        
        duIdx  = gradient(uI, x, acc=acc, edge_stencil=edge_stencil, axis=0)
        duIdy  = gradient(uI, y, acc=acc, edge_stencil=edge_stencil, axis=1)
        duIdz  = gradient(uI, z, acc=acc, edge_stencil=edge_stencil, axis=2)
        dvIdx  = gradient(vI, x, acc=acc, edge_stencil=edge_stencil, axis=0)
        dvIdy  = gradient(vI, y, acc=acc, edge_stencil=edge_stencil, axis=1)
        dvIdz  = gradient(vI, z, acc=acc, edge_stencil=edge_stencil, axis=2)
        dwIdx  = gradient(wI, x, acc=acc, edge_stencil=edge_stencil, axis=0)
        dwIdy  = gradient(wI, y, acc=acc, edge_stencil=edge_stencil, axis=1)
        dwIdz  = gradient(wI, z, acc=acc, edge_stencil=edge_stencil, axis=2)
        
        duIIdx = gradient(uII, x, acc=acc, edge_stencil=edge_stencil, axis=0)
        duIIdy = gradient(uII, y, acc=acc, edge_stencil=edge_stencil, axis=1)
        duIIdz = gradient(uII, z, acc=acc, edge_stencil=edge_stencil, axis=2)
        dvIIdx = gradient(vII, x, acc=acc, edge_stencil=edge_stencil, axis=0)
        dvIIdy = gradient(vII, y, acc=acc, edge_stencil=edge_stencil, axis=1)
        dvIIdz = gradient(vII, z, acc=acc, edge_stencil=edge_stencil, axis=2)
        dwIIdx = gradient(wII, x, acc=acc, edge_stencil=edge_stencil, axis=0)
        dwIIdy = gradient(wII, y, acc=acc, edge_stencil=edge_stencil, axis=1)
        dwIIdz = gradient(wII, z, acc=acc, edge_stencil=edge_stencil, axis=2)
        
        t_delta = timeit.default_timer() - t_start ## rank 0 only
        
        if verbose:
            tqdm.write(even_print('get gradients', format_time_string(t_delta), s=True))
        
        self.comm.Barrier()
        mem_free_gb  = psutil.virtual_memory().free/1024**3
        if verbose:
            tqdm.write(even_print('mem free', f'{mem_free_gb:0.1f} [GB]', s=True))
        
        # === stack velocities into vectors and mean-removed strains into tensors
        
        t_start = timeit.default_timer()
        
        uI_i  = np.stack(( uI  , vI  , wI  ), axis=-1)
        uII_i = np.stack(( uII , vII , wII ), axis=-1)
        
        duIdx_ij = np.stack((np.stack((duIdx, duIdy, duIdz), axis=4),
                             np.stack((dvIdx, dvIdy, dvIdz), axis=4),
                             np.stack((dwIdx, dwIdy, dwIdz), axis=4)), axis=5)
        
        duIIdx_ij = np.stack((np.stack((duIIdx, duIIdy, duIIdz), axis=4),
                              np.stack((dvIIdx, dvIIdy, dvIIdz), axis=4),
                              np.stack((dwIIdx, dwIIdy, dwIIdz), axis=4)), axis=5)
        
        t_delta = timeit.default_timer() - t_start
        if verbose:
            tqdm.write(even_print('tensor stacking',format_time_string(t_delta), s=True))
        
        self.comm.Barrier()
        mem_free_gb = psutil.virtual_memory().free/1024**3
        if verbose:
            tqdm.write(even_print('mem free', f'{mem_free_gb:0.1f} [GB]', s=True))
        
        # === production : P
        if True:
            
            if verbose: tqdm.write(72*'-')
            t_start = timeit.default_timer()
            
            r_uII_uII = rho*uII*uII
            r_uII_vII = rho*uII*vII
            r_uII_wII = rho*uII*wII
            
            r_vII_uII = rho*vII*uII
            r_vII_vII = rho*vII*vII
            r_vII_wII = rho*vII*wII
            
            r_wII_uII = rho*wII*uII
            r_wII_vII = rho*wII*vII
            r_wII_wII = rho*wII*wII
            
            ## unsteady_production_ = - ( r_uII_uII * dudx_fv + r_uII_vII * dudy_fv + r_uII_wII * dudz_fv \
            ##                          + r_uII_vII * dvdx_fv + r_vII_vII * dvdy_fv + r_vII_wII * dvdz_fv \
            ##                          + r_uII_wII * dwdx_fv + r_vII_wII * dwdy_fv + r_wII_wII * dwdz_fv )
            
            r_uIIuII_ij = np.stack((np.stack((r_uII_uII, r_uII_vII, r_uII_wII), axis=4),
                                    np.stack((r_vII_uII, r_vII_vII, r_vII_wII), axis=4),
                                    np.stack((r_wII_uII, r_wII_vII, r_wII_wII), axis=4)), axis=5)
            
            dudx_fv_ij = np.stack((np.stack((dudx_fv, dudy_fv, dudz_fv), axis=4),
                                   np.stack((dvdx_fv, dvdy_fv, dvdz_fv), axis=4),
                                   np.stack((dwdx_fv, dwdy_fv, dwdz_fv), axis=4)), axis=5)
            
            unsteady_production = -1*np.einsum('xyztij,xyztij->xyzt', r_uIIuII_ij, dudx_fv_ij)
            
            ## np.testing.assert_allclose(unsteady_production, unsteady_production_, atol=20000)
            ## print('check passed : np.einsum()')
            
            t_delta = timeit.default_timer() - t_start
            if verbose:
                tqdm.write(even_print('calc production', format_time_string(t_delta), s=True))
            
            self.comm.Barrier()
            
            if save_unsteady: ## write 4D unsteady production
                
                ## technically this is an estimate
                data_gb = self.n_ranks * np.prod(unsteady_production.shape) * unsteady_production.dtype.itemsize / 1024**3
                
                #with rgd(fn_h5_out_unsteady, 'a', driver='mpio', comm=self.comm) as f1:
                with rgd_meta(fn_h5_out_unsteady, 'a', driver='mpio', comm=self.comm) as f1:
                    dset = f1['data/production']
                    self.comm.Barrier()
                    t_start = timeit.default_timer()
                    with dset.collective:
                        dset[ct1:ct2,:,:,:] = unsteady_production.T
                    self.comm.Barrier()
                    t_delta = timeit.default_timer() - t_start
                    if verbose:
                        tqdm.write(even_print('write: production', '%0.2f [GB]  %0.2f [s]  %0.3f [GB/s]'%(data_gb,t_delta,(data_gb/t_delta)), s=True))
            
            ## combine sums across ranks for this [t] chunk
            unsteady_production_sum_i   = np.sum(unsteady_production, axis=3, keepdims=True, dtype=np.float64)
            unsteady_production_sum_buf = np.zeros((nx,ny,nz,1), dtype=np.float64, order='C')
            self.comm.Reduce(
                        [unsteady_production_sum_i, MPI.DOUBLE],
                        [unsteady_production_sum_buf, MPI.DOUBLE],
                        op=MPI.SUM,
                        root=0,
                        )
            
            ## add aggregated sum (across ranks) to the total accumulator
            unsteady_production_sum += unsteady_production_sum_buf
            
            # === release mem
            r_uII_uII           = None; del r_uII_uII
            r_uII_vII           = None; del r_uII_vII
            r_uII_wII           = None; del r_uII_wII
            r_vII_uII           = None; del r_vII_uII
            r_vII_vII           = None; del r_vII_vII
            r_vII_wII           = None; del r_vII_wII
            r_wII_uII           = None; del r_wII_uII
            r_wII_vII           = None; del r_wII_vII
            r_wII_wII           = None; del r_wII_wII
            r_uIIuII_ij         = None; del r_uIIuII_ij
            dudx_fv_ij          = None; del dudx_fv_ij
            unsteady_production = None; del unsteady_production
            
            self.comm.Barrier()
            mem_free_gb = psutil.virtual_memory().free/1024**3
            if verbose:
                tqdm.write(even_print('mem free', f'{mem_free_gb:0.1f} [GB]', s=True))
        
        # === dissipation : ε
        if True:
            
            if verbose: tqdm.write(72*'-')
            t_start = timeit.default_timer()
            
            duIIdx_ij_duIdx_ij = np.einsum('xyztij,xyztij->xyzt', duIIdx_ij, duIdx_ij)
            duIIdx_ij_duIdx_ji = np.einsum('xyztij,xyztji->xyzt', duIIdx_ij, duIdx_ij)
            
            ## # === from pp_turbulent_budget.F90
            ## unsteady_dissipation_ = mu * ( (duIdx + duIdx) * duIIdx  +  (duIdy + dvIdx) * duIIdy  +  (duIdz + dwIdx) * duIIdz \
            ##                              + (dvIdx + duIdy) * dvIIdx  +  (dvIdy + dvIdy) * dvIIdy  +  (dvIdz + dwIdy) * dvIIdz \
            ##                              + (dwIdx + duIdz) * dwIIdx  +  (dwIdy + dvIdz) * dwIIdy  +  (dwIdz + dwIdz) * dwIIdz )
            
            unsteady_dissipation = mu*(duIIdx_ij_duIdx_ij + duIIdx_ij_duIdx_ji)
            
            ## np.testing.assert_allclose(unsteady_dissipation, unsteady_dissipation_, rtol=1e-4)
            ## print('check passed : np.einsum() : dissipation')
            
            t_delta = timeit.default_timer() - t_start
            if verbose:
                tqdm.write(even_print('calc dissipation', format_time_string(t_delta),s=True))
            
            self.comm.Barrier()
            
            if save_unsteady: ## write 4D unsteady dissipation
                
                ## technically this is an estimate
                data_gb = self.n_ranks * np.prod(unsteady_dissipation.shape) * unsteady_dissipation.dtype.itemsize / 1024**3
                
                #with rgd(fn_h5_out_unsteady, 'a', driver='mpio', comm=self.comm) as f1:
                with rgd_meta(fn_h5_out_unsteady, 'a', driver='mpio', comm=self.comm) as f1:
                    dset = f1['data/dissipation']
                    self.comm.Barrier()
                    t_start = timeit.default_timer()
                    with dset.collective:
                        dset[ct1:ct2,:,:,:] = unsteady_dissipation.T
                    self.comm.Barrier()
                    t_delta = timeit.default_timer() - t_start
                    if verbose:
                        tqdm.write(even_print('write: dissipation', '%0.2f [GB]  %0.2f [s]  %0.3f [GB/s]'%(data_gb,t_delta,(data_gb/t_delta)), s=True))
            
            ## combine sums across ranks for this [t] chunk
            unsteady_dissipation_sum_i   = np.sum(unsteady_dissipation, axis=3, keepdims=True, dtype=np.float64)
            unsteady_dissipation_sum_buf = np.zeros((nx,ny,nz,1), dtype=np.float64, order='C')
            self.comm.Reduce(
                        [unsteady_dissipation_sum_i, MPI.DOUBLE],
                        [unsteady_dissipation_sum_buf, MPI.DOUBLE],
                        op=MPI.SUM,
                        root=0,
                        )
            
            ## add aggregated sum (across ranks) to the total accumulator
            unsteady_dissipation_sum += unsteady_dissipation_sum_buf
            
            ## release mem
            duIIdx_ij_duIdx_ij   = None; del duIIdx_ij_duIdx_ij
            duIIdx_ij_duIdx_ji   = None; del duIIdx_ij_duIdx_ji
            unsteady_dissipation = None; del unsteady_dissipation
            
            self.comm.Barrier()
            mem_free_gb = psutil.virtual_memory().free/1024**3
            if verbose:
                tqdm.write(even_print('mem free', f'{mem_free_gb:0.1f} [GB]', s=True))
        
        # === transport : T
        if True:
            
            if verbose: tqdm.write(72*'-')
            t_start = timeit.default_timer()
            
            ## triple correlation
            tc = np.einsum('xyzt,xyzti,xyzti,xyztj->xyztj', rho, uII_i, uII_i, uII_i)
            
            #tc_ddx = np.gradient(tc, x, axis=0, edge_order=2)
            #tc_ddy = np.gradient(tc, y, axis=1, edge_order=2)
            #tc_ddz = np.gradient(tc, z, axis=2, edge_order=2)
            
            tc_ddx = gradient(tc, x, axis=0, acc=acc, edge_stencil=edge_stencil)
            tc_ddy = gradient(tc, y, axis=1, acc=acc, edge_stencil=edge_stencil)
            tc_ddz = gradient(tc, z, axis=2, acc=acc, edge_stencil=edge_stencil)
            
            unsteady_transport = -0.5*(tc_ddx[:,:,:,:,0] + tc_ddy[:,:,:,:,1] + tc_ddz[:,:,:,:,2])
            
            t_delta = timeit.default_timer() - t_start
            if verbose:
                tqdm.write(even_print('calc transport', format_time_string(t_delta),s=True))
            
            self.comm.Barrier()
            
            if save_unsteady: ## write 4D unsteady transport
                
                ## technically this is an estimate
                data_gb = self.n_ranks * np.prod(unsteady_transport.shape) * unsteady_transport.dtype.itemsize / 1024**3
                
                #with rgd(fn_h5_out_unsteady, 'a', driver='mpio', comm=self.comm) as f1:
                with rgd_meta(fn_h5_out_unsteady, 'a', driver='mpio', comm=self.comm) as f1:
                    dset = f1['data/transport']
                    self.comm.Barrier()
                    t_start = timeit.default_timer()
                    with dset.collective:
                        dset[ct1:ct2,:,:,:] = unsteady_transport.T
                    self.comm.Barrier()
                    t_delta = timeit.default_timer() - t_start
                    if verbose:
                        tqdm.write(even_print('write: transport', '%0.2f [GB]  %0.2f [s]  %0.3f [GB/s]'%(data_gb,t_delta,(data_gb/t_delta)), s=True))
            
            ## combine sums across ranks for this [t] chunk
            unsteady_transport_sum_i   = np.sum(unsteady_transport, axis=3, keepdims=True, dtype=np.float64)
            unsteady_transport_sum_buf = np.zeros((nx,ny,nz,1), dtype=np.float64, order='C')
            self.comm.Reduce(
                        [unsteady_transport_sum_i, MPI.DOUBLE],
                        [unsteady_transport_sum_buf, MPI.DOUBLE],
                        op=MPI.SUM,
                        root=0,
                        )
            
            ## add aggregated sum (across ranks) to the total accumulator
            unsteady_transport_sum += unsteady_transport_sum_buf
            
            ## release mem
            tc     = None; del tc
            tc_ddx = None; del tc_ddx
            tc_ddy = None; del tc_ddy
            tc_ddz = None; del tc_ddz
            unsteady_transport = None; del unsteady_transport
            
            self.comm.Barrier()
            mem_free_gb = psutil.virtual_memory().free/1024**3
            if verbose:
                tqdm.write(even_print('mem free', f'{mem_free_gb:0.1f} [GB]', s=True))
        
        # === viscous diffusion : D
        if True:
            
            if verbose: tqdm.write(72*'-')
            t_start = timeit.default_timer()
            
            omega_ij = duIdx_ij + np.transpose(duIdx_ij, axes=(0,1,2,3,5,4))
            
            if False:
                
                omega_ij_2 = np.stack((np.stack(((duIdx+duIdx), (dvIdx+duIdy), (dwIdx+duIdz)), axis=4),
                                       np.stack(((duIdy+dvIdx), (dvIdy+dvIdy), (dwIdy+dvIdz)), axis=4),
                                       np.stack(((duIdz+dwIdx), (dvIdz+dwIdy), (dwIdz+dwIdz)), axis=4)), axis=5)
                
                np.testing.assert_allclose(omega_ij, omega_ij_2, rtol=1e-8)
                
                if verbose:
                    print('check passed : omega_ij')
            
            A = np.einsum('xyzt,xyzti,xyztij->xyztj', mu, uI_i, omega_ij)
            
            A_ddx = gradient(A[:,:,:,:,0], x, axis=0, acc=acc, edge_stencil=edge_stencil)
            A_ddy = gradient(A[:,:,:,:,1], y, axis=1, acc=acc, edge_stencil=edge_stencil)
            A_ddz = gradient(A[:,:,:,:,2], z, axis=2, acc=acc, edge_stencil=edge_stencil)
            
            unsteady_diffusion = A_ddx + A_ddy + A_ddz
            
            t_delta = timeit.default_timer() - t_start
            if verbose:
                tqdm.write(even_print('calc diffusion', format_time_string(t_delta),s=True))
            
            self.comm.Barrier()
            
            if save_unsteady: ## write 4D unsteady diffusion
                
                ## technically this is an estimate
                data_gb = self.n_ranks * np.prod(unsteady_diffusion.shape) * unsteady_diffusion.dtype.itemsize / 1024**3
                
                #with rgd(fn_h5_out_unsteady, 'a', driver='mpio', comm=self.comm) as f1:
                with rgd_meta(fn_h5_out_unsteady, 'a', driver='mpio', comm=self.comm) as f1:
                    dset = f1['data/diffusion']
                    self.comm.Barrier()
                    t_start = timeit.default_timer()
                    with dset.collective:
                        dset[ct1:ct2,:,:,:] = unsteady_diffusion.T
                    self.comm.Barrier()
                    t_delta = timeit.default_timer() - t_start
                    if verbose:
                        tqdm.write(even_print('write: diffusion', '%0.2f [GB]  %0.2f [s]  %0.3f [GB/s]'%(data_gb,t_delta,(data_gb/t_delta)), s=True))
            
            ## combine sums across ranks for this [t] chunk
            unsteady_diffusion_sum_i   = np.sum(unsteady_diffusion, axis=3, keepdims=True, dtype=np.float64)
            unsteady_diffusion_sum_buf = np.zeros((nx,ny,nz,1), dtype=np.float64, order='C')
            self.comm.Reduce(
                        [unsteady_diffusion_sum_i, MPI.DOUBLE],
                        [unsteady_diffusion_sum_buf, MPI.DOUBLE],
                        op=MPI.SUM,
                        root=0,
                        )
            
            ## add aggregated sum (across ranks) to the total accumulator
            unsteady_diffusion_sum += unsteady_diffusion_sum_buf
            
            ## release mem
            omega_ij = None; del omega_ij
            A        = None; del A
            A_ddx    = None; del A_ddx
            A_ddy    = None; del A_ddy
            A_ddz    = None; del A_ddz
            unsteady_diffusion = None; del unsteady_diffusion
            
            self.comm.Barrier()
            mem_free_gb = psutil.virtual_memory().free/1024**3
            if verbose:
                tqdm.write(even_print('mem free', f'{mem_free_gb:0.1f} [GB]', s=True))
        
        # === pressure diffusion
        if True:
            
            if verbose: tqdm.write(72*'-')
            t_start = timeit.default_timer()
            
            A = np.einsum('xyzti,xyzt->xyzti', uII_i, pI)
            
            #A_ddx = np.gradient(A[:,:,:,:,0], x, axis=0, edge_order=2)
            #A_ddy = np.gradient(A[:,:,:,:,1], y, axis=1, edge_order=2)
            #A_ddz = np.gradient(A[:,:,:,:,2], z, axis=2, edge_order=2)
            
            A_ddx = gradient(A[:,:,:,:,0], x, axis=0, acc=acc, edge_stencil=edge_stencil)
            A_ddy = gradient(A[:,:,:,:,1], y, axis=1, acc=acc, edge_stencil=edge_stencil)
            A_ddz = gradient(A[:,:,:,:,2], z, axis=2, acc=acc, edge_stencil=edge_stencil)
            
            unsteady_p_diffusion = A_ddx + A_ddy + A_ddz
            
            t_delta = timeit.default_timer() - t_start
            if verbose:
                tqdm.write(even_print('calc p_diffusion', format_time_string(t_delta),s=True))
            
            self.comm.Barrier()
            
            ## combine sums across ranks for this [t] chunk
            unsteady_p_diffusion_sum_i   = np.sum(unsteady_p_diffusion, axis=3, keepdims=True, dtype=np.float64)
            unsteady_p_diffusion_sum_buf = np.zeros((nx,ny,nz,1), dtype=np.float64, order='C')
            self.comm.Reduce(
                            [unsteady_p_diffusion_sum_i, MPI.DOUBLE],
                            [unsteady_p_diffusion_sum_buf, MPI.DOUBLE],
                            op=MPI.SUM,
                            root=0,
                            )
            
            ## add aggregated sum (across ranks) to the total accumulator
            unsteady_p_diffusion_sum += unsteady_p_diffusion_sum_buf
            
            # === release mem
            A        = None; del A
            A_ddx    = None; del A_ddx
            A_ddy    = None; del A_ddy
            A_ddz    = None; del A_ddz
            unsteady_p_diffusion = None; del unsteady_p_diffusion
            
            self.comm.Barrier()
            mem_free_gb = psutil.virtual_memory().free/1024**3
            if verbose:
                tqdm.write(even_print('mem free', f'{mem_free_gb:0.1f} [GB]', s=True))
        
        # === pressure dilatation
        if True:
            
            if verbose: tqdm.write(72*'-')
            t_start = timeit.default_timer()
            
            # A = np.einsum('xyzt,xyzti->xyzti', pI, uII_i)
            # A_ddx = np.gradient(A[:,:,:,:,0], x, axis=0, edge_order=2)
            # A_ddy = np.gradient(A[:,:,:,:,1], y, axis=1, edge_order=2)
            # A_ddz = np.gradient(A[:,:,:,:,2], z, axis=2, edge_order=2)
            # unsteady_p_dilatation = A_ddx + A_ddy + A_ddz
            
            unsteady_p_dilatation = pI * ( duIIdx + dvIIdy + dwIIdz )
            
            t_delta = timeit.default_timer() - t_start
            if verbose:
                tqdm.write(even_print('calc p_dilatation', format_time_string(t_delta),s=True))
            
            self.comm.Barrier()
            
            ## combine sums across ranks for this [t] chunk
            unsteady_p_dilatation_sum_i   = np.sum(unsteady_p_dilatation, axis=3, keepdims=True, dtype=np.float64)
            unsteady_p_dilatation_sum_buf = np.zeros((nx,ny,nz,1), dtype=np.float64, order='C')
            self.comm.Reduce(
                            [unsteady_p_dilatation_sum_i, MPI.DOUBLE],
                            [unsteady_p_dilatation_sum_buf, MPI.DOUBLE],
                            op=MPI.SUM,
                            root=0,
                            )
            
            ## add aggregated sum (across ranks) to the total accumulator
            unsteady_p_dilatation_sum += unsteady_p_dilatation_sum_buf
            
            ## release mem
            unsteady_p_dilatation = None
            del unsteady_p_dilatation
            
            self.comm.Barrier()
            mem_free_gb = psutil.virtual_memory().free/1024**3
            if verbose:
                tqdm.write(even_print('mem free', f'{mem_free_gb:0.1f} [GB]', s=True))
        
        if verbose:
            progress_bar.update()
            tqdm.write(72*'-')
        
        #break ## debug
    
    if verbose: progress_bar.close()
    if verbose: print(72*'-')
    
    ## CLOSE the files that were opened
    hf_mean.close()
    
    # ==============================================================
    # multiply accumulators by (1/n) to get [t] avg
    # ==============================================================
    
    if (self.rank==0):
        production   = np.copy( ((1/nt) * unsteady_production_sum   ) )
        dissipation  = np.copy( ((1/nt) * unsteady_dissipation_sum  ) )
        transport    = np.copy( ((1/nt) * unsteady_transport_sum    ) )
        diffusion    = np.copy( ((1/nt) * unsteady_diffusion_sum    ) )
        p_diffusion  = np.copy( ((1/nt) * unsteady_p_diffusion_sum  ) )
        p_dilatation = np.copy( ((1/nt) * unsteady_p_dilatation_sum ) )
    self.comm.Barrier()
    
    # === write to HDF5
    
    if self.rank==0:
        #with rgd(fn_h5_out, 'a') as f1:
        with rgd_meta(fn_h5_out, 'a') as f1:
            f1['data/production'][:,:,:,:]   = production.T
            f1['data/dissipation'][:,:,:,:]  = dissipation.T
            f1['data/transport'][:,:,:,:]    = transport.T
            f1['data/diffusion'][:,:,:,:]    = diffusion.T
            f1['data/p_diffusion'][:,:,:,:]  = p_diffusion.T
            f1['data/p_dilatation'][:,:,:,:] = p_dilatation.T
    self.comm.Barrier()
    
    ## report file contents
    if (self.rank==0):
        with h5py.File(fn_h5_out,'r') as hfr:
            h5_print_contents(hfr)
    self.comm.Barrier()
    
    if verbose: print(72*'-')
    if verbose: print('total time : rgd.calc_turb_budget() : %s'%format_time_string((timeit.default_timer() - t_start_func)))
    if verbose: print(72*'-')
    
    ## make .xdmf
    if self.rank==0:
        #with rgd(fn_h5_out, 'r') as f1:
        with rgd_meta(fn_h5_out, 'r') as f1:
            f1.make_xdmf()
    self.comm.Barrier()
    
    ## make .xdmf
    if save_unsteady:
        if self.rank==0:
            #with rgd(fn_h5_out_unsteady, 'r') as f1:
            with rgd_meta(fn_h5_out_unsteady, 'r') as f1:
                f1.make_xdmf()
        self.comm.Barrier()
    
    return
