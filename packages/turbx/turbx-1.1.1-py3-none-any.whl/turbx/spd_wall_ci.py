import os
import sys
import timeit
import traceback
from pathlib import Path, PurePosixPath

import h5py
import numpy as np
from tqdm import tqdm

from .confidence_interval import calc_var_bmbc, confidence_interval_unbiased
from .h5 import h5_print_contents
from .utils import even_print, format_time_string

# ======================================================================

def _calc_mean_uncertainty_BMBC(self, **kwargs):
    '''
    calculate the uncertainty of the mean using the
    "Batch Means and Batch Correlations" (BMBC) method outlined in
    §4 of https://doi.org/10.1016/j.jcp.2017.07.005
    '''
    
    if (self.rank==0):
        verbose = True
    else:
        verbose = False
    
    if verbose: print('\n'+'spd.calc_mean_uncertainty_BMBC()'+'\n'+72*'-')
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
    
    ## #n_threads = kwargs.get('n_threads',1)
    ## try:
    ##     n_threads = int(os.environ.get('OMP_NUM_THREADS'))
    ## except TypeError: ## not set
    ##     n_threads = os.cpu_count()
    
    fn_h5_out = kwargs.get('fn_h5_out',None) ## filename for output HDF5 (.h5) file
    
    confidence = kwargs.get('confidence',0.99)
    M          = kwargs.get('M',100) ## batch size
    
    if not isinstance(M, (int,np.int32,np.int64)):
        raise ValueError("'M' should be an int")
    if (M < 1):
        raise ValueError('M < 1')
    
    if (self.nt%M!=0):
        if verbose: print(f'nt = {self.nt:d}')
        if verbose: print(f'M = {M:d}')
        raise ValueError('nt%M!=0')
    
    if not isinstance(confidence, (float,np.float32,np.float64)):
        raise ValueError("'confidence' should be a float")
    if (confidence <= 0.) or (confidence >= 1.):
        raise ValueError('confidence should be between 0,1')
    
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
    if (fn_h5_out is None): ## automatically determine name
        fname_path = os.path.dirname(self.fname)
        fname_base = os.path.basename(self.fname)
        fname_root, fname_ext = os.path.splitext(fname_base)
        #fname_root = re.findall(r'io\S+_mpi_[0-9]+', fname_root)[0]
        fname_out_h5_base = fname_root+'_uncertainty_bmbc.h5'
        fn_h5_out = str(PurePosixPath(fname_path, fname_out_h5_base))
    if (Path(fn_h5_out).suffix != '.h5'):
        raise ValueError(f"fn_h5_out='{str(fn_h5_out)}' must end in .h5")
    if os.path.isfile(fn_h5_out):
        if (fn_h5_out == self.fname):
            raise ValueError(f"fn_h5_out='{str(fn_h5_out)}' cannot be same as input filename.")
    
    if verbose: even_print( 'fn_h5'     , self.fname )
    if verbose: even_print( 'fn_h5_out' , fn_h5_out  )
    if verbose: print(72*'-')
    if verbose: even_print( 'ni' , f'{self.ni:d}' )
    if verbose: even_print( 'nj' , f'{self.nj:d}' )
    if verbose: even_print( 'nt' , f'{self.nt:d}' )
    if verbose: print(72*'-')
    if verbose: even_print('n ranks', f'{self.n_ranks:d}' )
    #if verbose: even_print('n threads', f'{n_threads:d}' )
    if verbose: print(72*'-')
    if verbose: even_print('M', f'{M:d}' )
    if verbose: even_print('confidence level', f'{confidence:0.4f}' )
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
        print(72*'-')
    
    # ==============================================================
    # prepare buffers, maps, etc.
    # ==============================================================
    
    # n_lags = 2*nt-1
    
    data['M'] = M
    data['confidence'] = confidence
    
    ## HARDCODE
    scalars = [ 'tau_uy', 'u_tau', ]
    #scalars = [ 'tau_uy', ]
    
    K_full = nt // M
    
    if (K_full<10):
        raise ValueError('nt//M<10')
    
    #Ks = np.arange(3,K_full+1,dtype=np.int64)
    Ks = np.arange(10,K_full+1,dtype=np.int64)
    #Ks = np.copy(Ks[-1:]) ## debug, take last N (full time series)
    Ns = M * Ks
    #if verbose: print(Ns)
    nN = Ns.shape[0]
    
    ## report
    if verbose:
        even_print('n time durations (N)' , f'{nN:d}' )
        #print(72*'-')
    
    data['Ks'] = Ks
    data['Ns'] = Ns
    
    ## rank-local buffers
    data_mean  = np.zeros(shape=(nir,nN)   , dtype={'names':scalars , 'formats':[ np.float64 for sss in scalars ]})
    data_ci    = np.zeros(shape=(nir,nN,2) , dtype={'names':scalars , 'formats':[ np.float64 for sss in scalars ]})
    data_Nsig2 = np.zeros(shape=(nir,nN,)  , dtype={'names':scalars , 'formats':[ np.float64 for sss in scalars ]})
    #data_acor = np.zeros(shape=(nir,n_lags) , dtype={'names':scalars , 'formats':[ np.float64 for sss in scalars ]})
    
    # ==============================================================
    # main loop
    # ==============================================================
    
    if verbose:
        progress_bar = tqdm(
            total=len(scalars)*nir,
            ncols=100,
            desc='BMBC',
            leave=True,
            file=sys.stdout,
            mininterval=0.1,
            smoothing=0.,
            #bar_format="\033[B{l_bar}{bar}| {n}/{total} [{percentage:.1f}%] {elapsed}/{remaining}\033[A\n\b",
            bar_format="{l_bar}{bar}| {n}/{total} [{percentage:.1f}%] {elapsed}/{remaining}",
            ascii="░█",
            colour='#FF6600',
            )
    
    for scalar in scalars:
        
        dset = self[f'data/{scalar}']
        if verbose: tqdm.write(72*'-')
        
        for ii in range(ri1,ri2):
            
            iii = ii - ri1
            
            ## COLLECTIVE read
            self.comm.Barrier()
            t_start = timeit.default_timer()
            if self.usingmpi:
                with dset.collective:
                    dd = np.copy( dset[ii,:,:] )
            else:
                dd = np.copy( dset[ii,:,:] )
            self.comm.Barrier()
            t_delta = timeit.default_timer() - t_start
            data_gb = self.n_ranks * 1 * self.nj * self.nt * dset.dtype.itemsize / 1024**3
            if verbose:
                tqdm.write(even_print(f'read: {scalar}', '%0.3f [GB]  %0.3f [s]  %0.3f [GB/s]'%(data_gb,t_delta,(data_gb/t_delta)), s=True))
            
            ## assert shape [nz,nt]
            if ( dd.shape != (nj,nt) ):
                raise ValueError
                print(f'rank {self.rank:d}: shape violation')
                self.comm.Abort(1)
            
            ## cast to double
            dd = np.copy( dd.astype(np.float64) )
            
            ## re-dimensionalize
            if scalar in ['tau_uy','tau_vy','tau_wy',]:
                dd *= self.rho_inf * self.U_inf**2
            elif scalar in ['u_tau','v_tau','w_tau',]:
                dd *= self.U_inf
            elif scalar in ['T',]:
                dd *= self.T_inf
            elif scalar in ['rho',]:
                dd *= self.rho_inf
            elif scalar in ['p',]:
                dd *= self.rho_inf * self.U_inf**2
            else:
                raise ValueError(f"condition needed for redimensionalizing '{scalar}'")
            
            # ======================================================
            
            for iN,N in enumerate(Ns):
                
                ddN = np.copy( dd[:,:N] )
                
                ## mean in [z], leave [t]
                ddN = np.mean( ddN , axis=0 )
                
                ## assert shape
                if ( ddN.shape != (N,) ):
                    raise ValueError
                    print(f'rank {self.rank:d}: shape violation')
                    self.comm.Abort(1)
                
                d_mean = np.mean( ddN , dtype=np.float64 ) ## [t] mean, was already avged over [z]
                #dI     = np.copy( ddN - d_mean )
                
                data_mean[scalar][iii,iN] = d_mean
                
                try:
                    #Nsig2_ , S1ovS0_ = calc_var_bmbc( dI  , M=M )
                    Nsig2_ , S1ovS0_ = calc_var_bmbc( ddN , M=M )
                except Exception as ee:
                    print(f"error occurred on rank {self.rank:d}: {ee}")
                    traceback.print_exc()
                    #print('exception_traceback : \n'+traceback.format_exc().rstrip())
                    self.comm.Abort(1)
                
                data_Nsig2[scalar][iii,iN] = Nsig2_
                data_ci[scalar][iii,iN,:] = confidence_interval_unbiased(mean=d_mean, N_sigma2=Nsig2_, N=N, confidence=confidence )
            
            #self.comm.Barrier()
            if verbose: progress_bar.update()
            #break ## debug
        
        self.comm.Barrier() ## per scalar Barrier
    
    self.comm.Barrier() ## full loop Barrier
    if verbose:
        progress_bar.close()
        print(72*'-')
    
    # ==============================================================
    # write HDF5 (.h5) file
    # ==============================================================
    
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
            hfw.create_dataset( 'dims/x' , data=x ) ## [m]
            hfw.create_dataset( 'dims/z' , data=z ) ## [m]
            hfw.create_dataset( 'dims/t' , data=t ) ## [s]
            
            ## initialize datasets
            for scalar in scalars:
                hfw.create_dataset( f'mean/{scalar}'  , shape=(ni,nN,)   , dtype=np.float64, chunks=( min(nir,64),nN,  ) )
                hfw.create_dataset( f'Nsig2/{scalar}' , shape=(ni,nN,)   , dtype=np.float64, chunks=( min(nir,64),nN,  ) )
                hfw.create_dataset( f'ci/{scalar}'    , shape=(ni,nN,2,) , dtype=np.float64, chunks=( min(nir,64),nN,2 ) )
            
            ## independently write data
            hfw.create_dataset( 'Ks' , data=Ks )
            hfw.create_dataset( 'Ns' , data=Ns )
    
    self.comm.Barrier()
    
    with h5py.File(fn_h5_out, 'a', driver='mpio', comm=self.comm) as hfw:
        
        ## collectively write data
        for scalar in scalars:
            
            dset = hfw[f'mean/{scalar}']
            with dset.collective:
                dset[ri1:ri2,:] = data_mean[scalar][:,:]
            dset = hfw[f'Nsig2/{scalar}']
            with dset.collective:
                dset[ri1:ri2,:] = data_Nsig2[scalar][:,:]
            dset = hfw[f'ci/{scalar}']
            with dset.collective:
                dset[ri1:ri2,:,:] = data_ci[scalar][:,:,:]
    
    ## report file size
    if verbose:
        even_print( os.path.basename(fn_h5_out), f'{(os.path.getsize(fn_h5_out)/1024**2):0.2f} [MB]' )
        print(72*'-')
    
    ## report file contents
    self.comm.Barrier()
    if (self.rank==0):
        with h5py.File(fn_h5_out,'r') as hfr:
            h5_print_contents(hfr)
    self.comm.Barrier()
    
    if verbose: print(72*'-')
    if verbose: print('total time : spd.calc_mean_uncertainty_BMBC() : %s'%format_time_string((timeit.default_timer() - t_start_func)))
    if verbose: print(72*'-')
    return
