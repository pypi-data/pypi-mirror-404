import os
import sys
import time
import timeit
from pathlib import Path, PurePosixPath

import h5py
import numpy as np
from tqdm import tqdm

from .h5 import h5_print_contents
from .utils import even_print, format_time_string

# ======================================================================

def _calc_statistics_wall(self, **kwargs):
    '''
    Calculate statistics for an unsteady wall measurement
      which has dimensions (nx,1,nz)
    - mean
    - covariance
    - skewness, kurtosis
    - probability distribution function (PDF)
    '''
    
    if (self.rank==0):
        verbose = True
    else:
        verbose = False
    
    if verbose: print('\n'+'spd.calc_statistics_wall()'+'\n'+72*'-')
    t_start_func = timeit.default_timer()
    
    if not self.usingmpi:
        raise NotImplementedError('function is not implemented for non-MPI usage')
    
    h5py_is_mpi_build = h5py.h5.get_config().mpi
    if not h5py_is_mpi_build:
        if verbose: print('h5py was not compiled for parallel usage! exiting.')
        sys.exit(1)
    
    ri = kwargs.get('ri',1)
    rj = kwargs.get('rj',1)
    rt = kwargs.get('rt',1)
    
    fn_h5_stats = kwargs.get('fn_h5_stats',None) ## filename for output HDF5 (.h5) file
    n_bins      = kwargs.get('n_bins',512) ## n bins for histogram (PDF) calculation
    
    ## check data distribution
    if (rj!=1):
        raise AssertionError('rj!=1')
    if (rt!=1):
        raise AssertionError('rt!=1')
    if (ri*rj*rt != self.n_ranks):
        raise AssertionError('ri*rj*rt != self.n_ranks')
    if (ri>self.ni):
        raise AssertionError('ri>self.ni')
    if (self.ni%ri!=0):
        raise AssertionError('ni currently needs to be divisible by the n ranks')
    
    ## distribute data over i/[x]
    ril_ = np.array_split(np.arange(self.ni,dtype=np.int64),min(ri,self.ni))
    ril = [[b[0],b[-1]+1] for b in ril_ ]
    ri1,ri2 = ril[self.rank]
    nir = ri2 - ri1
    
    ## output filename : HDF5 (.h5)
    if (fn_h5_stats is None): ## automatically determine name
        fname_path = os.path.dirname(self.fname)
        fname_base = os.path.basename(self.fname)
        fname_root, fname_ext = os.path.splitext(fname_base)
        #fname_root = re.findall(r'io\S+_mpi_[0-9]+', fname_root)[0]
        fname_stats_h5_base = fname_root+'_stats.h5'
        fn_h5_stats = str(PurePosixPath(fname_path, fname_stats_h5_base))
    if (Path(fn_h5_stats).suffix != '.h5'):
        raise ValueError(f"fn_h5_stats='{str(fn_h5_stats)}' must end in .h5")
    if os.path.isfile(fn_h5_stats):
        if (fn_h5_stats == self.fname):
            raise ValueError(f"fn_h5_stats='{str(fn_h5_stats)}' cannot be same as input filename.")
    
    if verbose: even_print( 'fn_h5'        , self.fname   )
    if verbose: even_print( 'fn_h5_stats'  , fn_h5_stats  )
    if verbose: print(72*'-')
    if verbose: even_print( 'ni' , f'{self.ni:d}' )
    if verbose: even_print( 'nj' , f'{self.nj:d}' )
    if verbose: even_print( 'nt' , f'{self.nt:d}' )
    if verbose: print(72*'-')
    self.comm.Barrier()
    
    # ===
    
    ## the data dictionary to be pickled or written to .h5 later
    data = {}
    
    ## freestream data
    data['lchar']   = self.lchar
    data['U_inf']   = self.U_inf
    data['rho_inf'] = self.rho_inf
    data['T_inf']   = self.T_inf
    data['mu_inf']  = self.mu_inf
    data['p_inf']   = self.p_inf
    data['Ma']      = self.Ma
    data['Pr']      = self.Pr
    
    ## read in 1D coordinate arrays & re-dimensionalize
    x = np.copy( self['dims/x'][()] * self.lchar )
    z = np.copy( self['dims/z'][()] * self.lchar )
    t = np.copy( self['dims/t'][()] * self.tchar )
    data['x'] = x
    data['z'] = z
    data['t'] = t
    
    nx = self.ni
    ni = self.ni
    nz = self.nj
    nj = self.nj
    data['ni'] = ni
    data['nx'] = nx
    data['nj'] = nj
    data['nz'] = nz
    
    nt = self.nt
    data['nt'] = nt
    
    ## assert constant Δz
    dz0 = np.diff(z)[0]
    if not np.all(np.isclose(np.diff(z), dz0, rtol=1e-6)):
        raise NotImplementedError('Δz not constant')
    
    ## get Δt, dimensional [s]
    if hasattr(self,'dt'):
        dt = self.dt * self.tchar
        np.testing.assert_allclose(dt, t[1]-t[0], rtol=1e-12, atol=1e-12)
    else:
        dt = t[1] - t[0] ## already dimensional
    
    if hasattr(self,'duration'):
        t_meas = self.duration * self.tchar
        np.testing.assert_allclose(t_meas, t.max()-t.min(), rtol=1e-12, atol=1e-12)
    else:
        t_meas = t[-1] - t[0] ## already dimensional
        self.duration = t_meas / self.tchar ## non-dimensionalize for attribute
    
    zrange = z.max() - z.min()
    
    data['t'] = t
    data['dt'] = dt
    data['dz'] = dz0
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
    
    # ==============================================================
    # prepare buffers, maps, etc.
    # ==============================================================
    
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
        
        'u_tau'     : [ ( 'u_tau',                  ) ,  True, True, False ], ## uτ
        'utauI'     : [ (          ('u_tau',False), ) , False, True,  True ], ## uτ′
        'r_utauII'  : [ (   'rho', ('u_tau',True ), ) , False, True,  True ], ## ρ·uτ″
        
        'v_tau'     : [ ( 'v_tau',                  ) ,  True, True, False ], ## vτ
        'vtauI'     : [ (          ('v_tau',False), ) , False, True,  True ], ## vτ′
        'r_vtauII'  : [ (   'rho', ('v_tau',True ), ) , False, True,  True ], ## ρ·vτ″
        
        'w_tau'     : [ ( 'w_tau',                  ) ,  True, True, False ], ## wτ
        'wtauI'     : [ (          ('w_tau',False), ) , False, True,  True ], ## wτ′
        'r_wtauII'  : [ (   'rho', ('w_tau',True ), ) , False, True,  True ], ## ρ·wτ″
        
        'utauIutauI' : [ ( ('u_tau',False), ('u_tau',False) ), True, True, False ], ## uτ′uτ′
        'vtauIvtauI' : [ ( ('v_tau',False), ('v_tau',False) ), True, True, False ], ## vτ′vτ′
        'wtauIwtauI' : [ ( ('w_tau',False), ('w_tau',False) ), True, True, False ], ## wτ′wτ′
        #'utauIvtauI' : [ ( ('u_tau',False), ('v_tau',False) ), True, True, False ], ## uτ′vτ′
        #'utauIwtauI' : [ ( ('u_tau',False), ('w_tau',False) ), True, True, False ], ## uτ′wτ′
        
        'tau_uy'       : [ (  'tau_uy',                          ) ,  True, True, False ], ## τuy
        'tauuyI'       : [ ( ('tau_uy',False) ,                  ) , False, True,  True ], ## τ′uy
        'tauuyItauuyI' : [ ( ('tau_uy',False) , ('tau_uy',False) ) ,  True, True, False ], ## τ′uy·τ′uy
        
        'tau_vy'       : [ (  'tau_vy',                          ) ,  True, True, False ], ## τvy
        'tauvyI'       : [ ( ('tau_vy',False) ,                  ) , False, True,  True ], ## τ′vy
        'tauvyItauvyI' : [ ( ('tau_vy',False) , ('tau_vy',False) ) ,  True, True, False ], ## τ′vy·τ′vy
        
        'tau_wy'       : [ (  'tau_wy',                          ) ,  True, True, False ], ## τwy
        'tauwyI'       : [ ( ('tau_wy',False) ,                  ) , False, True,  True ], ## τ′wy
        'tauwyItauwyI' : [ ( ('tau_wy',False) , ('tau_wy',False) ) ,  True, True, False ], ## τ′wy·τ′wy
        
        'TITI'     : [ (        ('T',False), ('T',False) ) , True, True, False ], ## T′T′
        'TIITII'   : [ (        ('T',True ), ('T',True ) ) , True, True, False ], ## T″T″
        'r_TIITII' : [ ( 'rho', ('T',True ), ('T',True ) ) , True, True, False ], ## ρ·T″T″
        
        'rho'      : [ (  'rho',                       ) ,  True, True, False, ], ## ρ
        'rhoI'     : [ (                ('rho',False), ) , False, True,  True, ], ## ρ′
        'rhoIrhoI' : [ ( ('rho',False), ('rho',False), ) ,  True, True, False, ], ## ρ′ρ′
        
        'p'    : [ (  'p',                     ) ,  True, True, False, ], ## p
        'pI'   : [ (              ('p',False), ) , False, True,  True, ], ## p′
        'pIpI' : [ ( ('p',False), ('p',False), ) ,  True, True, False, ], ## p′p′
        
        'T'        : [ ( 'T',                ) ,  True, True, False, ], ## T
        'TI'       : [ (        ('T',False), ) , False, True,  True, ], ## T′
        'TII'      : [ (        ('T',True ), ) , False, True, False, ], ## T″
        'r_TII'    : [ ( 'rho', ('T',True ), ) , False, True,  True, ], ## ρ·T″
        
        }
    
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
    
    ## rank-local buffsres
    data_avg  = np.zeros(shape=(nir,),          dtype={'names':scalars_avg, 'formats':[ np.float64 for sss in scalars_avg ]})
    data_bins = np.zeros(shape=(nir,n_bins+1),  dtype={'names':scalars_pdf, 'formats':[ np.float64 for sss in scalars_pdf ]})
    data_pdf  = np.zeros(shape=(nir,n_bins),    dtype={'names':scalars_pdf, 'formats':[ np.float64 for sss in scalars_pdf ]})
    data_hos  = np.zeros(shape=(nir,),          dtype={'names':scalars_hos, 'formats':[ np.float64 for sss in scalars_hos ]})
    
    # ==============================================================
    # main loop
    # ==============================================================
    
    if verbose:
        progress_bar = tqdm(
            total=len(scalars_dict)*nir,
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
    
    for s,ss in scalars_dict.items(): ## e.g. where s='r_uIIvII' & ss=[ ( 'rho', ('u',True ), ('v',True ) ), True,True,False ]
        
        if verbose: tqdm.write(72*'-')
        
        recipe, do_mean, do_pdf, do_skew_kurt = ss
        
        if verbose:
            tqdm.write(even_print('computing',s,s=True,))
        
        ## should ρ be read?
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
        
        ## [x] loop (rank-local)
        for ii in range(ri1,ri2):
            
            iii = ii - ri1
            
            ## read ρ
            if read_rho:
                
                dset = self['data/rho']
                self.comm.Barrier()
                t_start = timeit.default_timer()
                if self.usingmpi:
                    with dset.collective:
                        rho = np.copy( dset[ii,:,:] )
                else:
                    rho = np.copy( dset[ii,:,:] )
                self.comm.Barrier()
                t_delta = timeit.default_timer() - t_start
                data_gb = self.n_ranks * 1 * self.nj * self.nt * dset.dtype.itemsize / 1024**3
                if verbose:
                    tqdm.write(even_print('read: ρ', '%0.3f [GB]  %0.3f [s]  %0.3f [GB/s]'%(data_gb,t_delta,(data_gb/t_delta)), s=True))
                
                rho = rho.astype(np.float64) ## cast to double
                
                ## re-dimensionalize
                rho *= self.rho_inf
                
                if ( rho.shape != (nj,nt) ):
                    raise ValueError
                    print(f'rank {self.rank:d}: shape violation')
                    self.comm.Abort(1)
                
                ## ρ mean in [t] --> leave (j,1)
                rho_avg = np.mean(rho, axis=-1, dtype=np.float64, keepdims=True)
            
            else:
                rho     = None ; del rho
                rho_avg = None ; del rho_avg
            
            ## product buffer for multiplication --> !!! notices ones() here and not zeros() !!!
            #data_accum = np.ones(shape=(ni,nj,nt), dtype=np.float64) ## chunk range context
            data_accum = np.ones(shape=(nj,nt), dtype=np.float64) ## chunk range context
            
            ## read unsteady scalar data, remove mean, <density weight>, multiply
            for sss in recipe:
                
                if isinstance(sss, str) and (sss=='rho'): ## ρ
                    
                    ## multiply product accumulator, ρ was already read and is already dimensional
                    data_accum *= rho
                
                elif isinstance(sss, str) and (sss!='rho'): ## scalar which will NOT be mean-removed
                    
                    ## read
                    dset = self[f'data/{sss}']
                    self.comm.Barrier()
                    t_start = timeit.default_timer()
                    if self.usingmpi:
                        with dset.collective:
                            data_X = np.copy( dset[ii,:,:] )
                    else:
                        data_X = np.copy( dset[ii,:,:] )
                    self.comm.Barrier()
                    t_delta = timeit.default_timer() - t_start
                    data_gb = self.n_ranks * 1 * self.nj * self.nt * dset.dtype.itemsize / 1024**3
                    if verbose:
                        tqdm.write(even_print(f'read: {sss}', '%0.3f [GB]  %0.3f [s]  %0.3f [GB/s]'%(data_gb,t_delta,(data_gb/t_delta)), s=True))
                    
                    data_X = data_X.astype(np.float64) ## cast to double
                    
                    if ( data_X.shape != (nj,nt) ):
                        raise ValueError
                        print(f'rank {self.rank:d}: shape violation')
                        self.comm.Abort(1)
                    
                    ## redimensionalize
                    if sss in ['tau_uy','tau_vy','tau_wy']:
                        data_X *= self.rho_inf * self.U_inf**2
                    elif sss in ['u_tau','v_tau','w_tau']:
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
                    
                    ## read
                    dset = self[f'data/{sn}']
                    self.comm.Barrier()
                    t_start = timeit.default_timer()
                    if self.usingmpi:
                        with dset.collective:
                            data_X = np.copy( dset[ii,:,:] )
                    else:
                        data_X = np.copy( dset[ii,:,:] )
                    self.comm.Barrier()
                    t_delta = timeit.default_timer() - t_start
                    data_gb = self.n_ranks * 1 * self.nj * self.nt * dset.dtype.itemsize / 1024**3
                    if verbose:
                        tqdm.write(even_print(f'read: {sn}', '%0.3f [GB]  %0.3f [s]  %0.3f [GB/s]'%(data_gb,t_delta,(data_gb/t_delta)), s=True))
                    
                    data_X = data_X.astype(np.float64) ## cast to double
                    
                    ## redimensionalize
                    if sn in ['tau_uy','tau_vy','tau_wy']:
                        data_X *= self.rho_inf * self.U_inf**2
                    elif sn in ['u_tau','v_tau','w_tau']:
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
                        data_X_mean = np.mean( rho*data_X , axis=-1, dtype=np.float64, keepdims=True) ## (nz,1)
                        data_X_mean /= rho_avg
                    else:
                        data_X_mean = np.mean( data_X , axis=-1, dtype=np.float64, keepdims=True) ## (nz,1)
                    
                    ## Reynolds prime □′ or Favre prime □″
                    data_X -= data_X_mean
                    
                    ## assert avg(□′)==0 or avg(ρ·□″)==0
                    if do_density_weighting:
                        a_ = np.mean(rho*data_X, axis=-1, dtype=np.float64, keepdims=True)
                    else:
                        a_ = np.mean(data_X, axis=-1, dtype=np.float64, keepdims=True)
                    if not np.allclose( a_, np.zeros_like(a_), atol=1e-3 ):
                        print(f'rank {self.rank:d}: avg(□′)!=0 or avg(ρ·□″)!=0')
                        self.comm.Abort(1)
                    
                    ## MULTIPLY product accumulator by □′ | □″
                    data_accum *= data_X
                
                else:
                    raise ValueError
            
            # ===============================================================================
            # At this point you have the UNSTEADY 2D [j,t] data according to 'recipe'
            # ===============================================================================
            
            #xiA = cx1 - rx1
            #xiB = cx2 - rx1
            
            self.comm.Barrier()
            t_start = timeit.default_timer()
            
            ## mean in [t] --> leave [j,1]
            d_mean = np.mean( data_accum, axis=-1, keepdims=True, dtype=np.float64)
            #if ( d_mean.shape != (ni,nj,1,) ):
            if ( d_mean.shape != (nj,1) ):
                raise ValueError
                print(f'rank {self.rank:d}: shape violation')
                self.comm.Abort(1)
            
            if do_mean: ## mean in [j] --> leave float
                data_avg[s][iii] = np.mean( d_mean, axis=(0,1), dtype=np.float64)
            
            if do_pdf:
                
                d_ = np.copy( data_accum.ravel() )
                if ( d_.shape != (nj*nt,) ):
                    raise ValueError
                    print(f'rank {self.rank:d}: shape violation')
                    self.comm.Abort(1)
                pdf_ , bin_edges_ = np.histogram( d_ , bins=n_bins , density=True )
                data_bins[s][iii,:] = bin_edges_
                data_pdf[s][iii,:]  = pdf_
            
            if do_skew_kurt:
                
                d_ = np.copy( data_accum.ravel() ) ## □′ or □″, although mean ==0 is not checked
                if ( d_.shape != (nj*nt,) ):
                    raise ValueError
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
                
                d_std = np.sqrt( np.mean( d_**2 , dtype=np.float64 ) )
                
                if np.isclose(d_std, 0., atol=1e-08):
                    d_skew = 0.
                    d_kurt = 0.
                else:
                    d_skew = np.mean( d_**3 , dtype=np.float64 ) / d_std**3
                    d_kurt = np.mean( d_**4 , dtype=np.float64 ) / d_std**4
                
                data_hos[f'{s}_skew'][iii] = d_skew
                data_hos[f'{s}_kurt'][iii] = d_kurt
            
            self.comm.Barrier() ## [x] loop ('ii' within this rank's range)
            if verbose: progress_bar.update()
    
    self.comm.Barrier()
    if verbose:
        progress_bar.close()
        print(72*'-')
    
    # ==============================================================
    # write HDF5 (.h5) file
    # ==============================================================
    
    ## open on rank 0 and write attributes, dimensions, etc.
    if (self.rank==0):
        with h5py.File(fn_h5_stats, 'w') as hfw:
            
            ## write floats,ints as top-level attributes
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
            
            ## write numpy arrays
            hfw.create_dataset( 'dims/x' , data=x ) ## [m]
            hfw.create_dataset( 'dims/z' , data=z ) ## [m]
            hfw.create_dataset( 'dims/t' , data=t ) ## [s]
            
            ## initialize datasets
            for scalar in scalars_avg:
                hfw.create_dataset( f'avg/{scalar}', shape=(nx,), dtype=np.float64, chunks=(1,) )
            for scalar in scalars_pdf:
                hfw.create_dataset( f'bins/{scalar}', shape=(nx,n_bins+1), dtype=np.float64, chunks=(1,n_bins+1) )
            for scalar in scalars_pdf:
                hfw.create_dataset( f'pdf/{scalar}', shape=(nx,n_bins), dtype=np.float64, chunks=(1,n_bins) )
            for scalar in scalars_hos:
                hfw.create_dataset( f'hos/{scalar}', shape=(nx,), dtype=np.float64, chunks=(1,) )
    
    self.comm.Barrier()
    time.sleep(2.)
    self.comm.Barrier()
    
    with h5py.File(fn_h5_stats, 'a', driver='mpio', comm=self.comm) as hfw:
        
        # === collectively write data
        
        for scalar in scalars_avg:
            dset = hfw[f'avg/{scalar}']
            with dset.collective:
                dset[ri1:ri2] = data_avg[scalar][:]
            self.comm.Barrier()
        
        for scalar in scalars_pdf:
            dset = hfw[f'bins/{scalar}']
            with dset.collective:
                dset[ri1:ri2,:] = data_bins[scalar][:,:]
            self.comm.Barrier()
        
        for scalar in scalars_pdf:
            dset = hfw[f'pdf/{scalar}']
            with dset.collective:
                dset[ri1:ri2,:] = data_pdf[scalar][:,:]
            self.comm.Barrier()
        
        for scalar in scalars_hos:
            dset = hfw[f'hos/{scalar}']
            with dset.collective:
                dset[ri1:ri2] = data_hos[scalar][:]
            self.comm.Barrier()
    
    ## report file size
    if verbose:
        even_print( os.path.basename(fn_h5_stats), f'{(os.path.getsize(fn_h5_stats)/1024**2):0.2f} [MB]' )
        print(72*'-')
    
    ## report file contents
    self.comm.Barrier()
    if (self.rank==0):
        with h5py.File(fn_h5_stats,'r') as hfr:
            h5_print_contents(hfr)
    self.comm.Barrier()
    
    if verbose: print(72*'-')
    if verbose: print('total time : spd.calc_statistics_wall() : %s'%format_time_string((timeit.default_timer() - t_start_func)))
    if verbose: print(72*'-')
    return
    