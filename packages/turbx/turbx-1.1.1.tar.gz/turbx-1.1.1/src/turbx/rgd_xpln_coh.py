import os
import re
import sys
import timeit
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path, PurePosixPath

import h5py
import numpy as np
import psutil
from mpi4py import MPI
from scipy.signal import csd
from tqdm import tqdm

from .gradient import gradient
from .h5 import h5_print_contents
from .signal import ccor
from .utils import even_print, format_time_string

# ======================================================================

def _calc_wall_coh_xpln(self, **kwargs):
    '''
    Calculate coherence & complex cross-spectrum between turbulent
      field and wall (uτ & τuy) in [t] at every [y]
    ----------------------------------------------------------------
    - Designed for analyzing unsteady, thin planes in [x]
    - Multithreaded with ThreadPoolExecutor()
        - scipy.signal.csd() automatically tries to run multithreaded
        - set OMP_NUM_THREADS=1 and pass 'n_threads' to as kwarg manually
    '''
    
    if (self.rank==0):
        verbose = True
    else:
        verbose = False
    
    if verbose: print('\n'+'rgd.calc_wall_coh_xpln()'+'\n'+72*'-')
    t_start_func = timeit.default_timer()
    
    ## assert that the opened RGD has fsubtype 'unsteady' (i.e. is NOT a prime file)
    if (self.fsubtype!='unsteady'):
        raise ValueError
    if not self.usingmpi:
        raise NotImplementedError('function is not implemented for non-MPI usage')
    
    h5py_is_mpi_build = h5py.h5.get_config().mpi
    if not h5py_is_mpi_build:
        if verbose: print('h5py was not compiled for parallel usage! exiting.')
        sys.exit(1)
    
    rx = kwargs.get('rx',1)
    ry = kwargs.get('ry',1)
    rz = kwargs.get('rz',1)
    rt = kwargs.get('rt',1)
    
    acc          = kwargs.get('acc',6)
    edge_stencil = kwargs.get('edge_stencil','full')
    
    sy = kwargs.get('sy',1) ## N [y] layers to read at a time
    if not isinstance(sy,int) or (sy<1):
        raise TypeError('sy should be a positive non-zero int')
    
    n_threads = kwargs.get('n_threads',1)
    
    ## Debug Rank:Proc Affinity
    #pp = psutil.Process()
    #print(f"[Rank {self.rank}] sees CPUs: {pp.cpu_affinity()}  |  n_threads={n_threads}  |  OMP_NUM_THREADS={os.environ.get('OMP_NUM_THREADS')}")
    
    #try:
    #    n_threads = int(os.environ.get('OMP_NUM_THREADS'))
    #except TypeError: ## not set
    #    n_threads = os.cpu_count()
    
    fn_h5_out       = kwargs.get('fn_h5_out',None)       ## Filename for output HDF5 (.h5) file
    overlap_fac_nom = kwargs.get('overlap_fac_nom',0.50) ## Nominal windows overlap factor
    n_win           = kwargs.get('n_win',8)              ## N segment windows for [t] PSD calc
    
    #overlap_fac_nom = kwargs.get('overlap_fac_nom',0.5)
    #n_win           = kwargs.get('n_win',8)
    
    ## Only distribute data across [y]
    if (rx!=1):
        raise AssertionError('rx!=1')
    if (rz!=1):
        raise AssertionError('rz!=1')
    if (rt!=1):
        raise AssertionError('rt!=1')
    
    if not isinstance(ry,int) or (ry<1):
        raise ValueError('ry should be a positive non-zero int')
    
    ## Check the choice of ranks per dimension
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
    
    if (self.ny%ry!=0):
        raise ValueError('ny not divisible by ry')
    
    ## Distribute 4D data over ranks --> here only in [y]
    ryl_ = np.array_split(np.arange(self.ny,dtype=np.int64),min(ry,self.ny))
    ryl = [[b[0],b[-1]+1] for b in ryl_ ]
    ry1,ry2 = ryl[self.rank]
    nyr = ry2 - ry1
    
    ## Check all [y] ranges have same size
    for ryl_ in ryl:
        if not (ryl_[1]-ryl_[0]==nyr):
            raise ValueError('[y] chunks are not even in size')
    
    if (nyr%sy!=0):
        raise ValueError('nyr not divisible by sy')
    
    ## Output filename : HDF5 (.h5)
    if (fn_h5_out is None): ## automatically determine name
        fname_path = os.path.dirname(self.fname)
        fname_base = os.path.basename(self.fname)
        fname_root, fname_ext = os.path.splitext(fname_base)
        fname_root = re.findall(r'io\S+_mpi_[0-9]+', fname_root)[0]
        fn_h5_out_base = fname_root+'_coh.h5'
        fn_h5_out = str(PurePosixPath(fname_path, fn_h5_out_base))
    if (Path(fn_h5_out).suffix != '.h5'):
        raise ValueError(f"fn_h5_out='{str(fn_h5_out)}' must end in .h5")
    if os.path.isfile(fn_h5_out):
        #if (os.path.getsize(fn_h5_out) > 8*1024**3):
        #    raise ValueError(f"fn_h5_out='{str(fn_h5_out)}' exists and is >8 [GB]. exiting for your own safety.")
        if (fn_h5_out == self.fname):
            raise ValueError(f"fn_h5_out='{str(fn_h5_out)}' cannot be same as input filename.")
    
    if verbose: even_print( 'fn_h5'      , self.fname )
    if verbose: even_print( 'fn_h5_out'  , fn_h5_out  )
    if verbose: print(72*'-')
    self.comm.Barrier()
    
    ## The data dictionary to be written to .h5 later
    data = {}
    
    ## Infile
    fsize = os.path.getsize(self.fname)/1024**3
    if verbose: even_print(os.path.basename(self.fname),'%0.1f [GB]'%fsize)
    if verbose: even_print('nx',f'{self.nx:d}')
    if verbose: even_print('ny',f'{self.ny:d}')
    if verbose: even_print('nz',f'{self.nz:d}')
    if verbose: even_print('nt',f'{self.nt:d}')
    if verbose: even_print('ngp',f'{self.ngp/1e6:0.1f} [M]')
    #if verbose: even_print('cy',f'{cy:d}')
    if verbose: even_print('sy',f'{sy:d}')
    if verbose: even_print('n_ranks',f'{self.n_ranks:d}')
    if verbose: even_print('n_threads',f'{n_threads:d}')
    if verbose: print(72*'-')
    
    ## 0D freestream scalars
    lchar   = self.lchar   ; data['lchar']   = lchar
    U_inf   = self.U_inf   ; data['U_inf']   = U_inf
    rho_inf = self.rho_inf ; data['rho_inf'] = rho_inf
    T_inf   = self.T_inf   ; data['T_inf']   = T_inf
    
    #data['M_inf'] = self.M_inf
    data['Ma'] = self.Ma
    data['Pr'] = self.Pr
    
    ## Read in 1D coordinate arrays & re-dimensionalize
    x = np.copy( self['dims/x'][()] * self.lchar )
    y = np.copy( self['dims/y'][()] * self.lchar )
    z = np.copy( self['dims/z'][()] * self.lchar )
    t = np.copy( self['dims/t'][()] * self.tchar )
    
    nx = self.nx ; data['nx'] = nx
    ny = self.ny ; data['ny'] = ny
    nz = self.nz ; data['nz'] = nz
    nt = self.nt ; data['nt'] = nt
    
    ## Assert constant Δz
    dz0 = np.diff(z)[0]
    if not np.all(np.isclose(np.diff(z), dz0, rtol=1e-6)):
        raise NotImplementedError('Δz not constant')
    dz = np.diff(z)[0]
    
    ## dimensional [s]
    dt = self.dt * self.tchar
    np.testing.assert_allclose(dt, t[1]-t[0], rtol=1e-12, atol=1e-12)
    
    t_meas = self.duration * self.tchar
    np.testing.assert_allclose(t_meas, t.max()-t.min(), rtol=1e-12, atol=1e-12)
    
    zrange = z.max() - z.min()
    
    data['x'] = x
    data['y'] = y
    data['z'] = z
    
    data['t']      = t
    data['t_meas'] = t_meas
    data['dt']     = dt
    data['dz']     = dz
    data['zrange'] = zrange
    
    if verbose: even_print( 'Δt/tchar'       , f'{dt/self.tchar:0.8f}' )
    if verbose: even_print( 'Δt'             , f'{dt:0.3e} [s]'        )
    if verbose: even_print( 'duration/tchar' , f'{self.duration:0.1f}' )
    if verbose: even_print( 'duration'       , f'{self.duration*self.tchar:0.3e} [s]' )
    if verbose: print(72*'-')
    
    ## report
    if verbose:
        even_print('Δt'     , f'{dt    :0.5e} [s]' )
        even_print('t_meas' , f'{t_meas:0.5e} [s]' )
        even_print('Δz'     , f'{dz0   :0.5e} [m]' )
        even_print('zrange' , f'{zrange:0.5e} [m]' )
        print(72*'-')
    
    ## Establish [t] windowing & get frequency
    nperseg     = nt // n_win
    noverlap    = int(round(nperseg*overlap_fac_nom))
    overlap_fac = noverlap / nperseg
    fs          = 1./dt ## dimensional [1/s]
    
    ## Get [freq] vector
    freq_w0,_ = csd(
            np.zeros((nt,),dtype=np.float64),
            np.zeros((nt,),dtype=np.float64),
            fs=fs,
            nperseg=nperseg,
            noverlap=noverlap,
            window='hann',
            detrend=False,
            scaling='density',
            return_onesided=True,
            )
    fp   = np.where(freq_w0>0) ## dont include 0 freq
    freq = np.copy(freq_w0[fp])
    nf   = freq.shape[0]
    df   = np.diff(freq)[0]
    
    data['nperseg']  = nperseg
    data['noverlap'] = noverlap
    data['freq']     = freq
    data['df']       = df
    data['nf']       = nf
    
    if verbose:
        even_print('overlap_fac (nominal)' , f'{overlap_fac_nom:0.5f}'  )
        even_print('n_win'                 , f'{n_win:d}'               )
        even_print('nperseg'               , f'{nperseg:d}'             )
        even_print('noverlap'              , f'{noverlap:d}'            )
        even_print('overlap_fac'           , f'{overlap_fac:0.5f}'      )
        print(72*'-')
    
    if verbose:
        even_print('freq min',f'{freq.min():0.1f} [Hz]')
        even_print('freq max',f'{freq.max():0.1f} [Hz]')
        even_print('df',f'{df:0.1f} [Hz]')
        even_print('nf',f'{nf:d}')
        print(72*'-')
    
    ## ## [z] Wavenumber (kz) vector -- scipy fftfreq version
    ## kz_full = sp.fft.fftfreq(n=nz, d=dz0) * ( 2 * np.pi )
    ## kzp     = np.where(kz_full>0) ## dont include k=0 or (-) k
    ## kz      = np.copy(kz_full[kzp])
    ## dkz     = kz[1] - kz[0]
    ## nkz     = kz.shape[0]
    
    ## [z] Wavenumber (kz) vector
    kz_ov_2pi,_ = csd(
                    np.zeros((nz,),dtype=np.float64),
                    np.zeros((nz,),dtype=np.float64),
                    fs=1/dz0,
                    nperseg=nz,
                    noverlap=0,
                    window='boxcar',
                    detrend=False,
                    scaling='density',
                    return_onesided=True,
                    )
    kz_full = kz_ov_2pi * (2 * np.pi)
    kzp     = np.where(kz_full>0) ## dont include k=0
    kz      = np.copy(kz_full[kzp])
    dkz = kz[1] - kz[0]
    nkz = kz.shape[0]
    
    data['kz']  = kz
    data['dkz'] = dkz
    data['nkz'] = nkz
    
    if verbose:
        even_print('kz min',f'{kz.min():0.1f} [1/m]')
        even_print('kz max',f'{kz.max():0.1f} [1/m]')
        even_print('dkz',f'{dkz:0.1f} [1/m]')
        even_print('nkz',f'{nkz:d}')
        print(72*'-')
    
    ## Wavelength λz = (2·π)/kz
    lz = np.copy( 2 * np.pi / kz )
    data['lz'] = lz
    
    # ===
    
    ## Get lags [t]
    lags_t,_  = ccor( np.ones(nt,dtype=np.float32) , np.ones(nt,dtype=np.float32), get_lags=True )
    n_lags_t_ = nt*2-1
    n_lags_t  = lags_t.shape[0]
    if (n_lags_t!=n_lags_t_):
        raise AssertionError('check lags [t]')
    
    data['lags_t']   = lags_t
    data['n_lags_t'] = n_lags_t
    
    if verbose:
        even_print('n lags (Δt)' , '%i'%(n_lags_t,))
    
    # ===
    
    ## cross-correlation pairs
    ## [ str:var1, str:var2, bool:do_density_weighting]
    ccor_combis = [
        
        [ 'utau'   , 'u' , True  ], ## [ uτ′  , ρ·u″ ]
        [ 'utau'   , 'v' , True  ], ## [ uτ′  , ρ·v″ ]
        [ 'utau'   , 'u' , False ], ## [ uτ′  , u′   ]
        [ 'utau'   , 'v' , False ], ## [ uτ′  , v′   ]
        [ 'utau'   , 'p' , False ], ## [ uτ′  , p′   ]
        [ 'utau'   , 'T' , False ], ## [ uτ′  , T′   ]
        
        [ 'tauuy'  , 'u' , True  ], ## [ τuy′ , ρ·u″ ]
        [ 'tauuy'  , 'v' , True  ], ## [ τuy′ , ρ·v″ ]
        [ 'tauuy'  , 'u' , False ], ## [ τuy′ , u′   ]
        [ 'tauuy'  , 'v' , False ], ## [ τuy′ , v′   ]
        [ 'tauuy'  , 'p' , False ], ## [ τuy′ , p′   ]
        [ 'tauuy'  , 'T' , False ], ## [ τuy′ , T′   ]
        
        ]
    
    ## Generate cross-correlation scalar names
    scalars = []
    for ccor_combi in ccor_combis:
        s1,s2,do_density_weighting = ccor_combi
        if do_density_weighting:
            scalars.append(f'{s1}I_r{s2}II')
        else:
            scalars.append(f'{s1}I_{s2}I')
    
    ## Generate avg scalar names
    scalars_Re_avg = []
    scalars_Fv_avg = []
    for ccor_combi in ccor_combis:
        s1,s2,do_density_weighting = ccor_combi
        if do_density_weighting and ('rho' not in scalars_Re_avg):
            scalars_Re_avg.append('rho')
        if do_density_weighting:
            #if (s1 not in scalars_Fv_avg):
            #    scalars_Fv_avg.append(s1)
            if (s2 not in scalars_Fv_avg):
                scalars_Fv_avg.append(s2)
        else:
            #if (s1 not in scalars_Re_avg):
            #    scalars_Re_avg.append(s1)
            if (s2 not in scalars_Re_avg):
                scalars_Re_avg.append(s2)
    
    ## numpy formatted arrays: buffers for PSD & other data (rank-local)
    Rt         = np.zeros(shape=(nyr, n_lags_t ) , dtype={'names':scalars        , 'formats':[np.dtype(np.float64)    for s in scalars]})
    Coh_t      = np.zeros(shape=(nyr, nf       ) , dtype={'names':scalars        , 'formats':[np.dtype(np.complex128) for s in scalars]})
    Coh_z      = np.zeros(shape=(nyr, nkz      ) , dtype={'names':scalars        , 'formats':[np.dtype(np.complex128) for s in scalars]})
    Pt         = np.zeros(shape=(nyr, nf       ) , dtype={'names':scalars        , 'formats':[np.dtype(np.complex128) for s in scalars]})
    Pz         = np.zeros(shape=(nyr, nkz      ) , dtype={'names':scalars        , 'formats':[np.dtype(np.complex128) for s in scalars]})
    covariance = np.zeros(shape=(nyr,          ) , dtype={'names':scalars        , 'formats':[np.dtype(np.float64)    for s in scalars]})
    avg_Re     = np.zeros(shape=(nyr,          ) , dtype={'names':scalars_Re_avg , 'formats':[np.dtype(np.float64)    for s in scalars_Re_avg]})
    avg_Fv     = np.zeros(shape=(nyr,          ) , dtype={'names':scalars_Fv_avg , 'formats':[np.dtype(np.float64)    for s in scalars_Fv_avg]})
    
    if verbose:
        even_print('n cross-correlation scalar combinations' , f'{len(ccor_combis):d}')
        print(72*'-')
    
    # ==============================================================
    # Calculate instantaneous uτ & τuy
    # ==============================================================
    
    if verbose:
        print('>>> calculating uτ & τuy')
    self.comm.Barrier()
    t_start = timeit.default_timer()
    
    if (self.rank==0):
        
        u        = np.zeros(shape=(nx,7,nz,nt), dtype=np.float64)
        T_wall   = np.zeros(shape=(nx,1,nz,nt), dtype=np.float64)
        rho_wall = np.zeros(shape=(nx,1,nz,nt), dtype=np.float64)
        
        dset = self['data/u']
        #with dset.collective:
        u[:,:,:,:] = dset[:,:,:7,:].T
        dset = self['data/T']
        #with dset.collective:
        T_wall[:,:,:,:] = dset[:,:,0,:].T[:,np.newaxis,:,:]
        dset = self['data/rho']
        #with dset.collective:
        rho_wall[:,:,:,:] = dset[:,:,0,:].T[:,np.newaxis,:,:]
        
        ## Re-dimensionalize
        u        *= self.U_inf
        T_wall   *= self.T_inf
        rho_wall *= self.rho_inf
        
        mu_wall          = np.zeros(shape=(nx,1,nz,nt), dtype=np.float64)
        mu_wall[:,:,:,:] = self.mu_Suth_ref * ( T_wall / self.T_Suth_ref )**(3/2) * ( ( self.T_Suth_ref + self.S_Suth ) / ( T_wall + self.S_Suth ) )
        
        ddy_u          = np.zeros(shape=(nx,7,nz,nt), dtype=np.float64)
        ddy_u[:,:,:,:] = gradient(u, y[:7], axis=1, acc=acc, edge_stencil=edge_stencil, d=1)
        
        ddy_u_wall          = np.zeros(shape=(nx,1,nz,nt), dtype=np.float64)
        ddy_u_wall[:,:,:,:] = ddy_u[:,0,:,:][:,np.newaxis,:,:]
        
        ddy_u = None ; del ddy_u
        u     = None ; del u
        
        ## INSTANTANEOUS τw
        tau_uy          = np.zeros(shape=(nx,1,nz,nt), dtype=np.float64)
        tau_uy[:,:,:,:] = mu_wall[:,:,:,:] * ddy_u_wall[:,:,:,:]
        
        ## INSTANTANEOUS uτ
        u_tau          = np.zeros(shape=(nx,1,nz,nt), dtype=np.float64)
        u_tau[:,:,:,:] = np.sign(tau_uy) * np.sqrt( np.abs(tau_uy) / rho_wall )
        
        mu_wall  = None ; del mu_wall
        T_wall   = None ; del T_wall
        rho_wall = None ; del rho_wall
        
        if ( u_tau.shape != (nx,1,nz,nt) ) or ( tau_uy.shape != (nx,1,nz,nt) ):
            print(f'rank {self.rank:d}: shape violation')
            self.comm.Abort(1)
        
        u_tau_avg  = np.mean(u_tau  , axis=3, dtype=np.float64, keepdims=True) ## (x,1,z,1)
        tau_uy_avg = np.mean(tau_uy , axis=3, dtype=np.float64, keepdims=True) ## (x,1,z,1)
        
        if ( u_tau_avg.shape != (nx,1,nz,1) ) or ( tau_uy_avg.shape != (nx,1,nz,1) ):
            print(f'rank {self.rank:d}: shape violation')
            self.comm.Abort(1)
        
        u_tau_avg  = None ; del u_tau_avg
        tau_uy_avg = None ; del tau_uy_avg
    
    # ==============================================================
    
    self.comm.Barrier()
    t_delta = timeit.default_timer() - t_start
    if verbose:
        even_print('calculate uτ & τuy',format_time_string(t_delta))
        print(72*'-')
    
    ## Initialize buffers on non-0 ranks
    if self.rank!=0:
        tau_uy = np.zeros(shape=(nx,1,nz,nt), dtype=np.float64)
        u_tau  = np.zeros(shape=(nx,1,nz,nt), dtype=np.float64)
    
    ## Broadcast from rank 0 to all ranks
    self.comm.Barrier()
    t_start = timeit.default_timer()
    
    self.comm.Bcast( tau_uy , root=0 )
    self.comm.Bcast( u_tau  , root=0 )
    
    self.comm.Barrier()
    t_delta = timeit.default_timer() - t_start
    
    if verbose:
        even_print('Bcast uτ & τuy',format_time_string(t_delta))
        print(72*'-')
    
    # ==============================================================
    # Check memory
    # ==============================================================
    
    hostname = MPI.Get_processor_name()
    mem_free_gb = psutil.virtual_memory().free / 1024**3
    G = self.comm.gather([ self.rank , hostname , mem_free_gb ], root=0)
    G = self.comm.bcast(G, root=0)
    
    host_mem = {}
    for rank, host, mem in G:
        if host not in host_mem or mem < host_mem[host]:
            host_mem[host] = mem
    total_free = sum(host_mem.values())
    
    if verbose:
        #print(72*'-')
        for key,value in host_mem.items():
            even_print(f'RAM free {key}', f'{int(np.floor(value)):d} [GB]')
        even_print('RAM free (local,min)', f'{int(np.floor(min(host_mem.values()))):d} [GB]')
        even_print('RAM free (global)', f'{int(np.floor(total_free)):d} [GB]')
    
    shape_read = (nx,sy,nz,nt) ## local
    if verbose: even_print('read shape (local)', f'[{nx:d},{sy:d},{nz:d},{nt:d}]')
    data_gb = np.dtype(np.float64).itemsize * np.prod(shape_read) / 1024**3
    if verbose: even_print('read size (global)', f'{int(np.ceil(data_gb*ry)):d} [GB]')
    
    if verbose: even_print('read size (global) ×6', f'{int(np.ceil(data_gb*ry*6)):d} [GB]')
    ram_usage_est = data_gb*ry*6/total_free
    if verbose: even_print('RAM usage estimate', f'{100*ram_usage_est:0.1f} [%]')
    
    self.comm.Barrier()
    if (ram_usage_est>0.80):
        print('RAM consumption might be too high. exiting.')
        self.comm.Abort(1)
    
    # ==============================================================
    # Main loop
    # ==============================================================
    
    if verbose:
        progress_bar = tqdm(
            #total=len(ccor_combis)*cy,
            total=len(ccor_combis)*(nyr//sy),
            ncols=100,
            desc='Coh',
            leave=True,
            file=sys.stdout,
            mininterval=0.1,
            smoothing=0.,
            #bar_format="\033[B{l_bar}{bar}| {n}/{total} [{percentage:.1f}%] {elapsed}/{remaining}\033[A\n\b",
            bar_format="{l_bar}{bar}| {n}/{total} [{percentage:.1f}%] {elapsed}/{remaining}",
            ascii="░█",
            colour='#FF6600',
            )
    
    for cci,cc in enumerate(ccor_combis): ## ccor pairs
        
        if verbose: tqdm.write(72*'-')
        
        scalar_L, scalar_R, do_density_weighting = cc
        
        if scalar_L == 'utau':
            scalar_L_str = 'uτ'
        elif scalar_L == 'tauuy':
            scalar_L_str = 'τuy'
        else:
            raise RuntimeError
        
        if do_density_weighting:
            msg = f'[{scalar_L_str}′,ρ·{scalar_R}″]'
        else:
            msg = f'[{scalar_L_str}′,{scalar_R}′]'
        if verbose:
            tqdm.write(even_print('computing',msg,s=True,))
        
        #dset_L   = self[f'data/{scalar_L}']
        dset_R   = self[f'data/{scalar_R}']
        dset_rho = self['data/rho']
        
        scalar = scalars[cci]
        
        ## Assert scalar name
        if do_density_weighting:
            if (f'{scalar_L}I_r{scalar_R}II' != scalar ):
                raise ValueError
        else:
            if (f'{scalar_L}I_{scalar_R}I' != scalar ):
                raise ValueError
        
        # ## [y] loop outer (chunks within rank)
        # for cyl_ in cyl:
        #     cy1, cy2 = cyl_
        #     nyc = cy2 - cy1
        
        for ci in range(nyr//sy): ## [y] loop
            
            cy1 = ry1 + ci*sy
            cy2 = cy1 + sy
            nyc = cy2 - cy1
            
            ## COPY data L (no read!)
            if scalar_L == 'utau':
                data_L = np.zeros(shape=(nx,1,nz,nt), dtype=np.float64)
                data_L[:,:,:,:] = u_tau[:,:,:,:]
            elif scalar_L == 'tauuy':
                data_L = np.zeros(shape=(nx,1,nz,nt), dtype=np.float64)
                data_L[:,:,:,:] = tau_uy[:,:,:,:]
            else:
                raise RuntimeError
            
            self.comm.Barrier()
            t_start = timeit.default_timer()
            
            ## Read data R
            scalar_str = scalar_R
            n_scalars_read = 1
            with dset_R.collective:
                data_R = np.copy( dset_R[:,:,cy1:cy2,:].T ).astype(np.float64)
            
            ## Read ρ
            if do_density_weighting:
                n_scalars_read += 1
                scalar_str += ',ρ'
                with dset_rho.collective:
                    rho = np.copy( dset_rho[:,:,cy1:cy2,:].T ).astype(np.float64)
            else:
                rho = None
            
            self.comm.Barrier()
            t_delta = timeit.default_timer() - t_start
            data_gb = n_scalars_read * ( self.nx * ry * (cy2-cy1) * self.nz * self.nt * dset_R.dtype.itemsize ) / 1024**3
            if verbose:
                tqdm.write(even_print(f'read: {scalar_str}', '%0.3f [GB]  %0.3f [s]  %0.3f [GB/s]'%(data_gb,t_delta,(data_gb/t_delta)), s=True))
            
            ## Assert shapes
            if ( data_L.shape != (nx,1,nz,nt) ):
                print(f'rank {self.rank:d}: shape violation')
                self.comm.Abort(1)
            if ( data_R.shape != (nx,nyc,nz,nt) ):
                print(f'rank {self.rank:d}: shape violation')
                self.comm.Abort(1)
            if (rho is not None) and ( rho.shape != (nx,nyc,nz,nt) ):
                print(f'rank {self.rank:d}: shape violation')
                self.comm.Abort(1)
            
            # === Redimensionalize
            
            if scalar_R in ['u','v','w',]:
                data_R *= U_inf
            elif scalar_R in ['p',]:
                data_R *= rho_inf*U_inf**2
            elif scalar_R in ['T',]:
                data_R *= T_inf
            else:
                raise ValueError
            
            if (rho is not None): ## i.e. if do_density_weighting
                rho *= rho_inf
            
            # === Compute mean-removed data
            
            ## avg(□) or avg(ρ·□)/avg(ρ) in [t]
            if do_density_weighting:
                rho_avg     = np.mean(        rho , axis=3, dtype=np.float64, keepdims=True) ## [x,y,z,1]
                data_R_avg  = np.mean( rho*data_R , axis=3, dtype=np.float64, keepdims=True) ## [x,y,z,1]
                data_R_avg /= rho_avg
            else:
                data_R_avg = np.mean( data_R , axis=3, dtype=np.float64, keepdims=True) ## [x,y,z,1]
            
            ### pointer to data L
            #if scalar_L == 'utau':
            #    data_L_avg = u_tau_avg
            #elif scalar_L == 'tauuy':
            #    data_L_avg = tau_uy_avg
            #else:
            #    raise RuntimeError
            
            data_L_avg = np.mean( data_L , axis=3, dtype=np.float64, keepdims=True) ## (x,y,z,1)
            
            ## Reynolds prime □′ or Favre prime □″
            data_L -= data_L_avg
            data_R -= data_R_avg
            
            ## Assert stationarity / definition averaging
            ## avg(□′)==0 or avg(ρ·□″)==0
            if do_density_weighting:
                b_ = np.mean(rho*data_R, axis=3, dtype=np.float64, keepdims=True)
            else:
                b_ = np.mean(data_R, axis=3, dtype=np.float64, keepdims=True)
            if not np.allclose( b_, np.zeros_like(b_), atol=1e-6 ):
                print(f'rank {self.rank:d}: avg(□′)!=0 or avg(ρ·□″)!=0')
                self.comm.Abort(1)
            
            ## LEFT variable (uτ′ or τuy′) ... never gets ρ-weighted / Favre mean-removed
            a_ = np.mean(data_L, axis=3, dtype=np.float64, keepdims=True)
            if not np.allclose( a_, np.zeros_like(a_), atol=1e-6 ):
                print(f'rank {self.rank:d}: avg(□′)!=0 or avg(ρ·□″)!=0')
                self.comm.Abort(1)
            
            a_ = None ; del a_
            b_ = None ; del b_
            
            ## Covariance (L here is never ρ-weighted)
            if do_density_weighting:
                covariance_ = np.mean( data_L * rho*data_R , axis=3 , dtype=np.float64, keepdims=True)
            else:
                covariance_ = np.mean( data_L * data_R , axis=3 , dtype=np.float64, keepdims=True)
            
            ## Write this chunk/scalar's covariance to covariance buffer
            ## avg over [x,z] : [x,y,z,1] --> [y]
            yiA = cy1 - ry1
            yiB = cy2 - ry1
            covariance[scalar][yiA:yiB] = np.squeeze( np.mean( covariance_ , axis=(0,2,3) , dtype=np.float64) )
            
            ## Write (rank-local) 1D [y] averages to buffers
            if do_density_weighting:
                avg_Fv[scalar_R][yiA:yiB] = np.squeeze( np.mean( data_R_avg , axis=(0,2,3) , dtype=np.float64) )
                avg_Re['rho'][yiA:yiB]    = np.squeeze( np.mean( rho_avg    , axis=(0,2,3) , dtype=np.float64) )
            else:
                avg_Re[scalar_R][yiA:yiB] = np.squeeze( np.mean( data_R_avg , axis=(0,2,3) , dtype=np.float64) )
            
            # ===============================================================================
            # At this point you have 4D [x,y,z,t] [_,□′] or [_,ρ·□″] data
            # ===============================================================================
            
            def __ccor_kernel_t(xi,zi,yii,do_density_weighting):
                if do_density_weighting:
                    uR = rho[xi,yii,zi,:] * data_R[xi,yii,zi,:]
                else:
                    uR = data_R[xi,yii,zi,:]
                uL = data_L[xi,0,zi,:]
                return xi,zi,ccor(uL,uR)
            
            def __coherence_kernel_t(xi,zi,yii,do_density_weighting):
                
                ## 1D [t] □′ or ρ·□″ vectors
                if do_density_weighting:
                    uR = rho[xi,yii,zi,:] * data_R[xi,yii,zi,:]
                else:
                    uR = data_R[xi,yii,zi,:]
                uL = data_L[xi,0,zi,:]
                
                _,Pxx = csd(
                        uL,uL,
                        fs=fs,
                        nperseg=nperseg,
                        noverlap=noverlap,
                        window='hann',
                        detrend=False,
                        scaling='density',
                        return_onesided=True,
                        )
                _,Pyy = csd(
                        uR,uR,
                        fs=fs,
                        nperseg=nperseg,
                        noverlap=noverlap,
                        window='hann',
                        detrend=False,
                        scaling='density',
                        return_onesided=True,
                        )
                _,Pxy = csd(
                        uL,uR,
                        fs=fs,
                        nperseg=nperseg,
                        noverlap=noverlap,
                        window='hann',
                        detrend=False,
                        scaling='density',
                        return_onesided=True,
                        )
                
                eps = np.finfo(float).eps
                Pxx = np.real(Pxx) ## imag part of auto- cross spectral density is =0 anyway
                Pyy = np.real(Pyy)
                Pxx = np.maximum(Pxx, eps)
                Pyy = np.maximum(Pyy, eps)
                Coh = (np.abs(Pxy)**2) / (Pxx * Pyy)
                return xi,zi,Pxy,Coh
            
            def __coherence_kernel_z(xi,ti,yii,do_density_weighting):
                
                ## 1D [z] □′ or ρ·□″ vectors
                if do_density_weighting:
                    uR = rho[xi,yii,:,ti] * data_R[xi,yii,:,ti]
                else:
                    uR = data_R[xi,yii,:,ti]
                uL = data_L[xi,0,:,ti]
                
                N = uL.shape[0]
                
                _,Pxx = csd(
                        uL,uL,
                        fs=fs,
                        nperseg=N,
                        noverlap=0,
                        window='boxcar',
                        detrend=False,
                        scaling='density',
                        return_onesided=True,
                        )
                _,Pyy = csd(
                        uR,uR,
                        fs=fs,
                        nperseg=N,
                        noverlap=0,
                        window='boxcar',
                        detrend=False,
                        scaling='density',
                        return_onesided=True,
                        )
                _,Pxy = csd(
                        uL,uR,
                        fs=fs,
                        nperseg=N,
                        noverlap=0,
                        window='boxcar',
                        detrend=False,
                        scaling='density',
                        return_onesided=True,
                        )
                
                eps = np.finfo(float).eps
                Pxx = np.real(Pxx) ## imag part of auto- cross spectral density is =0 anyway
                Pyy = np.real(Pyy)
                Pxx = np.maximum(Pxx, eps)
                Pyy = np.maximum(Pyy, eps)
                Coh = (np.abs(Pxy)**2) / (Pxx * Pyy)
                return xi,ti,Pxy,Coh
            
            self.comm.Barrier()
            t_start = timeit.default_timer()
            
            ## [y] loop inner (indices within chunk)
            for yi in range(cy1,cy2):
                
                yii  = yi - cy1 ## chunk local
                yiii = yi - ry1 ## rank local
                
                # ===========================================================================
                # Cross-Correlation [t] : loop over [x,z]
                # ===========================================================================
                
                ## Cross-correlation buffer for [y] loop inner
                R_xz = np.zeros((nx,nz,n_lags_t), dtype=np.float64) ## [x,z] range for ccor(t)
                
                ## Concurrent/threaded execution for ccor(t)
                tasks = [(xi,zi,yii,do_density_weighting) for xi in range(nx) for zi in range(nz)]
                with ThreadPoolExecutor(max_workers=n_threads) as executor:
                    results = executor.map(lambda task: __ccor_kernel_t(*task,), tasks)
                    for xi,zi,result in results:
                        R_xz[xi,zi,:] = result
                
                ## avg in [x,z] & write in rank context
                Rt[scalar][yiii,:] = np.mean(R_xz, axis=(0,1), dtype=np.float64)
                
                # ===========================================================================
                # Coherence [t] : loop over [x,z]
                # ===========================================================================
                
                ## Coherence buffer for [y] loop inner
                Coh_xz = np.zeros((nx,nz,nf), dtype=np.complex128) ## [x,z] range
                P_xz   = np.zeros((nx,nz,nf), dtype=np.complex128) ## [x,z] range
                
                ## Concurrent/threaded execution for Pxy & Coherence
                tasks = [(xi,zi,yii,do_density_weighting) for xi in range(nx) for zi in range(nz)]
                with ThreadPoolExecutor(max_workers=n_threads) as executor:
                    results = executor.map(lambda task: __coherence_kernel_t(*task,), tasks)
                    for xi,zi,P,Coh in results:
                        Coh_xz[xi,zi,:] = Coh[fp]
                        P_xz[xi,zi,:]   = P[fp]
                
                # if np.isnan(Coh_xz).any():
                #     print('NaNs in Coh_xz')
                #     self.comm.Abort(1)
                # if np.isnan(P_xz).any():
                #     print('NaNs in P_xz')
                #     self.comm.Abort(1)
                
                Coh_t[scalar][yiii,:] = np.mean(Coh_xz , axis=(0,1), dtype=np.complex128)
                Pt[scalar][yiii,:]    = np.mean(P_xz   , axis=(0,1), dtype=np.complex128)
                
                # ===========================================================================
                # Coherence [z] : loop over [x,t]
                # ===========================================================================
                
                ## Coherence buffer for [y] loop inner
                Coh_xt = np.zeros((nx,nt,nkz), dtype=np.complex128) ## [x,t] range
                P_xt   = np.zeros((nx,nt,nkz), dtype=np.complex128) ## [x,t] range
                
                ## Concurrent/threaded execution for Pxy & Coherence
                tasks = [(xi,ti,yii,do_density_weighting) for xi in range(nx) for ti in range(nt)]
                with ThreadPoolExecutor(max_workers=n_threads) as executor:
                    results = executor.map(lambda task: __coherence_kernel_z(*task,), tasks)
                    for xi,ti,P,Coh in results:
                        Coh_xt[xi,ti,:] = Coh[kzp]
                        P_xt[xi,ti,:]   = P[kzp]
                
                # if np.isnan(Coh_xt).any():
                #     print('NaNs in Coh_xt')
                #     self.comm.Abort(1)
                # if np.isnan(P_xt).any():
                #     print('NaNs in P_xt')
                #     self.comm.Abort(1)
                
                Coh_z[scalar][yiii,:] = np.mean(Coh_xt , axis=(0,1), dtype=np.complex128)
                Pz[scalar][yiii,:]    = np.mean(P_xt   , axis=(0,1), dtype=np.complex128)
                
                # ===========================================================================
            
            self.comm.Barrier()
            t_delta = timeit.default_timer() - t_start
            if verbose: tqdm.write(even_print(msg, format_time_string(t_delta), s=True))
            if verbose: progress_bar.update() ## (scalar, [y] chunk) progress
            
            #break ## DEBUG ([y] loop)
        #break ## DEBUG (scalar loop)
    
    if verbose: progress_bar.close()
    self.comm.Barrier()
    if verbose: print(72*'-')
    
    # ==============================================================
    # Write HDF5 (.h5) file
    # ==============================================================
    
    ## Open on rank 0 and write attributes, dimensions, etc.
    if (self.rank==0):
        with h5py.File(fn_h5_out, 'w') as hfw:
            
            ## Write floats,ints as top-level attributes
            for key,val in data.items():
                if isinstance(data[key], (int,np.int32,np.int64)):
                    hfw.attrs[key] = val
                elif isinstance(data[key], (float,np.float32,np.float64)):
                    hfw.attrs[key] = val
                elif isinstance(data[key], np.ndarray):
                    pass
                else:
                    print(f'key {key} is type {str(type(data[key]))}')
                    self.comm.Abort(1)
            
            ## Write dim arrays
            hfw.create_dataset( 'dims/x'      , data=x      ) ## [m]
            hfw.create_dataset( 'dims/y'      , data=y      ) ## [m]
            hfw.create_dataset( 'dims/z'      , data=z      ) ## [m]
            hfw.create_dataset( 'dims/t'      , data=t      ) ## [s]
            hfw.create_dataset( 'dims/freq'   , data=freq   ) ## [1/s] | [Hz]
            hfw.create_dataset( 'dims/kz'     , data=kz     ) ## [1/m]
            hfw.create_dataset( 'dims/lags_t' , data=lags_t ) ## [s]
            
            ## Initialize datasets
            for scalar in scalars:
                hfw.create_dataset( f'covariance/{scalar}'  , shape=(ny,)         , dtype=np.float64    , chunks=None         , data=np.full((ny,),0.,np.float64)         )
                hfw.create_dataset( f'Rt/{scalar}'          , shape=(ny,n_lags_t) , dtype=np.float64    , chunks=(1,n_lags_t) , data=np.full((ny,n_lags_t),0.,np.float64) )
                hfw.create_dataset( f'Pt/{scalar}'          , shape=(ny,nf)       , dtype=np.complex128 , chunks=(1,nf)       , data=np.full((ny,nf),0.,np.complex128)    )
                hfw.create_dataset( f'Pz/{scalar}'          , shape=(ny,nkz)      , dtype=np.complex128 , chunks=(1,nkz)      , data=np.full((ny,nkz),0.,np.complex128)   )
                hfw.create_dataset( f'Coh_t/{scalar}'       , shape=(ny,nf)       , dtype=np.complex128 , chunks=(1,nf)       , data=np.full((ny,nf),0.,np.complex128)    )
                hfw.create_dataset( f'Coh_z/{scalar}'       , shape=(ny,nkz)      , dtype=np.complex128 , chunks=(1,nkz)      , data=np.full((ny,nkz),0.,np.complex128)   )
            
            ## Initialize datasets 1D [y] mean
            for scalar in avg_Re.dtype.names:
                hfw.create_dataset( f'avg/Re/{scalar}', shape=(ny,), dtype=np.float64, chunks=None, data=np.full((ny,),0.,np.float64) )
            for scalar in avg_Fv.dtype.names:
                hfw.create_dataset( f'avg/Fv/{scalar}', shape=(ny,), dtype=np.float64, chunks=None, data=np.full((ny,),0.,np.float64) )
    
    self.comm.Barrier()
    
    with h5py.File(fn_h5_out, 'a', driver='mpio', comm=self.comm) as hfw:
        
        ## Collectively write covariance,Rt,P,Coh
        for scalar in scalars:
            dset = hfw[f'covariance/{scalar}']
            with dset.collective:
                dset[ry1:ry2] = covariance[scalar][:]
            dset = hfw[f'Rt/{scalar}']
            with dset.collective:
                dset[ry1:ry2,:] = Rt[scalar][:,:]
            dset = hfw[f'Pt/{scalar}']
            with dset.collective:
                dset[ry1:ry2,:] = Pt[scalar][:,:]
            dset = hfw[f'Pz/{scalar}']
            with dset.collective:
                dset[ry1:ry2,:] = Pz[scalar][:,:]
            dset = hfw[f'Coh_t/{scalar}']
            with dset.collective:
                dset[ry1:ry2,:] = Coh_t[scalar][:,:]
            dset = hfw[f'Coh_z/{scalar}']
            with dset.collective:
                dset[ry1:ry2,:] = Coh_z[scalar][:,:]
        
        ## Collectively write 1D [y] avgs (Reynolds,Favre)
        for scalar in avg_Re.dtype.names:
            dset = hfw[f'avg/Re/{scalar}']
            with dset.collective:
                dset[ry1:ry2] = avg_Re[scalar][:]
        for scalar in avg_Fv.dtype.names:
            dset = hfw[f'avg/Fv/{scalar}']
            with dset.collective:
                dset[ry1:ry2] = avg_Fv[scalar][:]
    
    ## Report file contents
    self.comm.Barrier()
    if (self.rank==0):
        even_print( os.path.basename(fn_h5_out) , f'{(os.path.getsize(fn_h5_out)/1024**2):0.1f} [MB]' )
        print(72*'-')
        with h5py.File(fn_h5_out,'r') as hfr:
            h5_print_contents(hfr)
    self.comm.Barrier()
    
    if verbose: print(72*'-')
    if verbose: print('total time : rgd.calc_wall_coh_xpln() : %s'%format_time_string((timeit.default_timer() - t_start_func)))
    if verbose: print(72*'-')
    return
