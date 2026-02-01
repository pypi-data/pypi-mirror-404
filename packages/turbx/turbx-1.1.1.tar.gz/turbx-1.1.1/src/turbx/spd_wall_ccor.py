import os
import sys
import timeit
from pathlib import Path, PurePosixPath

import h5py
import numpy as np
import scipy as sp
from tqdm import tqdm

from .h5 import h5_print_contents
from .signal import ccor, get_overlapping_window_size, get_overlapping_windows
from .utils import even_print, format_time_string

# ======================================================================

def _calc_ccor_wall(self, **kwargs):
    '''
    Calculate cross-correlation [z,t] at every [x]
    - designed for analyzing unsteady, pre-computed wall quantities ([y] plane)
    '''
    
    if (self.rank==0):
        verbose = True
    else:
        verbose = False
    
    if verbose: print('\n'+'spd.calc_ccor_wall()'+'\n'+72*'-')
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
    
    fn_h5_out       = kwargs.get('fn_h5_out',None)       ## filename for output HDF5 (.h5) file
    overlap_fac_nom = kwargs.get('overlap_fac_nom',0.50) ## nominal windows overlap factor
    n_win           = kwargs.get('n_win',8)              ## number of segment windows for [t] ccor calc
    
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
    
    ## distribute data over [i]/[x]
    ril_ = np.array_split(np.arange(self.ni,dtype=np.int64),min(ri,self.ni))
    ril = [[b[0],b[-1]+1] for b in ril_ ]
    ri1,ri2 = ril[self.rank]
    nir = ri2 - ri1
    
    ## output filename : HDF5 (.h5)
    if (fn_h5_out is None): ## automatically determine name
        fname_path = os.path.dirname(self.fname)
        fname_base = os.path.basename(self.fname)
        fname_root, fname_ext = os.path.splitext(fname_base)
        #fname_root = re.findall(r'io\S+_mpi_[0-9]+', fname_root)[0]
        fn_h5_out_base = fname_root+'_ccor.h5'
        fn_h5_out = str(PurePosixPath(fname_path, fn_h5_out_base))
    if (Path(fn_h5_out).suffix != '.h5'):
        raise ValueError(f"fn_h5_out='{str(fn_h5_out)}' must end in .h5")
    if os.path.isfile(fn_h5_out):
        if (fn_h5_out == self.fname):
            raise ValueError(f"fn_h5_out='{str(fn_h5_out)}' cannot be same as input filename.")
    
    if verbose: even_print( 'fn_h5'     , self.fname )
    if verbose: even_print( 'fn_h5_out' , fn_h5_out  )
    if verbose: print(72*'-')
    self.comm.Barrier()
    
    # ===
    
    ## the data dictionary to be written to .h5 later
    data = {}
    
    ## freestream data
    #lchar   = self.lchar   ; data['lchar']   = self.lchar
    U_inf   = self.U_inf   ; data['U_inf']   = self.U_inf
    rho_inf = self.rho_inf ; data['rho_inf'] = self.rho_inf
    T_inf   = self.T_inf   ; data['T_inf']   = self.T_inf
    #mu_inf  = self.mu_inf  ; data['mu_inf']  = self.mu_inf
    data['p_inf'] = self.p_inf
    data['Ma']    = self.Ma
    data['Pr']    = self.Pr
    
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
        print(72*'-')
    
    win_len, overlap       = get_overlapping_window_size(nt, n_win, overlap_fac_nom)
    overlap_fac            = overlap / win_len
    tw, n_win, n_pad       = get_overlapping_windows(t, win_len, overlap)
    t_meas_per_win         = (win_len-1)*dt
    data['win_len']        = win_len
    data['overlap_fac']    = overlap_fac
    data['overlap']        = overlap
    data['n_win']          = n_win
    data['t_meas_per_win'] = t_meas_per_win
    
    if verbose:
        even_print('overlap_fac (nominal)' , f'{overlap_fac_nom:0.5f}'  )
        even_print('n_win'                 , f'{n_win:d}'               )
        even_print('win_len'               , f'{win_len:d}'             )
        even_print('overlap'               , f'{overlap:d}'             )
        even_print('overlap_fac'           , f'{overlap_fac:0.5f}'      )
        even_print('n_pad'                 , f'{n_pad:d}'               )
        #even_print('t_win/(δ99/uτ)'        , '%0.3f [-]'%t_eddy_per_win )
        print(72*'-')
    
    ## get lags [t]
    #lags_t,_  = ccor( np.ones(nt,dtype=np.float32), np.ones(nt,dtype=np.float32), get_lags=True )
    lags_t,_  = ccor( np.ones(win_len,dtype=np.float32), np.ones(win_len,dtype=np.float32), get_lags=True )
    #n_lags_t_ = nt*2-1
    n_lags_t_ = win_len*2-1
    n_lags_t  = lags_t.shape[0]
    if (n_lags_t!=n_lags_t_):
        raise AssertionError('check lags [t]')
    
    data['lags_t']   = lags_t
    data['n_lags_t'] = n_lags_t
    
    if verbose:
        even_print('n lags (Δt)' , '%i'%(n_lags_t,))
    
    ## get lags [z]
    lags_z,_  = ccor( np.ones(nz,dtype=np.float32) , np.ones(nz,dtype=np.float32), get_lags=True )
    n_lags_z_ = nz*2-1
    n_lags_z  = lags_z.shape[0]
    if (n_lags_z!=n_lags_z_):
        raise AssertionError('check lags [z]')
    
    data['lags_z']   = lags_z
    data['n_lags_z'] = n_lags_z
    
    if verbose:
        even_print('n lags (Δz)' , '%i'%(n_lags_z,))
    
    # ==============================================================
    # prepare buffers, etc.
    # ==============================================================
    
    do_density_weighting = False ## deactivated for now... would need implementation
    
    ## cross-correlation pairs
    ## [ str:var1, str:var2 ]
    ccor_combis = [
    
    [ 'u_tau' , 'u_tau' ], ## [ uτ , uτ ] --> ccor[ uτ′ , uτ′ ]
    [ 'v_tau' , 'v_tau' ], ## [ vτ , vτ ] --> ccor[ vτ′ , vτ′ ]
    [ 'w_tau' , 'w_tau' ], ## [ wτ , wτ ] --> ccor[ wτ′ , wτ′ ]
    
    #[ 'u_tau' , 'v_tau' ], ## [ uτ , vτ ] --> ccor[ uτ′ , vτ′ ]
    #[ 'u_tau' , 'w_tau' ], ## [ uτ , wτ ] --> ccor[ uτ′ , wτ′ ]
    #[ 'v_tau' , 'w_tau' ], ## [ vτ , wτ ] --> ccor[ vτ′ , wτ′ ]
    
    [ 'tau_uy' , 'tau_uy' ], ## [ τuy , τuy ] --> ccor[ τuy′ , τuy′ ]
    [ 'tau_vy' , 'tau_vy' ], ## [ τvy , τvy ] --> ccor[ τvy′ , τvy′ ]
    [ 'tau_wy' , 'tau_wy' ], ## [ τwy , τwy ] --> ccor[ τwy′ , τwy′ ]
    
    #[ 'tau_uy' , 'tau_vy' ], ## [ τuy , τvy ] --> ccor[ τuy′ , τvy′ ]
    #[ 'tau_uy' , 'tau_wy' ], ## [ τuy , τwy ] --> ccor[ τuy′ , τwy′ ]
    #[ 'tau_vy' , 'tau_wy' ], ## [ τvy , τwy ] --> ccor[ τvy′ , τwy′ ]
    
    [ 'p'   , 'p'   ], ## [p,p] --> ccor[ p′ , p′ ]
    [ 'T'   , 'T'   ], ## [T,T] --> ccor[ T′ , T′ ]
    [ 'rho' , 'rho' ], ## [ρ,ρ] --> ccor[ ρ′ , ρ′ ]
    
    [ 'u_tau'  , 'p' ], ## [uτ,p] --> ccor[ uτ′  , p′ ]
    [ 'tau_uy' , 'p' ], ## [τuy,p] --> ccor[ τuy′ , p′ ]
    
    ]
    
    ## generate cross-correlation scalar names
    scalars = []
    for ccor_combi in ccor_combis:
        #s1,s2,do_density_weighting = ccor_combi
        s1,s2 = ccor_combi
        if do_density_weighting:
            raise NotImplementedError
        else:
            scalars.append(f"{s1.replace('_','')}I_{s2.replace('_','')}I")
    
    scalars_dtypes = [ np.dtype(np.float64) for s in scalars ]
    
    ## generate AVG scalar names
    scalars_Re_avg = []
    #scalars_Fv_avg = []
    for ccor_combi in ccor_combis:
        #s1,s2,do_density_weighting = ccor_combi
        s1,s2 = ccor_combi
        if do_density_weighting and ('rho' not in scalars_Re_avg):
            scalars_Re_avg.append('rho')
        if do_density_weighting:
            #if (s1 not in scalars_Fv_avg):
            #    scalars_Fv_avg.append(s1)
            #if (s2 not in scalars_Fv_avg):
            #    scalars_Fv_avg.append(s2)
            raise NotImplementedError
        else:
            if (s1 not in scalars_Re_avg):
                scalars_Re_avg.append(s1)
            if (s2 not in scalars_Re_avg):
                scalars_Re_avg.append(s2)
    
    ## numpy formatted arrays: buffers for PSD & other data (rank-local)
    Rz         = np.zeros(shape=(nir, n_lags_z ) , dtype={'names':scalars, 'formats':scalars_dtypes})
    Rt         = np.zeros(shape=(nir, n_lags_t ) , dtype={'names':scalars, 'formats':scalars_dtypes})
    covariance = np.zeros(shape=(nir,          ) , dtype={'names':scalars, 'formats':scalars_dtypes})
    avg_Re     = np.zeros(shape=(nir,          ) , dtype={'names':scalars_Re_avg, 'formats':[ np.dtype(np.float64) for s in scalars_Re_avg ]})
    #avg_Fv     = np.zeros(shape=(nir,          ) , dtype={'names':scalars_Fv_avg, 'formats':[ np.dtype(np.float64) for s in scalars_Fv_avg ]})
    
    if verbose:
        even_print('n cross-correlation scalar combinations' , '%i'%(len(ccor_combis),))
        print(72*'-')
    
    ## window for [z] -- rectangular because [z] is assumed periodic already
    window_z       = np.ones(nz,dtype=np.float64)
    mean_sq_win_z  = np.mean(window_z**2)
    if verbose:
        even_print('mean(window_z**2)', '%0.5f'%(mean_sq_win_z,))
    
    ## window function for [t]
    window_type = None
    if (window_type=='tukey'):
        window_t = sp.signal.windows.tukey(win_len,alpha=0.5,sym=False) ## α=0:rectangular, α=1:Hann
    elif (window_type=='hann'):
        window_t = sp.signal.windows.hann(win_len,sym=False)
    elif (window_type is None):
        window_t = np.ones(win_len, dtype=np.float64)
    else:
        raise ValueError
    
    if verbose:
        even_print('window type [t]', '\'%s\''%str(window_type))
    
    ## Not needed for normalization for cross-correlation
    ##   ... but report anyway
    mean_sq_win_t = np.mean(window_t**2)
    if verbose:
        even_print('mean(window_t**2)', '%0.5f'%(mean_sq_win_t,))
    
    # ==============================================================
    # Main loop
    # ==============================================================
    
    if verbose:
        progress_bar = tqdm(
            total=len(ccor_combis)*nir,
            ncols=100,
            desc='ccor',
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
        
        scalar_L, scalar_R = cc
        
        msg = f'ccor[{scalar_L}′,{scalar_R}′]'
        if verbose:
            tqdm.write(even_print('computing',msg,s=True,))
        
        dset_L = self[f'data/{scalar_L}']
        dset_R = self[f'data/{scalar_R}']
        data_gb_1x = self.n_ranks * 1 * self.nj * self.nt * dset_L.dtype.itemsize / 1024**3
        
        scalar = scalars[cci]
        
        ## assert scalar name
        scalar_ = f"{scalar_L.replace('_','')}I_{scalar_R.replace('_','')}I"
        if (scalar != scalar_):
            raise ValueError
        
        ## assert scalar name
        if do_density_weighting:
            #if (f'r{scalar_L}II_r{scalar_R}II' != scalar ):
            #    raise ValueError
            raise NotImplementedError
        else:
            if (f"{scalar_L.replace('_','')}I_{scalar_R.replace('_','')}I" != scalar ):
                raise ValueError
        
        ## [x] loop --> each rank works on part of global [x]/[i] range
        for ii in range(ri1,ri2):
            
            iii = ii - ri1 ## [x] index local
            
            data_L = np.zeros( (nz,nt) , dtype=np.float64 )
            data_R = np.zeros( (nz,nt) , dtype=np.float64 )
            
            self.comm.Barrier()
            t_start = timeit.default_timer()
            
            ## read data L
            n_scalars_read = 1 ## initialize
            scalar_str = scalar_L ## initialize
            with dset_L.collective:
                data_L[:,:] = np.copy( dset_L[ii,:,:] ).astype(np.float64)
            self.comm.Barrier()
            
            ## read data R (if != data L)
            if (scalar_L==scalar_R):
                data_R[:,:] = np.copy( data_L )
            else:
                n_scalars_read += 1
                scalar_str += f',{scalar_R}'
                with dset_R.collective:
                    data_R[:,:] = np.copy( dset_R[ii,:,:] ).astype(np.float64)
                self.comm.Barrier()
            
            self.comm.Barrier()
            t_delta = timeit.default_timer() - t_start
            data_gb = data_gb_1x * n_scalars_read
            
            if verbose:
                tqdm.write(even_print(f'read: {scalar_str}', f'{data_gb:0.3f} [GB]  {t_delta:0.3f} [s]  {data_gb/t_delta:0.3f} [GB/s]', s=True))
            
            ## data_L and data_R shape should be (nz,nt)
            if ( data_L.shape != (nz,nt) ) or ( data_R.shape != (nz,nt) ):
                print(f'rank {self.rank:d}: shape violation')
                self.comm.Abort(1)
            
            # === redimensionalize
            
            if scalar_L in ['tau_uy','tau_vy','tau_wy',]:
                data_L *= rho_inf * U_inf**2
            elif scalar_L in ['u_tau','v_tau','w_tau',]:
                data_L *= U_inf
            elif scalar_L in ['p',]:
                data_L *= rho_inf * U_inf**2
            elif scalar_L in ['T',]:
                data_L *= T_inf
            elif scalar_L in ['rho',]:
                data_L *= rho_inf
            else:
                raise ValueError
            
            if scalar_R in ['tau_uy','tau_vy','tau_wy',]:
                data_R *= rho_inf * U_inf**2
            elif scalar_R in ['u_tau','v_tau','w_tau',]:
                data_R *= U_inf
            elif scalar_R in ['p',]:
                data_R *= rho_inf * U_inf**2
            elif scalar_R in ['T',]:
                data_R *= T_inf
            elif scalar_R in ['rho',]:
                data_R *= rho_inf
            else:
                raise ValueError
            
            ## data_L and data_R shape should be (nz,nt)
            if ( data_L.shape != (nz,nt) ) or ( data_R.shape != (nz,nt) ):
                print(f'rank {self.rank:d}: shape violation')
                self.comm.Abort(1)
            
            # === compute mean-removed data
            
            ## avg(□) or avg(ρ·□)/avg(ρ) in [t]
            if do_density_weighting:
                #rho_avg     = np.mean(        rho , axis=-1, dtype=np.float64, keepdims=True)
                #data_L_avg  = np.mean( rho*data_L , axis=-1, dtype=np.float64, keepdims=True)
                #data_L_avg /= rho_avg
                #data_R_avg  = np.mean( rho*data_R , axis=-1, dtype=np.float64, keepdims=True)
                #data_R_avg /= rho_avg
                raise NotImplementedError
            else:
                data_L_avg = np.mean( data_L , axis=-1, dtype=np.float64, keepdims=True) ## (nz,1)
                data_R_avg = np.mean( data_R , axis=-1, dtype=np.float64, keepdims=True) ## (nz,1)
            
            ## data_L_avg and data_R_avg shape should be (nz,1)
            if ( data_L_avg.shape != (nz,1) ) or ( data_R_avg.shape != (nz,1) ):
                print(f'rank {self.rank:d}: shape violation')
                self.comm.Abort(1)
            
            ## Reynolds prime □′ or Favre prime □″ --> shape (nz,nt)
            data_L -= data_L_avg
            data_R -= data_R_avg
            
            ## data_L and data_R shape should be (nz,nt)
            if ( data_L.shape != (nz,nt) ) or ( data_R.shape != (nz,nt) ):
                print(f'rank {self.rank:d}: shape violation')
                self.comm.Abort(1)
            
            ## assert stationarity / definition averaging
            ## avg(□′)==0 or avg(ρ·□″)==0
            if do_density_weighting:
                #a_ = np.mean(rho*data_L, axis=-1, dtype=np.float64, keepdims=True)
                #b_ = np.mean(rho*data_R, axis=-1, dtype=np.float64, keepdims=True)
                raise NotImplementedError
            else:
                a_ = np.mean(data_L, axis=-1, dtype=np.float64, keepdims=True) ## average in [t] --> (nz,1)
                b_ = np.mean(data_R, axis=-1, dtype=np.float64, keepdims=True)
            if not np.allclose( a_, np.zeros_like(a_), atol=1e-6 ) or not np.allclose( b_, np.zeros_like(b_), atol=1e-6 ):
                print(f'rank {self.rank:d}: avg(□′)!=0 or avg(ρ·□″)!=0')
                self.comm.Abort(1)
            
            ## covariance: <□′□′>
            if do_density_weighting:
                #covariance_ = np.mean( rho*data_L * rho*data_R , axis=-1 , dtype=np.float64, keepdims=True)
                raise NotImplementedError
            else:
                covariance_ = np.mean( data_L*data_R , axis=-1 , dtype=np.float64, keepdims=True) ## average in [t] --> (nz,1)
            
            if ( covariance_.shape != (nz,1) ):
                print(f'rank {self.rank:d}: shape violation')
                self.comm.Abort(1)
            
            ## write this chunk/scalar's covariance to covariance buffer
            ## avg over [z,t] --> np.float64()
            covariance[scalar][iii] = np.mean( covariance_ , axis=(0,1) , dtype=np.float64)
            
            ## write (rank-local) 1D [x] average
            if do_density_weighting:
                #avg_Fv[scalar_L][iii] = np.mean( data_L_avg , axis=(0,1) , dtype=np.float64) )
                #avg_Fv[scalar_R][iii] = np.mean( data_R_avg , axis=(0,1) , dtype=np.float64) )
                #avg_Re['rho'][iii]    = np.mean( rho_avg    , axis=(0,1) , dtype=np.float64) )
                raise ValueError
            else:
                avg_Re[scalar_L][iii] = np.mean( data_L_avg , axis=(0,1) , dtype=np.float64)
                avg_Re[scalar_R][iii] = np.mean( data_R_avg , axis=(0,1) , dtype=np.float64)
            
            # ===============================================================================
            # At this point you have 4D [x,y,z,t] □′ data
            # ===============================================================================
            
            
            ## do [z] cross-correlation for every [t]
            Rz_buf = np.zeros((nt,n_lags_z), dtype=np.float64)
            for ti in range(nt):
                uL = np.copy( data_L[:,ti] )
                uR = np.copy( data_R[:,ti] )
                Rz_buf[ti,:] = ccor(uL,uR)
            
            Rz[scalar][iii,:] = np.mean(Rz_buf, axis=0, dtype=np.float64) ## mean across [t] --> (n_lags_z,)
            
            
            ## ## do [t] cross-correlation for every [z]
            ## Rt_buf = np.zeros((nz,n_lags_t), dtype=np.float64)
            ## for zi in range(nz):
            ##     uL = np.copy( data_L[zi,:] )
            ##     uR = np.copy( data_R[zi,:] )
            ##     Rt_buf[zi,:] = ccor(uL,uR)
            ## 
            ## Rt[scalar][iii,:] = np.mean(Rt_buf, axis=0, dtype=np.float64) ## mean across [z] --> (n_lags_t,)
            
            
            ## do [t] cross-correlation for every [z]
            Rt_buf = np.zeros((nz,n_lags_t), dtype=np.float64)
            for zi in range(nz):
                uL = np.copy( data_L[zi,:] )
                uR = np.copy( data_R[zi,:] )
                #Rt_buf[zi,:] = ccor(uL,uR)
                
                uL_, nw, n_pad = get_overlapping_windows(uL, win_len, overlap)
                uR_, nw, n_pad = get_overlapping_windows(uR, win_len, overlap)
                
                ## Per-segment buffer
                Rt_buf_win = np.zeros((nw,n_lags_t), dtype=np.float64)
                for wi in range(nw):
                    A1 = np.copy( uL_[wi,:] * window_t ) 
                    A2 = np.copy( uR_[wi,:] * window_t )
                    Rt_buf_win[wi,:] = ccor(A1,A2)
                Rt_buf[zi,:] = np.mean(Rt_buf_win, axis=0, dtype=np.float64) ## mean across windows --> (n_lags_t,)
            
            Rt[scalar][iii,:] = np.mean(Rt_buf, axis=0, dtype=np.float64) ## mean across [z] --> (n_lags_t,)
            
            
            self.comm.Barrier() ## [x] loop ('ii' within this rank's range)
            if verbose: progress_bar.update()
            
            #break ## DEBUG
        #break ## DEBUG
    
    self.comm.Barrier()
    if verbose:
        progress_bar.close()
        print(72*'-')
    
    # ==============================================================
    # Write HDF5 (.h5) file
    # ==============================================================
    
    ## Overwrite outfile!
    ## - first, open on rank 0 and to write attributes and initialize datasets
    if (self.rank==0):
        with h5py.File(fn_h5_out, 'w') as hfw:
            
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
            hfw.create_dataset( 'dims/x'      , data=x      ) ## [m]
            hfw.create_dataset( 'dims/z'      , data=z      ) ## [m]
            hfw.create_dataset( 'dims/t'      , data=t      ) ## [s]
            hfw.create_dataset( 'dims/lags_z' , data=lags_z )
            hfw.create_dataset( 'dims/lags_t' , data=lags_t )
            
            ## initialize datasets : covariance,Rz,Rt
            for scalar in scalars:
                hfw.create_dataset( f'covariance/{scalar}' , shape=(nx,)          , dtype=np.float64 , chunks=None         , data=np.full((nx,),0.,np.float64)         )
                hfw.create_dataset( f'Rz/{scalar}'         , shape=(nx,n_lags_z)  , dtype=np.float64 , chunks=(1,n_lags_z) , data=np.full((nx,n_lags_z),0.,np.float64) )
                hfw.create_dataset( f'Rt/{scalar}'         , shape=(nx,n_lags_t)  , dtype=np.float64 , chunks=(1,n_lags_t) , data=np.full((nx,n_lags_t),0.,np.float64) )
            
            ## initialize datasets : 1D [x] mean
            for scalar in avg_Re.dtype.names:
                hfw.create_dataset( f'avg/Re/{scalar}', shape=(nx,), dtype=np.float64, chunks=None, data=np.full((nx,),0.,np.float64) )
    
    self.comm.Barrier()
    
    ## re-open in parallel for data writes
    with h5py.File(fn_h5_out, 'a', driver='mpio', comm=self.comm) as hfw:
        
        ## collectively write covariance,Rz,Rt
        for scalar in scalars:
            dset = hfw[f'covariance/{scalar}']
            with dset.collective:
                dset[ri1:ri2] = covariance[scalar][:]
            dset = hfw[f'Rz/{scalar}']
            with dset.collective:
                dset[ri1:ri2,:] = Rz[scalar][:,:]
            dset = hfw[f'Rt/{scalar}']
            with dset.collective:
                dset[ri1:ri2,:] = Rt[scalar][:,:]
        
        ## collectively write 1D [z] avgs
        for scalar in avg_Re.dtype.names:
            dset = hfw[f'avg/Re/{scalar}']
            with dset.collective:
                dset[ri1:ri2] = avg_Re[scalar][:]
    
    ## report file contents
    self.comm.Barrier()
    if (self.rank==0):
        even_print( os.path.basename(fn_h5_out) , f'{(os.path.getsize(fn_h5_out)/1024**2):0.1f} [MB]' )
        print(72*'-')
        with h5py.File(fn_h5_out,'r') as hfr:
            h5_print_contents(hfr)
    self.comm.Barrier()
    
    if verbose: print(72*'-')
    if verbose: print('total time : spd.calc_ccor_wall() : %s'%format_time_string((timeit.default_timer() - t_start_func)))
    if verbose: print(72*'-')
    return
