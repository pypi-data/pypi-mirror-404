import os
import re
import sys
import timeit
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path, PurePosixPath

import h5py
import numpy as np
import psutil
import scipy as sp
from mpi4py import MPI
from scipy.signal import csd
from tqdm import tqdm

from .h5 import h5_print_contents
from .utils import even_print, format_time_string

# ======================================================================

def _calc_turb_cospectrum_xpln(self, **kwargs):
    '''
    Calculate FFT cospectrum in [z,t] at every [x,y]
    - Designed for analyzing unsteady, thin planes in [x]
    - Multithreaded with ThreadPoolExecutor()
        - scipy.signal.csd() automatically tries to run multithreaded
        - set OMP_NUM_THREADS=1 and pass 'n_threads' to as kwarg manually
    '''
    
    if (self.rank==0):
        verbose = True
    else:
        verbose = False
    
    if verbose: print('\n'+'rgd.calc_turb_cospectrum_xpln()'+'\n'+72*'-')
    t_start_func = timeit.default_timer()
    
    ## assert that the opened RGD has fsubtype 'unsteady' (i.e. is NOT a prime file)
    if (self.fsubtype!='unsteady'):
        raise ValueError
    if not self.usingmpi:
        raise NotImplementedError('function is not implemented for non-MPI usage')
    
    if not h5py.h5.get_config().mpi:
        if verbose: print('h5py was not compiled for parallel usage! exiting.')
        sys.exit(1)
    
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
    
    n_threads = kwargs.get('n_threads',1)
    
    ## Debug Rank:Proc Affinity
    #pp = psutil.Process()
    #print(f"[Rank {self.rank}] sees CPUs: {pp.cpu_affinity()}  |  n_threads={n_threads}  |  OMP_NUM_THREADS={os.environ.get('OMP_NUM_THREADS')}")
    
    #try:
    #    n_threads = int(os.environ.get('OMP_NUM_THREADS'))
    #except TypeError: ## not set
    #    n_threads = os.cpu_count()
    
    fn_h5_out       = kwargs.get('fn_h5_out',None)       ## filename for output HDF5 (.h5) file
    overlap_fac_nom = kwargs.get('overlap_fac_nom',0.50) ## nominal windows overlap factor
    n_win           = kwargs.get('n_win',8)              ## number of segment windows for [t] PSD calc
    #window_type     = kwargs.get('window_type','hann')   ## 'tukey','hann'
    
    ## only distribute data across [y]
    if (rx!=1):
        raise ValueError('rx!=1')
    if (rz!=1):
        raise ValueError('rz!=1')
    if (rt!=1):
        raise ValueError('rt!=1')
    
    if not isinstance(ry,int) or (ry<1):
        raise ValueError('ry should be a positive non-zero int')
    
    ## check the choice of ranks per dimension
    if (rx*ry*rz*rt != self.n_ranks):
        raise ValueError('rx*ry*rz*rt != self.n_ranks')
    if (rx>self.nx):
        raise ValueError('rx>self.nx')
    if (ry>self.ny):
        raise ValueError('ry>self.ny')
    if (rz>self.nz):
        raise ValueError('rz>self.nz')
    if (rt>self.nt):
        raise ValueError('rt>self.nt')
    
    if (self.ny%ry!=0):
        raise ValueError('ny not divisible by ry')
    
    ## distribute 4D data over ranks --> here only in [y]
    ryl_ = np.array_split(np.arange(self.ny,dtype=np.int64),ry)
    ryl = [[b[0],b[-1]+1] for b in ryl_ ]
    ry1,ry2 = ryl[self.rank]
    nyr = ry2 - ry1
    
    ## check all [y] ranges have same size
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
    
    ## output filename : HDF5 (.h5)
    if (fn_h5_out is None): ## automatically determine name
        fname_path = os.path.dirname(self.fname)
        fname_base = os.path.basename(self.fname)
        fname_root, fname_ext = os.path.splitext(fname_base)
        fname_root = re.findall(r'io\S+_mpi_[0-9]+', fname_root)[0]
        fname_fft_h5_base = fname_root+'_fft.h5'
        fn_h5_out = str(PurePosixPath(fname_path, fname_fft_h5_base))
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
    
    ## the data dictionary to be written to .h5 later
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
    
    ## read in 1D coordinate arrays & re-dimensionalize
    x = np.copy( self['dims/x'][()] * self.lchar )
    y = np.copy( self['dims/y'][()] * self.lchar )
    z = np.copy( self['dims/z'][()] * self.lchar )
    t = np.copy( self['dims/t'][()] * self.tchar )
    
    nx = self.nx ; data['nx'] = nx
    ny = self.ny ; data['ny'] = ny
    nz = self.nz ; data['nz'] = nz
    nt = self.nt ; data['nt'] = nt
    
    ## assert constant Δz
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
    
    ## establish [t] windowing (old)
    #win_len, overlap = get_overlapping_window_size(nt, n_win, overlap_fac_nom)
    #overlap_fac = overlap / win_len
    #tw, n_win, n_pad = get_overlapping_windows(t, win_len, overlap)
    #t_meas_per_win = (win_len-1)*dt
    #data['win_len']        = win_len
    #data['overlap_fac']    = overlap_fac
    #data['overlap']        = overlap
    #data['n_win']          = n_win
    #data['t_meas_per_win'] = t_meas_per_win
    
    # ## temporal [t] frequency (f) vector (Short Time Fourier Transform)
    # freq_full = sp.fft.fftfreq(n=win_len, d=dt)
    # fp        = np.where(freq_full>0) ## indices of positive values
    # freq      = np.copy(freq_full[fp])
    # df        = freq[1] - freq[0]
    # nf        = freq.size
    
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
    
    ## spatial [x] wavenumber (kx) and wavelength (λx)
    # λx  = u/f
    # kx  = 2·π·f/u
    # λx+ = λx/(ν/uτ)
    # kx+ = (2·π·f/u)·(ν/uτ)
    
    ## kx = 2·π·f/u --> [y,f]
    #kx = np.copy( 2*np.pi*freq[na,:] / u_avg[:,na] )
    
    ## λx = u/f --> [y,f]
    #lx = np.copy( u_avg[:,na] / freq[na,:] )
    
    #data['kx'] = kx
    #data['lx'] = lx
    
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
    
    ## Wavelength λz = (2·π)/kz
    lz = np.copy( 2 * np.pi / kz )
    data['lz'] = lz
    
    # ===
    
    ## cospectrum pairs
    ## [ (str:var1, bool:ρ_weighting) , (str:var2, bool:ρ_weighting) ]
    fft_combis = [
    
    [ ('u',True) , ('v',True) ], ## [ ρ·u″ , ρ·v″ ]
    [ ('u',True) , ('u',True) ], ## [ ρ·u″ , ρ·u″ ]
    [ ('v',True) , ('v',True) ], ## [ ρ·v″ , ρ·v″ ]
    [ ('w',True) , ('w',True) ], ## [ ρ·w″ , ρ·w″ ]
    
    [ ('u',False) , ('v',False) ], ## [ u′ , v′ ]
    [ ('u',False) , ('u',False) ], ## [ u′ , u′ ]
    [ ('v',False) , ('v',False) ], ## [ v′ , v′ ]
    [ ('w',False) , ('w',False) ], ## [ w′ , w′ ]
    
    [ ('p',False) , ('u',False) ], ## [ p′ , u′ ]
    [ ('p',False) , ('v',False) ], ## [ p′ , v′ ]
    [ ('p',False) , ('w',False) ], ## [ p′ , w′ ]
    
    [ ('p',False) , ('u',True) ], ## [ p′ , ρ·u″ ]
    [ ('p',False) , ('v',True) ], ## [ p′ , ρ·v″ ]
    [ ('p',False) , ('w',True) ], ## [ p′ , ρ·w″ ]
    
    [ ('p',False)   , ('p',False)   ], ## [ p′ , p′ ]
    [ ('T',False)   , ('T',False)   ], ## [ T′ , T′ ]
    [ ('rho',False) , ('rho',False) ], ## [ ρ′ , ρ′ ]
    
    ]
    
    ## generate FFT cospectrum scalar names
    scalars = []
    for fft_combi in fft_combis:
        if not isinstance(fft_combi,list):
            raise RuntimeError
        if not len(fft_combi)==2:
            raise RuntimeError
        
        sL = fft_combi[0][0]
        do_density_weighting_L = fft_combi[0][1]
        if do_density_weighting_L:
            sLs = f'r{sL}II'
        else:
            sLs = f'{sL}I'
        
        sR = fft_combi[1][0]
        do_density_weighting_R = fft_combi[1][1]
        if do_density_weighting_R:
            sRs = f'r{sR}II'
        else:
            sRs = f'{sR}I'
        
        scalars.append(f'{sLs}_{sRs}')
    
    ## generate avg scalar names
    scalars_Re_avg = []
    scalars_Fv_avg = []
    for fft_combi in fft_combis:
        sL = fft_combi[0][0]
        do_density_weighting_L = fft_combi[0][1]
        sR = fft_combi[1][0]
        do_density_weighting_R = fft_combi[1][1]
        
        if do_density_weighting_L or do_density_weighting_R:
            if 'rho' not in scalars_Re_avg:
                scalars_Re_avg.append('rho')
        
        if do_density_weighting_L:
            if sL not in scalars_Fv_avg:
                scalars_Fv_avg.append(sL)
        else:
            if sL not in scalars_Re_avg:
                scalars_Re_avg.append(sL)
        
        if do_density_weighting_R:
            if sR not in scalars_Fv_avg:
                scalars_Fv_avg.append(sR)
        else:
            if sR not in scalars_Re_avg:
                scalars_Re_avg.append(sR)
    
    ## numpy formatted arrays: buffers for PSD & other data (rank-local)
    Ekz        = np.zeros(shape=(nyr,nkz ) , dtype={'names':scalars        , 'formats':[ np.dtype(np.complex128) for s in scalars        ] })
    Ef         = np.zeros(shape=(nyr,nf  ) , dtype={'names':scalars        , 'formats':[ np.dtype(np.complex128) for s in scalars        ] })
    covariance = np.zeros(shape=(nyr,    ) , dtype={'names':scalars        , 'formats':[ np.dtype(np.float64)    for s in scalars        ] })
    avg_Re     = np.zeros(shape=(nyr,    ) , dtype={'names':scalars_Re_avg , 'formats':[ np.dtype(np.float64)    for s in scalars_Re_avg ] })
    avg_Fv     = np.zeros(shape=(nyr,    ) , dtype={'names':scalars_Fv_avg , 'formats':[ np.dtype(np.float64)    for s in scalars_Fv_avg ] })
    
    if verbose:
        even_print('n turb spectrum scalar combinations' , '%i'%(len(fft_combis),))
        print(72*'-')
    
    ## window for [z] -- rectangular because [z] is assumed periodic already
    window_z       = np.ones(nz,dtype=np.float64)
    sum_sqrt_win_z = np.sum(np.sqrt(window_z))
    mean_sq_win_z  = np.mean(window_z**2)
    if verbose:
        #even_print('sum(sqrt(window_z))'      , '%0.5f'%(sum_sqrt_win_z,))
        even_print('sum(sqrt(window_z)) / nz' , '%0.5f'%(sum_sqrt_win_z/nz,))
        even_print('mean(window_z**2)'        , '%0.5f'%(mean_sq_win_z,))
    
    # ## window function for [t]
    # if (window_type=='tukey'):
    #     window_t = sp.signal.windows.tukey(win_len,alpha=0.5,sym=False) ## α=0:rectangular, α=1:Hann
    # elif (window_type=='hann'):
    #     window_t = sp.signal.windows.hann(win_len,sym=False)
    # elif (window_type is None):
    #     window_t = np.ones(win_len, dtype=np.float64)
    # else:
    #     raise ValueError
    # 
    # if verbose:
    #     even_print('window type [t]', '\'%s\''%str(window_type))
    # 
    # ## sum of sqrt of window: needed for normalization
    # sum_sqrt_win_t = np.sum(np.sqrt(window_t))
    # if verbose:
    #     #even_print('sum(sqrt(window_t))'          , '%0.5f'%(sum_sqrt_win_t,))
    #     even_print('sum(sqrt(window_t)) / win_len', '%0.5f'%(sum_sqrt_win_t/win_len,))
    
    #if verbose: print(72*'-')
    
    # ==============================================================
    # check memory
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
    
    if verbose: even_print('read size (global) ×8', f'{int(np.ceil(data_gb*ry*8)):d} [GB]')
    ram_usage_est = data_gb*ry*8/total_free
    if verbose: even_print('RAM usage estimate', f'{100*ram_usage_est:0.1f} [%]')
    
    self.comm.Barrier()
    if (ram_usage_est>0.80):
        print('RAM consumption might be too high. exiting.')
        self.comm.Abort(1)
    
    # ==============================================================
    # main loop
    # ==============================================================
    
    if verbose:
        progress_bar = tqdm(
            #total=len(fft_combis)*cy,
            total=len(fft_combis)*(nyr//sy),
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
        
        scalar_L = cc[0][0]
        do_density_weighting_L = cc[0][1]
        scalar_R = cc[1][0]
        do_density_weighting_R = cc[1][1]
        
        if do_density_weighting_L:
            sLs  = f'r{scalar_L}II'
            sLsF = f'ρ·{scalar_L}″'
        else:
            sLs  = f'{scalar_L}I'
            sLsF = f'{scalar_L}′'
        
        if do_density_weighting_R:
            sRs  = f'r{scalar_R}II'
            sRsF = f'ρ·{scalar_R}″'
        else:
            sRs  = f'{scalar_R}I'
            sRsF = f'{scalar_R}′'
        
        msg = f'[{sLsF},{sRsF}]'
        
        dset_L   = self[f'data/{scalar_L}']
        dset_R   = self[f'data/{scalar_R}']
        dset_rho = self['data/rho']
        
        scalar = scalars[cci]
        
        ## assert scalar name
        if (f'{sLs}_{sRs}' != scalar):
            raise RuntimeError(f"'{sLs}_{sRs}' != '{scalar}'")
        
        ## [y] loop outer (grid subchunks within rank)
        # for cyl_ in cyl:
        #     cy1, cy2 = cyl_
        #     nyc = cy2 - cy1
        
        for ci in range(nyr//sy):
            
            ## buffers
            data_L = np.zeros((nx,sy,nz,nt), dtype=np.float64)
            data_R = np.zeros((nx,sy,nz,nt), dtype=np.float64)
            if do_density_weighting_L or do_density_weighting_R:
                rho = np.zeros((nx,sy,nz,nt), dtype=np.float64)
            else:
                rho = None
            
            cy1 = ry1 + ci*sy
            cy2 = cy1 + sy
            nyc = cy2 - cy1
            
            self.comm.Barrier()
            t_start = timeit.default_timer()
            
            ## read data L
            n_scalars_read = 1 ## initialize
            scalar_str = scalar_L
            with dset_L.collective:
                data_L[:,:,:,:] = dset_L[:,:,cy1:cy2,:].T
            
            ## read data R (if != data L)
            if (scalar_L==scalar_R):
                data_R[:,:,:,:] = data_L[:,:,:,:]
            else:
                n_scalars_read += 1
                scalar_str += f',{scalar_R}'
                with dset_R.collective:
                    data_R[:,:,:,:] = dset_R[:,:,cy1:cy2,:].T
            
            ## read ρ
            if do_density_weighting_L or do_density_weighting_R:
                n_scalars_read += 1
                scalar_str += ',ρ'
                with dset_rho.collective:
                    rho[:,:,:,:] = dset_rho[:,:,cy1:cy2,:].T
            else:
                rho = None
            
            self.comm.Barrier()
            t_delta = timeit.default_timer() - t_start
            data_gb = n_scalars_read * ( nx * ry * (cy2-cy1) * nz * nt * dset_L.dtype.itemsize ) / 1024**3
            if verbose:
                tqdm.write(even_print(f'read: {scalar_str}', '%0.3f [GB]  %0.3f [s]  %0.3f [GB/s]'%(data_gb,t_delta,(data_gb/t_delta)), s=True))
            
            ## data_L and data_R should be [nx,nyc,nz,nt] where nyc is the chunk [y] range
            if ( data_L.shape != (nx,nyc,nz,nt) ) or ( data_R.shape != (nx,nyc,nz,nt) ):
                print(f'rank {self.rank:d}: shape violation')
                self.comm.Abort(1)
            if (rho is not None) and ( rho.shape != (nx,nyc,nz,nt) ):
                print(f'rank {self.rank:d}: shape violation')
                self.comm.Abort(1)
            
            # === redimensionalize
            
            if scalar_L in ['u','v','w',]:
                data_L *= U_inf
            elif scalar_L in ['p',]:
                data_L *= rho_inf * U_inf**2
            elif scalar_L in ['T',]:
                data_L *= T_inf
            elif scalar_L in ['rho',]:
                data_L *= rho_inf
            else:
                raise RuntimeError
            
            if scalar_R in ['u','v','w',]:
                data_R *= U_inf
            elif scalar_R in ['p',]:
                data_R *= rho_inf * U_inf**2
            elif scalar_R in ['T',]:
                data_R *= T_inf
            elif scalar_R in ['rho',]:
                data_R *= rho_inf
            else:
                raise RuntimeError
            
            if (rho is not None):
                rho *= rho_inf
            
            # === compute mean-removed data
            
            ## Reynolds avg(□) or Favre avg(ρ·□)/avg(ρ) in [t]
            if do_density_weighting_L:
                rho_avg     = np.mean(        rho , axis=3, dtype=np.float64, keepdims=True) ## [x,y,z,1]
                data_L_avg  = np.mean( rho*data_L , axis=3, dtype=np.float64, keepdims=True) ## [x,y,z,1]
                data_L_avg /= rho_avg
            else:
                data_L_avg = np.mean( data_L , axis=3, dtype=np.float64, keepdims=True) ## [x,y,z,1]
            
            ## Reynolds avg(□) or Favre avg(ρ·□)/avg(ρ) in [t]
            if do_density_weighting_R:
                rho_avg     = np.mean(        rho , axis=3, dtype=np.float64, keepdims=True) ## [x,y,z,1]
                data_R_avg  = np.mean( rho*data_R , axis=3, dtype=np.float64, keepdims=True) ## [x,y,z,1]
                data_R_avg /= rho_avg
            else:
                data_R_avg = np.mean( data_R , axis=3, dtype=np.float64, keepdims=True) ## [x,y,z,1]
            
            ## Reynolds prime □′ or Favre prime □″
            data_L -= data_L_avg
            data_R -= data_R_avg
            
            ## LEFT
            ## Assert stationarity + definition Re/Fv averaging
            ## avg(□′)==0 or avg(ρ·□″)==0
            if do_density_weighting_L:
                a_ = np.mean(rho*data_L, axis=3, dtype=np.float64, keepdims=True)
            else:
                a_ = np.mean(data_L, axis=3, dtype=np.float64, keepdims=True)
            if not np.allclose( a_, np.zeros_like(a_), atol=1e-6 ):
                print(f'rank {self.rank:d}: avg(□′)!=0 or avg(ρ·□″)!=0')
                self.comm.Abort(1)
            
            ## RIGHT
            ## Assert stationarity + definition Re/Fv averaging
            ## avg(□′)==0 or avg(ρ·□″)==0
            if do_density_weighting_R:
                a_ = np.mean(rho*data_R, axis=3, dtype=np.float64, keepdims=True)
            else:
                a_ = np.mean(data_R, axis=3, dtype=np.float64, keepdims=True)
            if not np.allclose( a_, np.zeros_like(a_), atol=1e-6 ):
                print(f'rank {self.rank:d}: avg(□′)!=0 or avg(ρ·□″)!=0')
                self.comm.Abort(1)
            
            ## covariance: <□′·□′> OR <ρ□″·ρ□″> etc. --> note that this is NOT the typical Favre <ρ·□″□″> except in special cases
            if do_density_weighting_L and do_density_weighting_R:
                covariance_ = np.mean( rho*data_L * rho*data_R , axis=3 , dtype=np.float64, keepdims=True)
            elif do_density_weighting_L and not do_density_weighting_R:
                covariance_ = np.mean( rho*data_L * data_R , axis=3 , dtype=np.float64, keepdims=True)
            elif not do_density_weighting_L and do_density_weighting_R:
                covariance_ = np.mean( data_L * rho*data_R , axis=3 , dtype=np.float64, keepdims=True)
            elif not do_density_weighting_L and not do_density_weighting_R:
                covariance_ = np.mean( data_L * data_R , axis=3 , dtype=np.float64, keepdims=True)
            else:
                raise RuntimeError
            
            ## write this chunk/scalar's covariance to covariance buffer
            ## avg over [x,z] : [x,y,z,1] --> [y]
            yiA = cy1 - ry1
            yiB = cy2 - ry1
            covariance[scalar][yiA:yiB] = np.squeeze( np.mean( covariance_ , axis=(0,2,3) , dtype=np.float64) )
            
            ## write (rank-local) 1D [y] averages
            if do_density_weighting_L or do_density_weighting_R:
                avg_Re['rho'][yiA:yiB] = np.squeeze( np.mean( rho_avg    , axis=(0,2,3) , dtype=np.float64) )
            
            if do_density_weighting_L:
                avg_Fv[scalar_L][yiA:yiB] = np.squeeze( np.mean( data_L_avg , axis=(0,2,3) , dtype=np.float64) )
            else:
                avg_Re[scalar_L][yiA:yiB] = np.squeeze( np.mean( data_L_avg , axis=(0,2,3) , dtype=np.float64) )
            
            if do_density_weighting_R:
                avg_Fv[scalar_R][yiA:yiB] = np.squeeze( np.mean( data_R_avg , axis=(0,2,3) , dtype=np.float64) )
            else:
                avg_Re[scalar_R][yiA:yiB] = np.squeeze( np.mean( data_R_avg , axis=(0,2,3) , dtype=np.float64) )
            
            # ===============================================================================
            # At this point you have 4D [x,y,z,t] □′ or □″ data
            # ===============================================================================
            
            def __fft_z_thread_kernel(xi,ti,yii,do_density_weighting_L,do_density_weighting_R):
                
                ## 1D [z] □′ or ρ·□″ vectors
                if do_density_weighting_L:
                    uL = rho[xi,yii,:,ti] * data_L[xi,yii,:,ti]
                else:
                    uL = data_L[xi,yii,:,ti]
                
                if do_density_weighting_R:
                    uR = rho[xi,yii,:,ti] * data_R[xi,yii,:,ti]
                else:
                    uR = data_R[xi,yii,:,ti]
                
                ## One-sided amplitude spectra
                A1 = sp.fft.fft( uL * window_z )[kzp] / nz
                A2 = sp.fft.fft( uR * window_z )[kzp] / nz
                
                #P = 2. * np.real(A1*np.conj(A2)) / ( dkz * mean_sq_win_z )
                
                ## One-sided complex cross-spectral density in [kz]
                P = 2. * A1 * np.conj(A2) / ( dkz * mean_sq_win_z )
                
                return xi,ti,P
            
            def __fft_t_thread_kernel(xi,zi,yii,do_density_weighting_L,do_density_weighting_R):
                
                ## 1D [t] □′ or ρ·□″ vectors
                if do_density_weighting_L:
                    uL = rho[xi,yii,zi,:] * data_L[xi,yii,zi,:]
                else:
                    uL = data_L[xi,yii,zi,:]
                
                if do_density_weighting_R:
                    uR = rho[xi,yii,zi,:] * data_R[xi,yii,zi,:]
                else:
                    uR = data_R[xi,yii,zi,:]
                
                ## ## OLD with manual windowing
                ## uL_, nw, n_pad = get_overlapping_windows(uL, win_len, overlap)
                ## uR_, nw, n_pad = get_overlapping_windows(uR, win_len, overlap)
                ## 
                ## ## STFT buffer
                ## E_ijk_buf = np.zeros((nw,nf), dtype=np.float64)
                ## 
                ## ## compute fft for each overlapped window segment
                ## for wi in range(nw):
                ##     A1 = sp.fft.fft( uL_[wi,:] * window_t )[fp] / sum_sqrt_win_t
                ##     A2 = sp.fft.fft( uR_[wi,:] * window_t )[fp] / sum_sqrt_win_t
                ##     E_ijk_buf[wi,:] = 2. * np.real(A1*np.conj(A2)) / df
                ## 
                ## ## mean across short time FFT (STFT) segments
                ## E_ijk = np.mean(E_ijk_buf, axis=0, dtype=np.float64)
                
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
                
                ### Real part = co-spectral density (in-phase contribution to covariance)
                #P = np.real(P)
                #return xi,zi,P
                
                return xi,zi,P
            
            # ===============================================================================
            
            ## [y] loop inner ([y] indices within subdivision within rank)
            for yi in range(cy1,cy2):
                
                yii  = yi - cy1 ## chunk local
                yiii = yi - ry1 ## rank local
                
                ## PSD buffers for [y] loop inner
                E_xt = np.zeros((nx,nt,nkz) , dtype=np.complex128) ## [x,t] range for FFT(z)
                E_xz = np.zeros((nx,nz,nf ) , dtype=np.complex128) ## [x,z] range for FFT(t)
                
                # ===========================================================================
                # FFT(z) : loop over [x,t]
                # ===========================================================================
                
                ## concurrent/threaded execution for fft(z)
                tasks = [(xi,ti,yii,do_density_weighting_L,do_density_weighting_R) for xi in range(nx) for ti in range(nt)]
                with ThreadPoolExecutor(max_workers=n_threads) as executor:
                    results = executor.map(lambda task: __fft_z_thread_kernel(*task,), tasks)
                    for xi,ti,P in results:
                        E_xt[xi,ti,:] = P
                
                ## for xi in range(nx):
                ##     for ti in range(nt):
                ##         ...
                
                ## avg in [x,t] & write in rank context
                Ekz[scalar][yiii,:] = np.mean(E_xt, axis=(0,1))
                
                # ===========================================================================
                # FFT(t) : loop over [x,z], use windows
                # ===========================================================================
                
                ## concurrent/threaded execution for fft(t)
                tasks = [(xi,zi,yii,do_density_weighting_L,do_density_weighting_R) for xi in range(nx) for zi in range(nz)]
                with ThreadPoolExecutor(max_workers=n_threads) as executor:
                    results = executor.map(lambda task: __fft_t_thread_kernel(*task,), tasks)
                    for xi,zi,P in results:
                        E_xz[xi,zi,:] = P
                
                ## for xi in range(nx):
                ##     for zi in range(nz):
                ##         ...
                
                ## avg in [x,z] & write in rank context
                Ef[scalar][yiii,:] = np.mean(E_xz, axis=(0,1))
            
            self.comm.Barrier()
            t_delta = timeit.default_timer() - t_start
            if verbose: tqdm.write(even_print(msg, format_time_string(t_delta), s=True))
            if verbose: progress_bar.update() ## (scalar, [y] chunk) progress
            
            #break ## debug --> only do one round in [y] sub-chunk loop
    
    if verbose: progress_bar.close()
    self.comm.Barrier()
    if verbose: print(72*'-')
    
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
            hfw.create_dataset( 'dims/y'    , data=y    ) ## [m]
            hfw.create_dataset( 'dims/z'    , data=z    ) ## [m]
            hfw.create_dataset( 'dims/t'    , data=t    ) ## [s]
            hfw.create_dataset( 'dims/freq' , data=freq ) ## [1/s] | [Hz]
            hfw.create_dataset( 'dims/kz'   , data=kz   ) ## [1/m]
            hfw.create_dataset( 'dims/lz'   , data=lz   ) ## [m]
            
            ## initialize datasets
            for scalar in scalars:
                hfw.create_dataset( f'covariance/{scalar}' , shape=(ny,)    , dtype=np.float64    , chunks=None    , data=np.full((ny,),0.,np.float64)       )
                hfw.create_dataset( f'Ekz/{scalar}'        , shape=(ny,nkz) , dtype=np.complex128 , chunks=(1,nkz) , data=np.full((ny,nkz),0.,np.complex128) )
                hfw.create_dataset( f'Ef/{scalar}'         , shape=(ny,nf)  , dtype=np.complex128 , chunks=(1,nf)  , data=np.full((ny,nf),0.,np.complex128)  )
            
            ## initialize datasets 1D [y] mean
            for scalar in avg_Re.dtype.names:
                hfw.create_dataset( f'avg/Re/{scalar}', shape=(ny,), dtype=np.float64, chunks=None, data=np.full((ny,),0.,np.float64) )
            for scalar in avg_Fv.dtype.names:
                hfw.create_dataset( f'avg/Fv/{scalar}', shape=(ny,), dtype=np.float64, chunks=None, data=np.full((ny,),0.,np.float64) )
    
    self.comm.Barrier()
    
    with h5py.File(fn_h5_out, 'a', driver='mpio', comm=self.comm) as hfw:
        
        ## collectively write covariance,Ekz,Ef
        for scalar in scalars:
            dset = hfw[f'covariance/{scalar}']
            with dset.collective:
                dset[ry1:ry2] = covariance[scalar][:]
            dset = hfw[f'Ekz/{scalar}']
            with dset.collective:
                dset[ry1:ry2,:] = Ekz[scalar][:,:]
            dset = hfw[f'Ef/{scalar}']
            with dset.collective:
                dset[ry1:ry2,:] = Ef[scalar][:,:]
        
        ## collectively write 1D [y] avgs (Reynolds,Favre)
        for scalar in avg_Re.dtype.names:
            dset = hfw[f'avg/Re/{scalar}']
            with dset.collective:
                dset[ry1:ry2] = avg_Re[scalar][:]
        for scalar in avg_Fv.dtype.names:
            dset = hfw[f'avg/Fv/{scalar}']
            with dset.collective:
                dset[ry1:ry2] = avg_Fv[scalar][:]
    
    ## report file contents
    self.comm.Barrier()
    if (self.rank==0):
        even_print( os.path.basename(fn_h5_out) , f'{(os.path.getsize(fn_h5_out)/1024**2):0.1f} [MB]' )
        print(72*'-')
        with h5py.File(fn_h5_out,'r') as hfr:
            h5_print_contents(hfr)
    self.comm.Barrier()
    
    if verbose: print(72*'-')
    if verbose: print('total time : rgd.calc_turb_cospectrum_xpln() : %s'%format_time_string((timeit.default_timer() - t_start_func)))
    if verbose: print(72*'-')
    return
