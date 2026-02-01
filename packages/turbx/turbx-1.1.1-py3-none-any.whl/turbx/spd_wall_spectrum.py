import os
import sys
import timeit
from pathlib import Path, PurePosixPath

import h5py
import numpy as np
import scipy as sp
from scipy.signal import csd
from tqdm import tqdm

from .h5 import h5_print_contents
from .utils import even_print, format_time_string

# ======================================================================

def _calc_turb_cospectrum_wall(self, **kwargs):
    '''
    Calculate FFT cospectrum in [z,t] at every [x]
    - designed for analyzing unsteady, pre-computed wall quantities ([y] plane)
    '''
    
    if (self.rank==0):
        verbose = True
    else:
        verbose = False
    
    if verbose: print('\n'+'spd.calc_turb_cospectrum_wall()'+'\n'+72*'-')
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
    n_win           = kwargs.get('n_win',8)              ## number of segment windows for [t] PSD calc
    
    ## check data distribution (only distribute data in [i]/[x])
    if (rj!=1):
        raise AssertionError('rj!=1')
    if (rt!=1):
        raise AssertionError('rt!=1')
    
    if not isinstance(ri,int) or (ri<1):
        raise ValueError('ri should be a positive non-zero int')
    
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
        fn_h5_out_base = fname_root+'_fft.h5'
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
    
    ## infile
    fsize = os.path.getsize(self.fname)/1024**3
    if verbose: even_print(os.path.basename(self.fname),'%0.1f [GB]'%fsize)
    if verbose: even_print('ni',f'{self.ni:d}')
    if verbose: even_print('nj',f'{self.nj:d}')
    if verbose: even_print('nt',f'{self.nt:d}')
    if verbose: even_print('n_pts',f'{self.n_pts/1e6:0.1f} [M]')
    if verbose: even_print('n_ranks',f'{self.n_ranks:d}')
    if verbose: print(72*'-')
    
    ## 0D freestream scalars
    #lchar   = self.lchar   ; data['lchar']   = self.lchar
    U_inf   = self.U_inf   ; data['U_inf']   = self.U_inf
    rho_inf = self.rho_inf ; data['rho_inf'] = self.rho_inf
    T_inf   = self.T_inf   ; data['T_inf']   = self.T_inf
    #mu_inf  = self.mu_inf  ; data['mu_inf']  = self.mu_inf
    data['p_inf'] = self.p_inf
    #data['M_inf'] = self.M_inf
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
    
    ## establish [t] windowing & get frequency
    nperseg     = nt // n_win
    noverlap    = int(round(nperseg*overlap_fac_nom))
    overlap_fac = noverlap / nperseg
    fs          = 1./dt ## dimensional [1/s]
    
    ## get [freq] vector
    freq,_ = csd(
            np.zeros((nt,),dtype=np.float64),
            np.zeros((nt,),dtype=np.float64),
            fs=fs,
            nperseg=nperseg,
            noverlap=noverlap,
            window='hann',
            detrend='constant',
            scaling='density',
            return_onesided=True,
            )
    
    nf = freq.shape[0]
    df = np.diff(freq)[0]
    
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
    
    ## spatial [z] wavenumber (kz) vector
    kz_full = sp.fft.fftfreq(n=nz, d=dz0) * ( 2 * np.pi )
    kzp     = np.where(kz_full>0) ## indices of positive values
    kz      = np.copy(kz_full[kzp])
    dkz     = kz[1] - kz[0]
    nkz     = kz.shape[0]
    
    ## wavenumber vector should be size nz//2-1
    if (nkz!=nz//2-1):
        raise ValueError
    
    data['kz']  = kz
    data['dkz'] = dkz
    data['nkz'] = nkz
    
    if verbose:
        even_print('kz min',f'{kz.min():0.1f} [1/m]')
        even_print('kz max',f'{kz.max():0.1f} [1/m]')
        even_print('dkz',f'{dkz:0.1f} [1/m]')
        even_print('nkz',f'{nkz:d}')
        print(72*'-')
    
    ## wavelength λz = (2·π)/kz
    lz = np.copy( 2 * np.pi / kz )
    data['lz'] = lz
    
    # ==============================================================
    # prepare buffers, etc.
    # ==============================================================
    
    do_density_weighting = False ## deactivated for now... would need implementation
    
    ## cospectrum pairs
    ## [ str:var1, str:var2 ]
    fft_combis = [
    
    [ 'u_tau' , 'u_tau' ], ## [ uτ , uτ ] --> FFT[ uτ′ , uτ′ ]
    [ 'v_tau' , 'v_tau' ], ## [ vτ , vτ ] --> FFT[ vτ′ , vτ′ ]
    [ 'w_tau' , 'w_tau' ], ## [ wτ , wτ ] --> FFT[ wτ′ , wτ′ ]
    
    #[ 'u_tau' , 'v_tau' ], ## [ uτ , vτ ] --> FFT[ uτ′ , vτ′ ]
    #[ 'u_tau' , 'w_tau' ], ## [ uτ , wτ ] --> FFT[ uτ′ , wτ′ ]
    #[ 'v_tau' , 'w_tau' ], ## [ vτ , wτ ] --> FFT[ vτ′ , wτ′ ]
    
    [ 'tau_uy' , 'tau_uy' ], ## [ τuy , τuy ] --> FFT[ τuy′ , τuy′ ]
    [ 'tau_vy' , 'tau_vy' ], ## [ τvy , τvy ] --> FFT[ τvy′ , τvy′ ]
    [ 'tau_wy' , 'tau_wy' ], ## [ τwy , τwy ] --> FFT[ τwy′ , τwy′ ]
    
    #[ 'tau_uy' , 'tau_vy' ], ## [ τuy , τvy ] --> FFT[ τuy′ , τvy′ ]
    #[ 'tau_uy' , 'tau_wy' ], ## [ τuy , τwy ] --> FFT[ τuy′ , τwy′ ]
    #[ 'tau_vy' , 'tau_wy' ], ## [ τvy , τwy ] --> FFT[ τvy′ , τwy′ ]
    
    [ 'p'   , 'p'   ], ## [p,p] --> FFT[ p′ , p′ ]
    [ 'T'   , 'T'   ], ## [T,T] --> FFT[ T′ , T′ ]
    [ 'rho' , 'rho' ], ## [ρ,ρ] --> FFT[ ρ′ , ρ′ ]
    
    [ 'u_tau'  , 'p' ], ## [uτ,p] --> FFT[ uτ′  , p′ ]
    [ 'tau_uy' , 'p' ], ## [τuy,p] --> FFT[ τuy′ , p′ ]
    
    ]
    
    ## generate FFT cospectrum scalar names
    scalars = []
    for fft_combi in fft_combis:
        #s1,s2,do_density_weighting = fft_combi
        s1,s2 = fft_combi
        if do_density_weighting:
            raise NotImplementedError
        else:
            scalars.append(f"{s1.replace('_','')}I_{s2.replace('_','')}I")
    
    ## generate AVG scalar names
    scalars_Re_avg = []
    #scalars_Fv_avg = []
    for fft_combi in fft_combis:
        #s1,s2,do_density_weighting = fft_combi
        s1,s2 = fft_combi
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
    Ekz        = np.zeros(shape=(nir,nkz ) , dtype={'names':scalars         , 'formats':[ np.dtype(np.complex128) for s in scalars        ]})
    Ef         = np.zeros(shape=(nir,nf  ) , dtype={'names':scalars         , 'formats':[ np.dtype(np.complex128) for s in scalars        ]})
    covariance = np.zeros(shape=(nir,    ) , dtype={'names':scalars         , 'formats':[ np.dtype(np.float64)    for s in scalars        ]})
    avg_Re     = np.zeros(shape=(nir,    ) , dtype={'names':scalars_Re_avg  , 'formats':[ np.dtype(np.float64)    for s in scalars_Re_avg ]})
    #avg_Fv     = np.zeros(shape=(nir,    ) , dtype={'names':scalars_Fv_avg  , 'formats':[ np.dtype(np.float64)    for s in scalars_Fv_avg ]})
    
    if verbose:
        even_print('n turb spectrum scalar combinations' , '%i'%(len(fft_combis),))
        print(72*'-')
    
    ## window for [z] -- rectangular because [z] is assumed periodic already
    window_z       = np.ones(nz,dtype=np.float64)
    mean_sq_win_z  = np.mean(window_z**2)
    if verbose:
        even_print('mean(window_z**2)', '%0.5f'%(mean_sq_win_z,))
    
    # ==============================================================
    # main loop
    # ==============================================================
    
    if verbose:
        progress_bar = tqdm(
            total=len(fft_combis)*nir,
            ncols=100,
            desc='fft',
            leave=True,
            file=sys.stdout,
            mininterval=0.1,
            smoothing=0.,
            #bar_format="\033[B{l_bar}{bar}| {n}/{total} [{percentage:.1f}%] {elapsed}/{remaining}\033[A\n\b",
            bar_format="{l_bar}{bar}| {n}/{total} [{percentage:.1f}%] {elapsed}/{remaining}",
            ascii="░█",
            colour='#FF6600',
            )
    
    for cci,cc in enumerate(fft_combis): ## fft pairs
        
        if verbose: tqdm.write(72*'-')
        
        scalar_L, scalar_R = cc
        
        msg = f'FFT[{scalar_L}′,{scalar_R}′]'
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
        
        ## [x] loop (rank-local)
        for ii in range(ri1,ri2):
            
            iii = ii - ri1
            
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
            
            ## covariance: <□′·□′> OR <ρ□″·ρ□″> --> note that this is NOT the typical Favre <ρ·□″□″>
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
            
            ## do [z] FFT for every [t]
            Ekz_buf = np.zeros((nt,nkz), dtype=np.complex128)
            for ti in range(nt):
                uL = np.copy( data_L[:,ti] )
                uR = np.copy( data_R[:,ti] )
                
                ## One-sided amplitude spectra
                A1 = sp.fft.fft( uL * window_z )[kzp] / nz
                A2 = sp.fft.fft( uR * window_z )[kzp] / nz
                
                Ekz_buf[ti,:] = 2. * A1 * np.conj(A2) / ( dkz * mean_sq_win_z )
            
            Ekz[scalar][iii,:] = np.mean(Ekz_buf, axis=0) ## mean across [t] --> (nkz,)
            
            ## do [t] FFT for every [z]
            Ef_buf = np.zeros((nz,nf), dtype=np.complex128)
            #for zi in range(self.nj):
            for zi in range(nz):
                uL = np.copy( data_L[zi,:] )
                uR = np.copy( data_R[zi,:] )
                
                ## One-sided complex cross-spectral density in [f] (using Welch's method)
                _,P = csd(
                        uL,uR,
                        fs=fs,
                        nperseg=nperseg,
                        noverlap=noverlap,
                        window='hann',
                        detrend='constant',
                        scaling='density',
                        return_onesided=True,
                        )
                
                Ef_buf[zi,:] = P
            
            Ef[scalar][iii,:] = np.mean(Ef_buf, axis=0) ## mean across [z] --> (nf,)
            
            self.comm.Barrier() ## [x] loop ('ii' within this rank's range)
            if verbose: progress_bar.update()
            
            #break ## DEBUG
    
    self.comm.Barrier()
    if verbose:
        progress_bar.close()
        print(72*'-')
    
    # ==============================================================
    # write HDF5 (.h5) file
    # ==============================================================
    
    ## overwrite outfile!
    ## open on rank 0 and write attributes, dimensions, etc.
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
            hfw.create_dataset( 'dims/x'    , data=x    ) ## [m]
            hfw.create_dataset( 'dims/z'    , data=z    ) ## [m]
            hfw.create_dataset( 'dims/t'    , data=t    ) ## [s]
            hfw.create_dataset( 'dims/freq' , data=freq ) ## [1/s] | [Hz]
            hfw.create_dataset( 'dims/kz'   , data=kz   ) ## [1/m]
            hfw.create_dataset( 'dims/lz'   , data=lz   ) ## [m]
            
            ## initialize datasets : covariance,Ekz,Ef
            for scalar in scalars:
                hfw.create_dataset( f'covariance/{scalar}' , shape=(nx,)    , dtype=np.float64    , chunks=None    , data=np.full((nx,),0.,np.float64)       )
                hfw.create_dataset( f'Ekz/{scalar}'        , shape=(nx,nkz) , dtype=np.complex128 , chunks=(1,nkz) , data=np.full((nx,nkz),0.,np.complex128) )
                hfw.create_dataset( f'Ef/{scalar}'         , shape=(nx,nf)  , dtype=np.complex128 , chunks=(1,nf)  , data=np.full((nx,nf),0.,np.complex128)  )
            
            ## initialize datasets : 1D [x] mean
            for scalar in avg_Re.dtype.names:
                hfw.create_dataset( f'avg/Re/{scalar}', shape=(nx,), dtype=np.float64, chunks=None, data=np.full((nx,),0.,np.float64) )
    
    self.comm.Barrier()
    
    ## re-open in parallel for data writes
    with h5py.File(fn_h5_out, 'a', driver='mpio', comm=self.comm) as hfw:
        
        ## collectively write covariance,Ekz,Ef
        for scalar in scalars:
            dset = hfw[f'covariance/{scalar}']
            with dset.collective:
                dset[ri1:ri2] = covariance[scalar][:]
            dset = hfw[f'Ekz/{scalar}']
            with dset.collective:
                dset[ri1:ri2,:] = Ekz[scalar][:,:]
            dset = hfw[f'Ef/{scalar}']
            with dset.collective:
                dset[ri1:ri2,:] = Ef[scalar][:,:]
        
        ## collectively write 1D [y] avgs
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
    if verbose: print('total time : spd.calc_turb_cospectrum_wall() : %s'%format_time_string((timeit.default_timer() - t_start_func)))
    if verbose: print(72*'-')
    return
