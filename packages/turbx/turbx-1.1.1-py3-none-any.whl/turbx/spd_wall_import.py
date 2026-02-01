import os
import sys
import timeit

import h5py
import numpy as np
from tqdm import tqdm

from .eas4 import eas4
from .gradient import gradient
from .h5 import h5_ds_force_allocate_chunks, h5_print_contents
from .utils import even_print, format_time_string

# ======================================================================

def _init_from_eas4_wall(self, fn_eas4, **kwargs):
    '''
    Initialize 'wall' SPD from an EAS4
    '''
    verbose = kwargs.get('verbose',True)
    if (self.rank!=0):
        verbose=False
    
    if verbose: print('\n'+'spd.init_from_eas4_wall()'+'\n'+72*'-')
    t_start_func = timeit.default_timer()
    
    #if (self.rank==0):
    with eas4(fn_eas4,'r',comm=self.comm,driver=self.driver) as hfr:
        
        if (hfr.x.ndim!=1):
            raise RuntimeError('hfr.x.ndim!=1')
        if (hfr.z.ndim!=1):
            raise RuntimeError('hfr.z.ndim!=1')
        
        ## Primary attributes
        ats = ['Ma','Re','Pr','kappa','R','p_inf','T_inf','S_Suth','mu_Suth_ref','T_Suth_ref',]
        for at in ats:
            self.attrs[at] = hfr.udef[at]
        
        ## Derived attributes
        ats = ['C_Suth','mu_inf','rho_inf','nu_inf','a_inf','U_inf','cp','cv','lchar','tchar','uchar','M_inf',]
        for at in ats:
            if at in hfr.attrs:
                self.attrs[at] = hfr.attrs[at]
        
        ## 3D polydata grid coordinates : shape (nx,nz,3)
        xyz = np.zeros((hfr.nx,hfr.nz,3), dtype=np.float64)
        xyz[:,:,0] = hfr.x[:,np.newaxis]
        xyz[:,:,1] = 0.
        xyz[:,:,2] = hfr.z[np.newaxis,:]
        
        self.create_dataset(
            name='dims/xyz',
            chunks=(1,hfr.nz,1), ## (x,z,3)
            #shape=(hfr.nx, hfr.nz, 3),
            #dtype=np.float64,
            data=xyz,
            )
        
        self.flush()
        xyz = None; del xyz
        
        ## 1D [x],[y],[z] vector
        self.create_dataset('dims/x', data=hfr.x, chunks=None)
        self.create_dataset('dims/z', data=hfr.z, chunks=None)
        self.create_dataset('dims/y', data=np.array([0.,],dtype=np.float64), chunks=None)
        
        ## Add attributes
        self.attrs['ni'] = hfr.nx
        self.attrs['nj'] = hfr.nz
        self.attrs['n_quads'] = ( hfr.nx - 1 ) * ( hfr.nz - 1 )
        self.attrs['n_pts'] = hfr.nx * hfr.nz
        #self.attrs['nt'] = hfr.nt
        self.attrs['nt'] = 0 ## overwritten later
    
    if self.usingmpi:
        self.comm.Barrier()
    
    self.get_header(verbose=True)
    if verbose: print(72*'-')
    
    if (self.rank==0):
        with h5py.File(self.fname,'r') as hf:
            h5_print_contents(hf)
    if self.usingmpi:
        self.comm.Barrier()
    
    ## Report
    if verbose:
        print(72*'-')
        even_print( os.path.basename(self.fname), f'{(os.path.getsize(self.fname)/1024**3):0.1f} [GB]')
    if verbose: print(72*'-')
    if verbose: print('total time : spd.init_from_eas4_wall() : %s'%format_time_string((timeit.default_timer() - t_start_func)))
    if verbose: print(72*'-')
    return

def _import_eas4_wall(self, fn_eas4_list, **kwargs):
    '''
    Directly import to 'wall' SPD file from EAS4s
    - only parallelize in [x]
    '''
    
    if (self.rank!=0):
        verbose=False
    else:
        verbose=True
    
    if verbose: print('\n'+'spd.import_eas4_wall()'+'\n'+72*'-')
    t_start_func = timeit.default_timer()
    
    ## dont actually copy over data, just initialize datasets with 0's
    init_dsets_only = kwargs.get('init_dsets_only',False)
    
    ## import from EAS4 as 3D unchunked datasets
    ## - have to convert to 4D later
    ## - necessary workaround for disk space with 'huge' datasets
    threeD   = kwargs.get('threeD',False)
    fn_h5_3D = kwargs.get('fn_h5_3D',None)
    fi_min   = kwargs.get('fi_min',0) ## minimum 'file' ID (for restarting MOVE)
    
    if fn_h5_3D is not None:
        if not os.path.isfile(fn_h5_3D):
            raise FileNotFoundError(fn_h5_3D)
    
    # if not self.usingmpi:
    #     if verbose: print('this function has not been implemented in non-MPI mode')
    #     sys.exit(1)
    
    # if not h5py.h5.get_config().mpi:
    #     if verbose: print('h5py was not compiled for parallel usage! exiting.')
    #     sys.exit(1)
    
    acc          = kwargs.get('acc',4)
    edge_stencil = kwargs.get('edge_stencil','full')
    chunks       = kwargs.get('chunks',None)
    
    if chunks is None:
        #chunks = (4, self.nj, 50) ## (x,z,t)
        chunks = (1,self.nj,1) ## (x,z,t) --> probably a bad default!
        print("WARNING! Not providing 'chunk' could result in very bad performance")
    if not isinstance(chunks,tuple):
        raise ValueError("'chunks' must be tuple")
    if len(chunks)!=3:
        raise ValueError("len(chunks)!=3")
    
    ## delete EAS4s after import --> DANGER!
    ## ... only actually deletes files if 'do_delete.txt' is present
    delete_after_import = kwargs.get('delete_after_import',False)
    
    ## check that the passed list of EAS4 files is OK
    if not isinstance(fn_eas4_list, list):
        raise ValueError("'fn_eas4_list' must be list")
    #if not hasattr(fn_eas4_list, '__iter__'):
    #    raise ValueError("'fn_eas4_list' must be iterable")
    for fn_eas4 in fn_eas4_list:
        if not os.path.isfile(fn_eas4):
            raise FileNotFoundError(fn_eas4)
    
    ## n ranks per direction
    rx = kwargs.get('rx',1)
    if (rx != self.n_ranks):
        raise AssertionError('rx != self.n_ranks')
    
    ## nx = ni
    if not hasattr(self,'ni'):
        raise ValueError('attribute ni not found.')
    else:
        self.nx = self.ni
    
    ## nz = nj
    if not hasattr(self,'nj'):
        raise ValueError('attribute nj not found.')
    else:
        self.nz = self.nj
    
    ## distribute in [x]
    if self.usingmpi:
        rxl_ = np.array_split(np.arange(self.nx,dtype=np.int64),min(rx,self.nx))
        rxl  = [[b[0],b[-1]+1] for b in rxl_ ]
        rx1, rx2 = rxl[self.rank]
        nxr = rx2 - rx1
    else:
        rx1,rx2 = 0,self.nx
        nxr = self.nx
    
    ## Get all time info & check
    # ==============================================================
    
    if len(fn_eas4_list) == 0:
        if not hasattr(self,'t') or not hasattr(self,'nt'):
            raise RuntimeError("if fn_eas4_list=[], then t should exist")
        nt = self.nt
        t  = np.copy(self.t)
    
    else:
        if (self.rank==0):
            t = np.array([], dtype=np.float64)
            for fn_eas4 in fn_eas4_list:
                with eas4(fn_eas4, 'r', verbose=False) as hf_eas4:
                    t_ = np.copy(hf_eas4.t)
                t = np.concatenate((t,t_))
        else:
            t = np.array([], dtype=np.float64) ## 't' must exist on all ranks before bcast
        
        if self.usingmpi:
            self.comm.Barrier()
            t = self.comm.bcast(t, root=0)
        nt = t.shape[0]
        self.nt = nt
        self.t = t
        assert self.t.dtype == np.float64, f'Array dtype is {str(t.dtype)}, expected np.float64'
    
    if len(fn_eas4_list) > 0:
        if verbose: even_print('n EAS4 files','%i'%len(fn_eas4_list))
        if verbose: even_print('nt all files','%i'%nt)
        if verbose: even_print('delete after import',str(delete_after_import))
    else:
        if verbose: even_print('nt',f'{nt:d}')
    if verbose: print(72*'-')
    
    # ==============================================================
    
    ## check [t] & Δt
    if (nt>1):
        
        ## check no zero distance elements
        if (np.diff(t).size - np.count_nonzero(np.diff(t))) != 0.:
            raise AssertionError('t arr has zero-distance elements')
        else:
            if verbose: even_print('check: Δt!=0','passed')
        
        ## check monotonically increasing
        if not np.all(np.diff(t) > 0.):
            raise AssertionError('t arr not monotonically increasing')
        else:
            if verbose: even_print('check: t mono increasing','passed')
        
        ## check constant Δt
        dt0 = np.diff(t)[0]
        if not np.all(np.isclose(np.diff(t), dt0, rtol=1e-3)):
            if (self.rank==0):
                print(np.diff(t))
            #raise AssertionError('t arr not uniformly spaced')
            if verbose:
                even_print('check: constant Δt','failed')
                print('WARNING: [t] not uniformly spaced!!')
        else:
            if verbose: even_print('check: constant Δt','passed')
        
        ## (over)write [t]
        if len(fn_eas4_list) > 0:
            if self.usingmpi: self.comm.Barrier()
            if 'dims/t' in self:
                del self['dims/t']
            self.create_dataset('dims/t', data=t, chunks=None, dtype=np.float64)
            self.attrs['nt'] = nt
            self.attrs['dt'] = dt0
            self.attrs['duration'] = dt0 * (nt - 1)
            self.flush()
            if self.usingmpi: self.comm.Barrier()
            if verbose: print(72*'-')
    
    else:
        return ## nothing to do
    
    # ==============================================================
    # Initialize datasets (harmless if they exist)
    # ==============================================================
    
    if not threeD: ## ...because '3D' mode doesnt require pre-initialization
        
        scalars = [
            'tau_uy','tau_vy','tau_wy',
            'u_tau','v_tau','w_tau',
            'T','mu','nu','rho','p',
            ]
        
        dtype = np.dtype(np.float32)
        shape = (self.nx, self.nz, self.nt)
        data_gb = np.prod(shape) * dtype.itemsize / 1024**3
        
        if verbose:
            progress_bar = tqdm(
                total=len(scalars),
                ncols=100,
                desc='initialize dsets',
                leave=True,
                file=sys.stdout,
                mininterval=0.1,
                smoothing=0.,
                #bar_format="\033[B{l_bar}{bar}| {n}/{total} [{percentage:.1f}%] {elapsed}/{remaining}\033[A\n\b",
                bar_format="{l_bar}{bar}| {n}/{total} [{percentage:.1f}%] {elapsed}/{remaining}",
                ascii="░█",
                colour='#FF6600',
                )
        
        ## Initialize output datasets
        for scalar in scalars:
            
            dsn = f'data/{scalar}'
            if dsn not in self:
                if self.usingmpi: self.comm.Barrier()
                t_start = timeit.default_timer()
                
                if verbose:
                    tqdm.write( even_print(f'initializing data/{scalar}', f'{str(shape)} / {data_gb:0.1f} [GB]', s=True) )
                
                dset = self.create_dataset(
                                        dsn,
                                        shape=shape,
                                        dtype=dtype,
                                        chunks=chunks,
                                        )
                
                ## write dummy data to dataset to ensure that it is truly initialized
                if not self.usingmpi:
                    h5_ds_force_allocate_chunks(dset,verbose=verbose) #,quick=True)
                
                if self.usingmpi: self.comm.Barrier()
                t_delta = timeit.default_timer() - t_start
                if verbose:
                    tqdm.write( even_print(f'initialize data/{scalar}', f'{data_gb:0.2f} [GB]  {t_delta:0.2f} [s]  {(data_gb/t_delta):0.3f} [GB/s]', s=True) )
                
                chunk_kb_ = np.prod(dset.chunks) * dset.dtype.itemsize / 1024. ## actual
                if verbose:
                    tqdm.write( even_print('chunk shape (x,z,t)', str(dset.chunks), s=True) )
                    tqdm.write( even_print('chunk size', f'{int(round(chunk_kb_)):d} [KB]', s=True) )
            
            if verbose: progress_bar.update()
        
        if self.usingmpi:
            self.comm.Barrier()
        if verbose:
            progress_bar.close()
            print(72*'-')
    
    # ==============================================================
    # Read,process,write (from EAS4)
    # ==============================================================
    
    if not init_dsets_only and fn_h5_3D is None:
        
        if verbose:
            progress_bar = tqdm(
                total=len(fn_eas4_list),
                ncols=100,
                desc='import',
                leave=True,
                file=sys.stdout,
                mininterval=0.1,
                smoothing=0.,
                #bar_format="\033[B{l_bar}{bar}| {n}/{total} [{percentage:.1f}%] {elapsed}/{remaining}\033[A\n\b",
                bar_format="{l_bar}{bar}| {n}/{total} [{percentage:.1f}%] {elapsed}/{remaining}",
                ascii="░█",
                colour='#FF6600',
                )
        
        tii = 0 ## timestep index counter full series
        
        for i_eas4,fn_eas4 in enumerate(fn_eas4_list):
            
            with eas4(fn_eas4, 'r', verbose=False, driver=self.driver, comm=self.comm) as hf_eas4:
                
                ## dimensional coordinates
                #x = np.copy( hf_eas4.x * hf_eas4.lchar )
                y = np.copy( hf_eas4.y * hf_eas4.lchar )
                #z = np.copy( hf_eas4.z * hf_eas4.lchar )
                
                nx = hf_eas4.nx
                ny = hf_eas4.ny
                nz = hf_eas4.nz
                nt = hf_eas4.nt ## OVERWRITING ABOVE!!!
                
                if verbose:
                    tqdm.write(even_print(os.path.basename(fn_eas4), f'{(os.path.getsize(fn_eas4)/1024**3):0.1f} [GB]', s=True))
                
                ## rank-local data read buffer for this EAS4
                scalars = ['rho','u','v','w','T','p']
                #formats = [ np.dtype(np.float32) for s in scalars ]
                formats = [ np.dtype(np.float64) for s in scalars ] ## do arithmetic in double
                data    = np.zeros(shape=(nxr,ny,nz,nt), dtype={'names':scalars, 'formats':formats})
                
                ## read (FULL file)
                self.comm.Barrier()
                t_start = timeit.default_timer()
                for ti in range(hf_eas4.nt): ## timesteps in EAS4
                    for scalar in scalars:
                        dset_path = f'Data/DOMAIN_000000/ts_{ti:06d}/par_{hf_eas4.scalar_n_map[scalar]:06d}'
                        dset = hf_eas4[dset_path]
                        with dset.collective:
                            if hf_eas4.dform==1:
                                data[scalar][:,:,:,ti] = dset[rx1:rx2,:,:]
                            elif hf_eas4.dform==2:
                                data[scalar][:,:,:,ti] = dset[:,:,rx1:rx2].T
                            else:
                                raise RuntimeError
                
                self.comm.Barrier()
                t_delta = timeit.default_timer() - t_start
                
                data_gb = os.path.getsize(fn_eas4)/1024**3
                if verbose:
                    #msg = even_print('read {os.path.basename(fn_eas4)}', f'{data_gb:0.2f} [GB]  {t_delta:0.2f} [s]  {(data_gb/t_delta):0.3f} [GB/s]', s=True)
                    msg = even_print('read', f'{data_gb:0.2f} [GB]  {t_delta:0.2f} [s]  {(data_gb/t_delta):0.3f} [GB/s]', s=True)
                    tqdm.write(msg)
                
                ## re-dimensionalize EAS4 data
                data['rho'][:,:,:,:] *= hf_eas4.rho_inf
                data['u'][:,:,:,:]   *= hf_eas4.U_inf
                data['v'][:,:,:,:]   *= hf_eas4.U_inf
                data['w'][:,:,:,:]   *= hf_eas4.U_inf
                data['T'][:,:,:,:]   *= hf_eas4.T_inf
                data['p'][:,:,:,:]   *= hf_eas4.rho_inf * hf_eas4.U_inf**2
                
                ## calculate μ and ν (dimensional)
                mu = np.zeros(shape=(nxr,ny,nz,nt), dtype=np.float64)
                nu = np.zeros(shape=(nxr,ny,nz,nt), dtype=np.float64)
                mu[:,:,:,:] = hf_eas4.mu_Suth_ref * ( data['T'][:,:,:,:] / hf_eas4.T_Suth_ref )**(3/2) * ( ( hf_eas4.T_Suth_ref + hf_eas4.S_Suth ) / ( data['T'][:,:,:,:] + hf_eas4.S_Suth ) )
                nu[:,:,:,:] = mu / data['rho'][:,:,:,:]
            
            # ==========================================================
            
            ## Dimensional wall strains
            ddy_u      = gradient( data['u'][:,:,:,:], y, axis=1, acc=acc, edge_stencil=edge_stencil, d=1)
            ddy_v      = gradient( data['v'][:,:,:,:], y, axis=1, acc=acc, edge_stencil=edge_stencil, d=1)
            ddy_w      = gradient( data['w'][:,:,:,:], y, axis=1, acc=acc, edge_stencil=edge_stencil, d=1)
            ddy_u_wall = np.copy( ddy_u[:,0,:,:] )
            ddy_v_wall = np.copy( ddy_v[:,0,:,:] )
            ddy_w_wall = np.copy( ddy_w[:,0,:,:] )
            
            if (ddy_u_wall.ndim!=3): ## (x,z,t)
                raise ValueError
            if (ddy_u_wall.shape!=(nxr,nz,nt)): ## (x,z,t)
                raise ValueError
            
            ## Dimensional wall quantities
            rho_wall = np.copy( data['rho'][:,0,:,:] )
            mu_wall  = np.copy( mu[:,0,:,:]          )
            nu_wall  = np.copy( nu[:,0,:,:]          )
            T_wall   = np.copy( data['T'][:,0,:,:]   )
            p_wall   = np.copy( data['p'][:,0,:,:]   )
            
            if (mu_wall.ndim!=3): ## (x,z,t)
                raise ValueError
            if (mu_wall.shape!=(nxr,nz,nt)): ## (x,z,t)
                raise ValueError
            
            if (rho_wall.ndim!=3): ## (x,z,t)
                raise ValueError
            if (rho_wall.shape!=(nxr,nz,nt)): ## (x,z,t)
                raise ValueError
            
            tau_uy = np.copy( mu_wall * ddy_u_wall ) ## INSTANTANEOUS τw
            tau_vy = np.copy( mu_wall * ddy_v_wall )
            tau_wy = np.copy( mu_wall * ddy_w_wall )
            
            u_tau = np.copy( np.sign(tau_uy) * np.sqrt( np.abs(tau_uy) / rho_wall ) ) ## INSTANTANEOUS uτ
            v_tau = np.copy( np.sign(tau_vy) * np.sqrt( np.abs(tau_vy) / rho_wall ) ) ## INSTANTANEOUS vτ
            w_tau = np.copy( np.sign(tau_wy) * np.sqrt( np.abs(tau_wy) / rho_wall ) ) ## INSTANTANEOUS wτ
            
            #grp      = self['data']
            #scalars  = list(grp.keys())
            scalars = [
                    'tau_uy','tau_vy','tau_wy',
                    'u_tau','v_tau','w_tau',
                    'T','mu','nu','rho','p',
                    ]
            
            ## 3D [scalar][x,z,t] numpy structured array
            ## rank-local data buffer for write
            formats  = [ np.dtype(np.float32) for s in scalars ] ## casting to single
            data4spd = np.zeros(shape=(nxr,hf_eas4.nz,hf_eas4.nt), dtype={'names':scalars, 'formats':formats})
            data4spd['tau_uy'][:,:,:] = tau_uy   / ( self.rho_inf * self.U_inf**2 )
            data4spd['tau_vy'][:,:,:] = tau_vy   / ( self.rho_inf * self.U_inf**2 )
            data4spd['tau_wy'][:,:,:] = tau_wy   / ( self.rho_inf * self.U_inf**2 )
            data4spd['T'][:,:,:]      = T_wall   / self.T_inf
            data4spd['rho'][:,:,:]    = rho_wall / self.rho_inf
            data4spd['p'][:,:,:]      = p_wall   / ( self.rho_inf * self.U_inf**2 )
            data4spd['mu'][:,:,:]     = mu_wall  / self.mu_inf
            data4spd['nu'][:,:,:]     = nu_wall  / self.nu_inf
            data4spd['u_tau'][:,:,:]  = u_tau    / self.U_inf
            data4spd['v_tau'][:,:,:]  = v_tau    / self.U_inf
            data4spd['w_tau'][:,:,:]  = w_tau    / self.U_inf
            
            tiA = tii
            tiB = tiA + nt
            tii += nt ## increment tii by this EAS4's nt
            
            ## write
            self.comm.Barrier()
            t_start = timeit.default_timer()
            
            if not threeD:
                
                #for scalar in data4spd.dtype.names:
                for scalar in scalars:
                    dset = self[f'data/{scalar}']
                    with dset.collective:
                        dset[rx1:rx2,:,tiA:tiB] = data4spd[scalar][:,:,:]
            
            else: ## Write as chunkless dset per-file
                
                for scalar in scalars:
                    dsn   = f'data/{i_eas4:d}/{scalar}'
                    shape = ( self.nx, self.nz, nt ) ## 'nt' here is from EAS4
                    dtype = np.dtype(np.float32)
                    
                    dset = self.create_dataset(
                                            dsn,
                                            shape=shape,
                                            dtype=dtype,
                                            chunks=None,
                                            )
                    
                    with dset.collective: ## do actual collective write
                        dset[rx1:rx2,:,:] = data4spd[scalar][:,:,:]
            
            self.comm.Barrier()
            t_delta = timeit.default_timer() - t_start
            
            ## Report write speed
            data_gb = self.n_ranks * data4spd.nbytes / 1024**3
            if verbose:
                msg = even_print('write', f'{data_gb:0.2f} [GB]  {t_delta:0.2f} [s]  {(data_gb/t_delta):0.3f} [GB/s]', s=True)
                tqdm.write(msg)
            
            ## Delete source file (under restrictive conditions)
            if delete_after_import:
                if os.path.isfile('do_delete.txt'):
                    if (self.rank==0):
                        tqdm.write(even_print('deleting', fn_eas4, s=True))
                        os.remove(fn_eas4)
                    self.comm.Barrier()
            
            if verbose: progress_bar.update()
        if verbose: progress_bar.close()
    
    # ==============================================================
    # MOVE from 3D, chunkless HDF5 file to CHUNKED SPD file
    # ==============================================================
    
    if not init_dsets_only and fn_h5_3D is not None:
        
        # ## report contents of 3D file
        # if (self.rank==0):
        #     with h5py.File(fn_h5_3D, 'r') as hfr:
        #         h5_print_contents(hfr)
        # if self.usingmpi:
        #     self.comm.Barrier()
        
        ## Get 'file indices' -- 'indices' are digits in 'data/%d/...' dset names
        if (self.rank==0):
            fi = []
            with h5py.File(fn_h5_3D, 'r') as hfr:
                gpd = hfr['data']
                fi_list = sorted([int(name) for name in gpd.keys() if name.isdigit()])
                nfi_actual = len([ fi for fi in fi_list if fi >= fi_min ]) ## n files to actually process
                fi = np.array(fi_list, dtype=np.int32)
        else:
            fi = np.array([], dtype=np.int32) ## 'fi' must exist on all ranks before bcast
        if self.usingmpi:
            self.comm.Barrier()
            fi = self.comm.bcast(fi, root=0)
        
        if fi.shape[0]==0:
            raise RuntimeError
        
        nx = self.nx
        #ny = self.ny ## doesnt exist
        nz = self.nz
        #nt = self.nt ## no!
        
        scalars = [
                'tau_uy','tau_vy','tau_wy',
                'u_tau','v_tau','w_tau',
                'T','mu','nu','rho','p',
                ]
        
        if verbose:
            progress_bar = tqdm(
                #total=fi.shape[0]*len(scalars),
                total=nfi_actual*len(scalars),
                ncols=100,
                desc='import',
                leave=True,
                file=sys.stdout,
                mininterval=1/24,
                smoothing=0.3,
                #bar_format="\033[B{l_bar}{bar}| {n}/{total} [{percentage:.1f}%] {elapsed}/{remaining}\033[A\n\b",
                bar_format="{l_bar}{bar}| {n}/{total} [{percentage:.1f}%] {elapsed}/{remaining}",
                ascii="░█",
                colour='#FF6600',
                )
        
        tii = 0 ## timestep index counter full series
        
        with h5py.File(fn_h5_3D, 'r', driver=self.driver, comm=self.comm) as hfr:
            for fii in fi:
                for scalar in scalars:
                    
                    ## dataset name & handle in HDF5 file composed of chunkless dsets
                    dsn  = f'data/{fii:d}/{scalar}'
                    dset = hfr[dsn]
                    nt   = dset.shape[2] ## nt of corresponding chunkless dset (EAS4)
                    
                    ## time range for this EAS4 data
                    tiA = tii
                    tiB = tiA + nt
                    #if verbose:
                    #    tqdm.write(f'tiA={tiA:d},tiB={tiB:d}')
                    
                    if fii >= fi_min: ## do read / write
                        
                        data_gb = nx * nz * nt * dset.dtype.itemsize / 1024**3
                        
                        ## COLLECTIVE read
                        if self.usingmpi: self.comm.Barrier()
                        t_start = timeit.default_timer()
                        if self.usingmpi:
                            with dset.collective:
                                dd = np.copy( dset[rx1:rx2,:,:] )
                        else:
                            dd = np.copy( dset[()] )
                        if self.usingmpi: self.comm.Barrier()
                        t_delta = timeit.default_timer() - t_start
                        
                        if verbose:
                            tqdm.write(even_print(f'read: {fii:d}/{scalar}', '%0.3f [GB]  %0.3f [s]  %0.3f [GB/s]'%(data_gb,t_delta,(data_gb/t_delta)), s=True))
                        
                        ## assert shape
                        if ( dd.shape != (nxr,nz,nt) ):
                            print(f'rank {self.rank:d}: shape violation')
                            if self.usingmpi: self.comm.Abort(1)
                            raise ValueError
                        
                        ## dataset name & handle in SPD file
                        dsn  = f'data/{scalar}'
                        dset = self[dsn]
                        
                        ## COLLECTIVE write
                        if self.usingmpi: self.comm.Barrier()
                        t_start = timeit.default_timer()
                        if self.usingmpi:
                            with dset.collective:
                                dset[rx1:rx2,:,tiA:tiB] = dd[:,:,:]
                        else:
                            dset[:,:,tiA:tiB] = dd[:,:,:]
                        if self.usingmpi: self.comm.Barrier()
                        t_delta = timeit.default_timer() - t_start
                        
                        if verbose:
                            tqdm.write(even_print(f'write: data/{scalar}', '%0.3f [GB]  %0.3f [s]  %0.3f [GB/s]'%(data_gb,t_delta,(data_gb/t_delta)), s=True))
                        if verbose:
                            progress_bar.update()
                    
                    if os.path.isfile('stop.txt'):
                        break
                
                tii += nt ## increment tii by this EAS4's nt
                
                if os.path.isfile('stop.txt'):
                    break
            
            if verbose:
                progress_bar.close()
    
    ## Report file
    if self.usingmpi:
        self.comm.Barrier()
    if verbose:
        print(72*'-')
        even_print( os.path.basename(self.fname), f'{(os.path.getsize(self.fname)/1024**3):0.1f} [GB]')
    if verbose: print(72*'-')
    if verbose: print('total time : spd.import_eas4_wall() : %s'%format_time_string((timeit.default_timer() - t_start_func)))
    if verbose: print(72*'-')
    return
