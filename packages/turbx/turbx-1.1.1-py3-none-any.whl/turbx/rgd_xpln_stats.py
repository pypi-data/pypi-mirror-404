import os
import re
import sys
import timeit
from pathlib import Path, PurePosixPath

import h5py
import numpy as np
import psutil
from mpi4py import MPI
from tqdm import tqdm

from .h5 import h5_print_contents
from .utils import even_print, format_time_string

# ======================================================================

def _calc_statistics_xpln(self,**kwargs):
    '''
    Calculate statistics for an unsteady volumetric measurement
        which has a small number of points in the [x] direction
    - Mean
    - Covariance
    - Triple products
    - Skewness, Kurtosis
    - Probability distribution function (PDF)
    '''
    
    if (self.rank==0):
        verbose = True
    else:
        verbose = False
    
    if verbose: print('\n'+'rgd.calc_statistics_xpln()'+'\n'+72*'-')
    t_start_func = timeit.default_timer()
    
    ## assert that the opened RGD has fsubtype 'unsteady' (i.e. is NOT a prime file)
    if (self.fsubtype!='unsteady'):
        raise ValueError
    
    rx = kwargs.get('rx',1)
    ry = kwargs.get('ry',1)
    rz = kwargs.get('rz',1)
    rt = kwargs.get('rt',1)
    
    # cy = kwargs.get('cy',1) ## number of subdivisions per rank [y] range
    # if not isinstance(cy,int):
    #     raise TypeError('cy should be an int')
    # if (cy<1):
    #     raise TypeError('cy should be an int')
    
    sy = kwargs.get('sy',1) ## number of [y] layers to read at a time
    if not isinstance(sy,int) or (sy<1):
        raise TypeError('sy should be a positive non-zero int')
    
    #fn_dat_stats = kwargs.get('fn_dat_stats',None) ## filename for output pickle (.dat) file
    fn_h5_out  = kwargs.get('fn_h5_out',None) ## filename for output HDF5 (.h5) file
    
    n_bins = kwargs.get('n_bins',512) ## n bins for histogram (PDF) calculation
    
    ## For now only distribute data in [y] --> allows [x,z] mean before Send/Recv
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
    ryl_ = np.array_split(np.arange(self.ny,dtype=np.int64),ry)
    ryl = [[b[0],b[-1]+1] for b in ryl_ ]
    ry1,ry2 = ryl[self.rank]
    nyr = ry2 - ry1
    
    ## Check all [y] ranges have same size
    for ryl_ in ryl:
        if not (ryl_[1]-ryl_[0]==nyr):
            raise ValueError('[y] chunks are not even in size')
    
    # ## [y] sub chunk range --> cyl = list of ranges in ry1:ry2
    # ## cy is the NUMBER of chunks for the rank sub-range
    # cyl_ = np.array_split( np.arange(ry1,ry2) , min(cy,nyr) )
    # cyl  = [[b[0],b[-1]+1] for b in cyl_ ]
    # 
    # for nyc_ in [ cyl_[1]-cyl_[0] for cyl_ in cyl ]:
    #     if (nyc_ < 1):
    #         #raise ValueError
    #         print(f'rank {self.rank:d}: sub-range is <1')
    #         self.comm.Abort(1)
    # 
    # if 1: ## assert that [y] sub-chunk ranges are correct
    #     
    #     yi = np.arange(self.ny, dtype=np.int32)
    #     
    #     local_indices = []
    #     for cyl_ in cyl:
    #         cy1, cy2 = cyl_
    #         local_indices += [ yi_ for yi_ in yi[cy1:cy2] ]
    #     
    #     G = self.comm.gather([ self.rank , local_indices ], root=0)
    #     G = self.comm.bcast(G, root=0)
    #     
    #     all_indices = []
    #     for G_ in G:
    #         all_indices += G_[1]
    #     all_indices = np.array( sorted(all_indices), dtype=np.int32 )
    #     
    #     if not np.array_equal( all_indices , yi ):
    #         raise AssertionError
    
    if (nyr%sy!=0):
        raise ValueError('nyr not divisible by sy')
    
    ## Output filename : HDF5 (.h5)
    if (fn_h5_out is None): ## automatically determine name
        fname_path = os.path.dirname(self.fname)
        fname_base = os.path.basename(self.fname)
        fname_root, fname_ext = os.path.splitext(fname_base)
        fname_root = re.findall(r'io\S+_mpi_[0-9]+', fname_root)[0]
        fname_stats_h5_base = fname_root+'_stats.h5'
        fn_h5_out = str(PurePosixPath(fname_path, fname_stats_h5_base))
    if (Path(fn_h5_out).suffix != '.h5'):
        raise ValueError(f"fn_h5_out='{str(fn_h5_out)}' must end in .h5")
    if os.path.isfile(fn_h5_out):
        #if (os.path.getsize(fn_h5_out) > 8*1024**3):
        #    raise ValueError(f"fn_h5_out='{str(fn_h5_out)}' exists and is >8 [GB]. exiting for your own safety.")
        if (fn_h5_out == self.fname):
            raise ValueError(f"fn_h5_out='{str(fn_h5_out)}' cannot be same as input filename.")
    
    # ===
    
    if verbose: even_print( 'fn_h5'      , self.fname )
    if verbose: even_print( 'fn_h5_out'  , fn_h5_out  )
    if verbose: print(72*'-')
    self.comm.Barrier()
    
    ## The data dictionary to be pickled later
    data = {}
    
    ## infile
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
    #if verbose: even_print('n_threads',f'{n_threads:d}')
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
    
    ## Dimensional [s]
    dt = self.dt * self.tchar
    np.testing.assert_allclose(dt, t[1]-t[0], rtol=1e-12, atol=1e-12)
    
    t_meas = self.duration * self.tchar
    np.testing.assert_allclose(t_meas, t.max()-t.min(), rtol=1e-12, atol=1e-12)
    
    zrange = z.max() - z.min()
    
    data['x'] = x
    data['y'] = y
    data['z'] = z
    
    data['t'] = t
    data['t_meas'] = t_meas
    data['dt'] = dt
    data['dz'] = dz
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
        #print(72*'-')
    
    # ===
    
    ## key    = str:scalar name
    ## value  = tuple:recipe,
    ##          bool:do_mean,
    ##          bool:do_pdf,
    ##          bool:do_skew_kurt
    ##
    ## recipe elements:
    ##    - if tuple : ( str:scalar , bool:ρ weighting ) --> always mean-removed
    ##    - if str   : str:scalar
    
    scalars_dict = {
        
        'r_uIIuIIuII' : [ ( 'rho', ('u',True ), ('u',True ), ('u',True ) ), True,True,True ], ## ρ·u″u″u″
        'uIuIuI'      : [ (        ('u',False), ('u',False), ('u',False) ), True,True,True ], ## u′u′u′
        
        'r_uIIuIIvII' : [ ( 'rho', ('u',True ), ('u',True ), ('v',True ) ), True,True,True ], ## ρ·u″u″v″
        'uIuIvI'      : [ (        ('u',False), ('u',False), ('v',False) ), True,True,True ], ## u′u′v′
        
        'r_uIIvIIvII' : [ ( 'rho', ('u',True ), ('v',True ), ('v',True ) ), True,True,True ], ## ρ·u″v″v″
        'uIvIvI'      : [ (        ('u',False), ('v',False), ('v',False) ), True,True,True ], ## u′v′v′
        
        'r_vIIvIIvII' : [ ( 'rho', ('v',True ), ('v',True ), ('v',True ) ), True,True,True ], ## ρ·v″v″v″
        'vIvIvI'      : [ (        ('v',False), ('v',False), ('v',False) ), True,True,True ], ## v′v′v′
        
        'r_vIIwIIwII' : [ ( 'rho', ('v',True ), ('w',True ), ('w',True ) ), True,True,True ], ## ρ·v″w″w″
        'vIwIwI'      : [ (        ('v',False), ('w',False), ('w',False) ), True,True,True ], ## v′w′w′
        
        'r_uIIuII' : [ ( 'rho', ('u',True ), ('u',True ) ), True,True,True ], ## ρ·u″u″
        'r_vIIvII' : [ ( 'rho', ('v',True ), ('v',True ) ), True,True,True ], ## ρ·v″v″
        'r_wIIwII' : [ ( 'rho', ('w',True ), ('w',True ) ), True,True,True ], ## ρ·w″w″
        'r_uIIvII' : [ ( 'rho', ('u',True ), ('v',True ) ), True,True,True ], ## ρ·u″v″
        'r_uIIwII' : [ ( 'rho', ('u',True ), ('w',True ) ), True,True,True ], ## ρ·u″w″
        'r_vIIwII' : [ ( 'rho', ('v',True ), ('w',True ) ), True,True,True ], ## ρ·v″w″
        
        'uIuI'     : [ (        ('u',False), ('u',False) ), True,True,True ], ## u′u′
        'vIvI'     : [ (        ('v',False), ('v',False) ), True,True,True ], ## v′v′
        'wIwI'     : [ (        ('w',False), ('w',False) ), True,True,True ], ## w′w′
        'uIvI'     : [ (        ('u',False), ('v',False) ), True,True,True ], ## u′v′
        'uIwI'     : [ (        ('u',False), ('w',False) ), True,True,True ], ## u′w′
        'vIwI'     : [ (        ('v',False), ('w',False) ), True,True,True ], ## v′w′
        
        'uITI'     : [ (        ('u',False), ('T',False) ), True,True,True ], ## u′T′
        'vITI'     : [ (        ('v',False), ('T',False) ), True,True,True ], ## v′T′
        'wITI'     : [ (        ('w',False), ('T',False) ), True,True,True ], ## w′T′
        
        'TITI'     : [ (        ('T',False), ('T',False) ), True,True,False ], ## T′T′
        'TIITII'   : [ (        ('T',True ), ('T',True ) ), True,True,False ], ## T″T″
        'r_TIITII' : [ ( 'rho', ('T',True ), ('T',True ) ), True,True,False ], ## ρ·T″T″
        
        'rho'      : [ ( 'rho',                ) ,  True, True, False, ], ## ρ
        'rhoI'     : [ (        ('rho',False), ) , False, True,  True, ], ## ρ′
        
        'T'        : [ ( 'T',                )   ,  True, True, False, ], ## T
        'TI'       : [ (        ('T',False), )   , False, True,  True, ], ## T′
        'TII'      : [ (        ('T',True ), )   , False, True,  True, ], ## T″
        'r_TII'    : [ ( 'rho', ('T',True ), )   , False, True,  True, ], ## ρ·T″
        
        'p'        : [ ( 'p',              )   ,  True, True, False, ], ## p
        'pI'       : [ (      ('p',False), )   , False, True,  True, ], ## p′
        
        'u'        : [ ( 'u',                ) ,  True, True, False, ], ## u
        'uI'       : [ (        ('u',False), ) , False, True,  True, ], ## u′
        #'uII'      : [ (        ('u',True ), ) , False, True,  True, ], ## u″
        'r_uII'    : [ ( 'rho', ('u',True ), ) , False, True,  True, ], ## ρ·u″
        
        'v'        : [ ( 'v',                ) ,  True, True, False, ], ## v
        'vI'       : [ (        ('v',False), ) , False, True,  True, ], ## v′
        'r_vII'    : [ ( 'rho', ('v',True ), ) , False, True,  True, ], ## ρ·v″
        
        'w'        : [ ( 'w',                ) ,  True, True, False, ], ## w
        'wI'       : [ (        ('w',False), ) , False, True,  True, ], ## w′
        'r_wII'    : [ ( 'rho', ('w',True ), ) , False, True,  True, ], ## ρ·w″
        
        }
    
    dtype_unsteady = np.float64
    
    scalars_avg  = []
    scalars_pdf  = []
    scalars_hos_ = []
    for s,ss in scalars_dict.items():
        recipe, do_mean, do_pdf, do_skew_kurt = ss
        if do_mean:
            scalars_avg.append(s)
        if do_pdf:
            scalars_pdf.append(s)
        if do_skew_kurt:
            scalars_hos_.append(s)
    
    scalars_hos=[]
    for s_ in ['skew','kurt']:
        for ss_ in scalars_hos_:
            scalars_hos.append(f'{ss_}_{s_}')
    
    data_avg  = np.zeros(shape=(nyr,)         , dtype={'names':scalars_avg, 'formats':[ np.float64 for sss in scalars_avg ]})
    data_bins = np.zeros(shape=(nyr,n_bins+1) , dtype={'names':scalars_pdf, 'formats':[ np.float64 for sss in scalars_pdf ]})
    data_pdf  = np.zeros(shape=(nyr,n_bins)   , dtype={'names':scalars_pdf, 'formats':[ np.float64 for sss in scalars_pdf ]})
    data_hos  = np.zeros(shape=(nyr,)         , dtype={'names':scalars_hos, 'formats':[ np.float64 for sss in scalars_hos ]})
    
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
        print(72*'-')
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
    
    self.comm.Barrier()
    if verbose:
        progress_bar = tqdm(
            #total=cy*len(scalars_dict),
            total=len(scalars_dict)*(nyr//sy),
            ncols=100,
            desc='statistics',
            leave=True,
            file=sys.stdout,
            mininterval=0.1,
            smoothing=0.,
            #bar_format="\033[B{l_bar}{bar}| {n}/{total} [{percentage:.1f}%] {elapsed}/{remaining}\033[A\n\b",
            bar_format="{l_bar}{bar}| {n}/{total} [{percentage:.1f}%] {elapsed}/{remaining}",
            ascii="░█",
            colour='#FF6600',
            )
    
    ## Scalar dict loop
    for s,ss in scalars_dict.items(): ## e.g. where s='r_uIIvII' & ss=[ ( 'rho', ('u',True ), ('v',True ) ), True,True,False ]
        
        if verbose: tqdm.write(72*'-')
        
        recipe, do_mean, do_pdf, do_skew_kurt = ss
        
        if verbose:
            tqdm.write(even_print('computing',s,s=True,))
        
        # if verbose: ## report per-rank read shape
        #     nyc_max = max([ cyl_[1]-cyl_[0] for cyl_ in cyl ])
        #     data_gb = 8 * nx * nyc_max * nz * nt / 1024**3
        #     tqdm.write(even_print('read shape per rank', f'[{nx:d},{nyc_max:d},{nz:d},{nt:d}] · 8 [Bytes] --> {data_gb:0.1f} [GB]', s=True))
        #     tqdm.write(even_print('mem per read', f'{self.n_ranks*data_gb:0.1f} [GB]', s=True))
        #     tqdm.write(even_print('mem per read ×6', f'{self.n_ranks*data_gb*6.:0.3f} [GB]', s=True)) ## genoa3tb64c, ?R ...
        
        ## Should ρ be read?
        read_rho = False
        for s_ in recipe:
            if isinstance(s_, str) and (s_=='rho'):
                read_rho = True
            elif isinstance(s_, str) and (s_!='rho'):
                pass
            elif isinstance(s_, tuple):
                if not isinstance(s_[1], bool):
                    raise ValueError
                if s_[1]: ## i.e. density-weighted
                    read_rho = True
            else:
                raise ValueError
        
        ## [y] loop outer (grid subchunks within rank)
        # for cyl_ in cyl:
        #     cy1, cy2 = cyl_
        #     nyc = cy2 - cy1
        
        for ci in range(nyr//sy):
            cy1 = ry1 + ci*sy
            cy2 = cy1 + sy
            nyc = cy2 - cy1
            
            ## Read ρ
            if read_rho:
                
                #rho = np.zeros(shape=(nx,nyc,nz,nt), dtype=dtype_unsteady) ## buffer... chunk range context
                
                dset = self['data/rho']
                self.comm.Barrier()
                t_start = timeit.default_timer()
                if self.usingmpi:
                    with dset.collective:
                        #rho[:,:,:,:] = dset[:,:,cy1:cy2,:].T.astype(np.float64)
                        rho = dset[:,:,cy1:cy2,:].T
                else:
                    #rho[:,:,:,:] = dset[()].T.astype(np.float64)
                    rho = dset[()].T
                self.comm.Barrier()
                t_delta = timeit.default_timer() - t_start
                data_gb = dset.dtype.itemsize * self.nx * ry * (cy2-cy1) * self.nz * self.nt / 1024**3
                if verbose:
                    tqdm.write(even_print('read: ρ', '%0.3f [GB]  %0.3f [s]  %0.3f [GB/s]'%(data_gb,t_delta,(data_gb/t_delta)), s=True))
                
                ## Cast to double
                rho = rho.astype(np.float64)
                
                ## Re-dimensionalize
                rho *= self.rho_inf
                
                ## ρ mean in [t] --> leave [x,y,z,1]
                rho_avg = np.mean(rho, axis=3, dtype=np.float64, keepdims=True)
            
            else:
                rho     = None ; del rho
                rho_avg = None ; del rho_avg
            
            ## Product buffer for multiplication --> !!! notices ones() here and not zeros() !!!
            data_accum = np.ones(shape=(nx,nyc,nz,nt), dtype=dtype_unsteady) ## chunk range context
            
            ## Read unsteady scalar data, remove mean, <density weight>, multiply
            for sss in recipe:
                
                if isinstance(sss, str) and (sss=='rho'): ## ρ
                    
                    ## Multiply product accumulator, ρ was already read and is already dimensional
                    data_accum *= rho
                
                elif isinstance(sss, str) and (sss!='rho'): ## scalar which will NOT be mean-removed
                    
                    #data_X = np.zeros(shape=(nx,nyc,nz,nt), dtype=dtype_unsteady) ## buffer... chunk range context
                    dset = self[f'data/{sss}']
                    
                    ## Read
                    self.comm.Barrier()
                    t_start = timeit.default_timer()
                    if self.usingmpi:
                        with dset.collective:
                            #data_X[:,:,:,:] = dset[:,:,cy1:cy2,:].T.astype(np.float64)
                            #data_X = np.copy( dset[:,:,cy1:cy2,:].T )
                            data_X = dset[:,:,cy1:cy2,:].T
                    else:
                        #data_X[:,:,:,:] = dset[()].T.astype(np.float64)
                        #data_X = np.copy( dset[()].T )
                        data_X = dset[()].T
                    self.comm.Barrier()
                    t_delta = timeit.default_timer() - t_start
                    data_gb = dset.dtype.itemsize * self.nx * ry * (cy2-cy1) * self.nz * self.nt / 1024**3
                    if verbose:
                        tqdm.write(even_print(f'read: {sss}', '%0.3f [GB]  %0.3f [s]  %0.3f [GB/s]'%(data_gb,t_delta,(data_gb/t_delta)), s=True))
                    
                    ## Cast to double
                    data_X = data_X.astype(np.float64)
                    
                    ## Re-dimensionalize
                    if sss in ['u','v','w',]:
                        data_X *= self.U_inf
                    elif sss in ['T',]:
                        data_X *= self.T_inf
                    elif sss in ['rho',]:
                        data_X *= self.rho_inf
                    elif sss in ['p',]:
                        data_X *= self.rho_inf * self.U_inf**2
                    else:
                        raise ValueError(f"condition needed for redimensionalizing '{str(sss)}'")
                    
                    ## MULTIPLY product accumulator
                    data_accum *= data_X
                
                elif isinstance(sss, tuple): ## scalar which WILL be mean-removed (with- or without ρ-weighting)
                    
                    if (len(sss)!=2):
                        raise ValueError
                    
                    sn, do_density_weighting = sss ## e.g. ('u',True)
                    
                    #data_X = np.zeros(shape=(nx,nyc,nz,nt), dtype=dtype_unsteady) ## buffer... chunk range context
                    dset = self[f'data/{sn}']
                    
                    ## Read
                    self.comm.Barrier()
                    t_start = timeit.default_timer()
                    if self.usingmpi:
                        with dset.collective:
                            #data_X[:,:,:,:] = dset[:,:,cy1:cy2,:].T.astype(np.float64)
                            #data_X = np.copy( dset[:,:,cy1:cy2,:].T )
                            data_X = dset[:,:,cy1:cy2,:].T
                    else:
                        #data_X[:,:,:,:] = dset[()].T.astype(np.float64)
                        #data_X = np.copy( dset[()].T )
                        data_X = dset[()].T
                    self.comm.Barrier()
                    t_delta = timeit.default_timer() - t_start
                    data_gb = dset.dtype.itemsize * self.nx * ry * (cy2-cy1) * self.nz * self.nt / 1024**3
                    if verbose:
                        tqdm.write(even_print(f'read: {sn}', '%0.3f [GB]  %0.3f [s]  %0.3f [GB/s]'%(data_gb,t_delta,(data_gb/t_delta)), s=True))
                    
                    ## Cast to double
                    data_X = data_X.astype(np.float64)
                    
                    ## Redimensionalize
                    if sn in ['u','v','w',]:
                        data_X *= self.U_inf
                    elif sn in ['T',]:
                        data_X *= self.T_inf
                    elif sn in ['rho',]:
                        data_X *= self.rho_inf
                    elif sn in ['p',]:
                        data_X *= self.rho_inf * self.U_inf**2
                    else:
                        raise ValueError(f"condition needed for redimensionalizing '{str(sn)}'")
                    
                    ## avg(□) or avg(ρ·□)/avg(ρ)
                    if do_density_weighting:
                        data_X_mean = np.mean( rho*data_X , axis=3, dtype=np.float64, keepdims=True) ## [x,y,z,1]
                        data_X_mean /= rho_avg
                    else:
                        data_X_mean = np.mean( data_X , axis=3, dtype=np.float64, keepdims=True) ## [x,y,z,1]
                    
                    ## Reynolds prime □′ or Favre prime □″
                    data_X -= data_X_mean
                    
                    ## Assert avg(□′)==0 or avg(ρ·□″)==0
                    if do_density_weighting:
                        a_ = np.mean(rho*data_X, axis=3, dtype=np.float64, keepdims=True)
                    else:
                        a_ = np.mean(data_X, axis=3, dtype=np.float64, keepdims=True)
                    #np.testing.assert_allclose(a_, np.zeros_like(a_), atol=1e-3)
                    if not np.allclose( a_, np.zeros_like(a_), atol=1e-3 ):
                        print(f'rank {self.rank:d}: avg(□′)!=0 or avg(ρ·□″)!=0')
                        self.comm.Abort(1)
                    
                    ## MULTIPLY product accumulator by □′ | □″
                    data_accum *= data_X
                
                else:
                    raise ValueError
            
            # ===============================================================================
            # At this point you have the UNSTEADY 4D [x,y,z,t] data according to 'recipe'
            # ===============================================================================
            
            yiA = cy1 - ry1
            yiB = cy2 - ry1
            
            ## Mean in [t] --> leave [x,y,z,1]
            d_mean = np.mean( data_accum, axis=(3,), keepdims=True, dtype=np.float64)
            if ( d_mean.shape != (nx,nyc,nz,1,) ):
                print(f'rank {self.rank:d}: shape violation')
                self.comm.Abort(1)
            
            if do_mean: ## mean in [x,z] --> leave [y]
                data_avg[s][yiA:yiB] = np.squeeze( np.mean( d_mean, axis=(0,2), dtype=np.float64) )
            
            ## [y] loop inner ([y] indices within subdivision within rank)
            for yi in range(cy1,cy2):
                
                yii  = yi - cy1 ## chunk local
                yiii = yi - ry1 ## rank local
                
                if do_pdf:
                    
                    d_ = np.copy( data_accum[:,yii,:,:].ravel() )
                    if ( d_.shape != (nx*1*nz*nt,) ):
                        print(f'rank {self.rank:d}: shape violation')
                        self.comm.Abort(1)
                    pdf_ , bin_edges_ = np.histogram( d_ , bins=n_bins , density=True )
                    data_bins[s][yiii,:] = bin_edges_
                    data_pdf[s][yiii,:]  = pdf_
                
                if do_skew_kurt:
                    
                    #d_ = np.copy( data_accum[:,yii,:,:] ) ## [x,1,z,t]
                    d_ = np.zeros(shape=(nx,1,nz,nt), dtype=dtype_unsteady)
                    d_[:,:,:,:] = data_accum[:,yii,:,:][:,np.newaxis,:,:] ## [x,1,z,t]
                    if ( d_.shape != (nx,1,nz,nt) ):
                        print(f'rank {self.rank:d}: shape violation')
                        self.comm.Abort(1)
                    
                    ## ## is it interpretable as a Reynolds mean-removed quantity? (□′)
                    ## interpretable_as_Re_mean = False
                    ## a_ = np.mean(d_, axis=3, dtype=np.float64, keepdims=True) ## mean in [t]
                    ## np.testing.assert_equal( a_.shape, (nx,1,nz,1,) )
                    ## if np.allclose(a_, np.zeros_like(a_), atol=1e-10):
                    ##     interpretable_as_Re_mean = True
                    ## 
                    ## ## is it interpretable as a Favre mean-removed quantity? (□″)
                    ## interpretable_as_Fv_mean = False
                    ## if read_rho and not interpretable_as_Re_mean:
                    ##     #rho_ = np.copy( rho[:,yii,:,:] )
                    ##     rho_ = np.zeros(shape=(nx,1,nz,nt), dtype=dtype_unsteady)
                    ##     rho_[:,:,:,:] = rho[:,yii,:,:][:,np.newaxis,:,:] ## [x,1,z,t]
                    ##     np.testing.assert_equal( rho_.shape, (nx,1,nz,nt) )
                    ##     
                    ##     a_ = np.mean(d_*rho_, axis=3, dtype=np.float64, keepdims=True) ## mean in [t]
                    ##     np.testing.assert_equal( a_.shape, (nx,1,nz,1,) )
                    ##     if np.allclose(a_, np.zeros_like(a_), atol=1e-10):
                    ##         interpretable_as_Fv_mean = True
                    ## 
                    ## if (not interpretable_as_Re_mean) and (not interpretable_as_Fv_mean):
                    ##     print(f'{s} has non-zero Favre and Reynolds mean, i.e. is not <□′>!=0 and <ρ□″>!=0')
                    ##     self.comm.Abort(1)
                    
                    dI = np.copy( d_.ravel() ) ## □′ or □″
                    if ( dI.shape != (nx*1*nz*nt,) ):
                        print(f'rank {self.rank:d}: shape violation')
                        self.comm.Abort(1)
                    
                    d_std = np.sqrt( np.mean( dI**2 , dtype=np.float64 ) )
                    
                    if np.isclose(d_std, 0., atol=1e-08):
                        d_skew = 0.
                        d_kurt = 0.
                    else:
                        d_skew = np.mean( dI**3 , dtype=np.float64 ) / d_std**3
                        d_kurt = np.mean( dI**4 , dtype=np.float64 ) / d_std**4
                    
                    data_hos[f'{s}_skew'][yiii] = d_skew
                    data_hos[f'{s}_kurt'][yiii] = d_kurt
            
            self.comm.Barrier() ## [y] loop outer (chunks within rank)
            if verbose: progress_bar.update()
            
            # break ## debug
    
    if verbose:
        progress_bar.close()
        print(72*'-')
    
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
            
            ## Write numpy arrays
            hfw.create_dataset( 'dims/x' , data=x ) ## [m]
            hfw.create_dataset( 'dims/y' , data=y ) ## [m]
            hfw.create_dataset( 'dims/z' , data=z ) ## [m]
            hfw.create_dataset( 'dims/t' , data=t ) ## [s]
            
            ## Initialize datasets
            for scalar in scalars_avg:
                hfw.create_dataset( f'avg/{scalar}', shape=(ny,), dtype=np.float64, chunks=None, data=np.full((ny,),0.,np.float64) )
            for scalar in scalars_pdf:
                hfw.create_dataset( f'bins/{scalar}', shape=(ny,n_bins+1), dtype=np.float64, chunks=(1,n_bins+1), data=np.full((ny,n_bins+1),0.,np.float64) )
            for scalar in scalars_pdf:
                hfw.create_dataset( f'pdf/{scalar}', shape=(ny,n_bins), dtype=np.float64, chunks=(1,n_bins), data=np.full((ny,n_bins),0.,np.float64) )
            for scalar in scalars_hos:
                hfw.create_dataset( f'hos/{scalar}', shape=(ny,), dtype=np.float64, chunks=None, data=np.full((ny,),0.,np.float64) )
    
    self.comm.Barrier()
    
    with h5py.File(fn_h5_out, 'a', driver='mpio', comm=self.comm) as hfw:
        
        ## Collectively write avg,bins,pdf,hos
        for scalar in scalars_avg:
            dset = hfw[f'avg/{scalar}']
            with dset.collective:
                dset[ry1:ry2] = data_avg[scalar][:]
        for scalar in scalars_pdf:
            dset = hfw[f'bins/{scalar}']
            with dset.collective:
                dset[ry1:ry2,:] = data_bins[scalar][:,:]
        for scalar in scalars_pdf:
            dset = hfw[f'pdf/{scalar}']
            with dset.collective:
                dset[ry1:ry2,:] = data_pdf[scalar][:,:]
        for scalar in scalars_hos:
            dset = hfw[f'hos/{scalar}']
            with dset.collective:
                dset[ry1:ry2] = data_hos[scalar][:]
    
    ## Report file contents
    self.comm.Barrier()
    if (self.rank==0):
        even_print( os.path.basename(fn_h5_out) , f'{(os.path.getsize(fn_h5_out)/1024**2):0.1f} [MB]' )
        print(72*'-')
        with h5py.File(fn_h5_out,'r') as hfr:
            h5_print_contents(hfr)
    self.comm.Barrier()
    
    if verbose: print(72*'-')
    if verbose: print('total time : rgd.calc_statistics_xpln() : %s'%format_time_string((timeit.default_timer() - t_start_func)))
    if verbose: print(72*'-')
    return
