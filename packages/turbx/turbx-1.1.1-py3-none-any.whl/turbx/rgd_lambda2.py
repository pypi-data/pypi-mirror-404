import math
import os
import sys
import timeit

import numpy as np
import psutil
from tqdm import tqdm

from .gradient import gradient
from .h5 import h5_chunk_sizer, h5_ds_force_allocate_chunks
from .utils import even_print, format_time_string

# ======================================================================

def _calc_lambda2(self, **kwargs):
    '''
    Calculate λ₂ & Q
    Jeong & Hussain (1996) : https://doi.org/10.1017/S0022112095000462
    '''
    
    if (self.rank==0):
        verbose = True
    else:
        verbose = False
    
    rx = kwargs.get('rx',1)
    ry = kwargs.get('ry',1)
    rz = kwargs.get('rz',1)
    
    save_Q       = kwargs.get('save_Q',True)
    save_lambda2 = kwargs.get('save_lambda2',True)
    
    acc          = kwargs.get('acc',4)
    edge_stencil = kwargs.get('edge_stencil','half')
    
    chunk_kb         = kwargs.get('chunk_kb',4*1024) ## h5 chunk size: default 4 [MB]
    chunk_constraint = kwargs.get('chunk_constraint',(1,None,None,None)) ## the 'constraint' parameter for sizing h5 chunks
    chunk_base       = kwargs.get('chunk_base',2)
    
    d = 1 ## derivative order
    stencil_npts = 2*math.floor((d+1)/2) - 1 + acc
    
    if ((stencil_npts-1)%2 != 0):
        raise AssertionError
    
    stencil_npts_one_side = int( (stencil_npts-1)/2 )
    
    # ===
    
    if verbose: print('\n'+'turbx.rgd.calc_lambda2()'+'\n'+72*'-')
    t_start_func = timeit.default_timer()
    
    ## checks
    if all([(save_Q is False),(save_lambda2 is False)]):
        raise AssertionError('neither λ-2 nor Q set to be solved')
    if not (self.open_mode=='a') or (self.open_mode=='w') or (self.open_mode=='r+'):
        raise ValueError('not able to write to hdf5 file')
    if 'data/u' not in self:
        raise ValueError('data/u not in hdf5')
    if 'data/v' not in self:
        raise ValueError('data/v not in hdf5')
    if 'data/w' not in self:
        raise ValueError('data/w not in hdf5')
    
    if (rx*ry*rz != self.n_ranks):
        raise AssertionError('rx*ry*rz != self.n_ranks')
    if (rx>self.nx):
        raise AssertionError('rx>self.nx')
    if (ry>self.ny):
        raise AssertionError('ry>self.ny')
    if (rz>self.nz):
        raise AssertionError('rz>self.nz')
    
    if verbose: even_print('save_Q','%s'%save_Q)
    if verbose: even_print('save_lambda2','%s'%save_lambda2)
    if verbose: even_print('rx','%i'%rx)
    if verbose: even_print('ry','%i'%ry)
    if verbose: even_print('rz','%i'%rz)
    if verbose: print(72*'-')
    
    #t_read = 0.
    #t_write = 0.
    #data_gb_read = 0.
    #data_gb_write = 0.
    #t_q_crit = 0.
    #t_l2     = 0.
    
    ## get size of infile
    fsize = os.path.getsize(self.fname)/1024**3
    if verbose: even_print(os.path.basename(self.fname),'%0.1f [GB]'%fsize)
    if verbose: even_print('nx','%i'%self.nx)
    if verbose: even_print('ny','%i'%self.ny)
    if verbose: even_print('nz','%i'%self.nz)
    if verbose: even_print('ngp','%0.1f [M]'%(self.ngp/1e6,))
    if verbose: print(72*'-')
    
    ## report memory
    mem_total_gb = psutil.virtual_memory().total/1024**3
    mem_avail_gb = psutil.virtual_memory().available/1024**3
    mem_free_gb  = psutil.virtual_memory().free/1024**3
    if verbose: even_print('mem total', '%0.1f [GB]'%mem_total_gb)
    if verbose: even_print('mem available', '%0.1f [GB]'%mem_avail_gb)
    if verbose: even_print('mem free', '%0.1f [GB]'%mem_free_gb)
    if verbose: print(72*'-')
    
    # === The 'standard' non-abutting / non-overlapping index split
    
    if self.usingmpi:
        
        comm4d = self.comm.Create_cart(dims=[rx,ry,rz], periods=[False,False,False], reorder=False)
        t4d = comm4d.Get_coords(self.rank)
        
        rxl_ = np.array_split(np.arange(self.nx,dtype=np.int64),min(rx,self.nx))
        ryl_ = np.array_split(np.arange(self.ny,dtype=np.int64),min(ry,self.ny))
        rzl_ = np.array_split(np.arange(self.nz,dtype=np.int64),min(rz,self.nz))
        #rtl_ = np.array_split(np.arange(self.nt,dtype=np.int64),min(rt,self.nt))
        
        rxl = [[b[0],b[-1]+1] for b in rxl_ ]
        ryl = [[b[0],b[-1]+1] for b in ryl_ ]
        rzl = [[b[0],b[-1]+1] for b in rzl_ ]
        #rtl = [[b[0],b[-1]+1] for b in rtl_ ]
        
        rx1, rx2 = rxl[t4d[0]]; nxr = rx2 - rx1
        ry1, ry2 = ryl[t4d[1]]; nyr = ry2 - ry1
        rz1, rz2 = rzl[t4d[2]]; nzr = rz2 - rz1
        #rt1, rt2 = rtl[t4d[3]]; ntr = rt2 - rt1
    
    else:
        
        nxr = self.nx
        nyr = self.ny
        nzr = self.nz
        #ntr = self.nt
    
    ## Check rank / grid distribution
    if self.usingmpi and False:
        for ri in range(self.n_ranks):
            self.comm.Barrier()
            if (self.rank == ri):
                print('rank %04d : rx1=%i rx2=%i ry1=%i ry2=%i rz1=%i rz2=%i'%(self.rank, rx1,rx2, ry1,ry2, rz1,rz2))
                sys.stdout.flush()
    
    if self.usingmpi: self.comm.Barrier()
    
    # === Extend the rank ranges (spatial range overlap)
    
    if self.usingmpi:
        
        n_overlap = stencil_npts_one_side + 3
        
        xA = 0
        xB = nxr
        yA = 0
        yB = nyr
        zA = 0
        zB = nzr
        
        ## backup non-overlapped bounds
        rx1_orig, rx2_orig = rx1, rx2
        ry1_orig, ry2_orig = ry1, ry2
        rz1_orig, rz2_orig = rz1, rz2
        
        ## overlap in [x]
        if (t4d[0]!=0):
            rx1, rx2 = rx1-n_overlap, rx2
            xA += n_overlap
            xB += n_overlap
        if (t4d[0]!=rx-1):
            rx1, rx2 = rx1, rx2+n_overlap
        
        ## overlap in [y]
        if (t4d[1]!=0):
            ry1, ry2 = ry1-n_overlap, ry2
            yA += n_overlap
            yB += n_overlap
        if (t4d[1]!=ry-1):
            ry1, ry2 = ry1, ry2+n_overlap
        
        ## overlap in [z]
        if (t4d[2]!=0):
            rz1, rz2 = rz1-n_overlap, rz2
            zA += n_overlap
            zB += n_overlap
        if (t4d[2]!=rz-1):
            rz1, rz2 = rz1, rz2+n_overlap
        
        ## update (rank local) nx,ny,nz
        nxr = rx2 - rx1
        nyr = ry2 - ry1
        nzr = rz2 - rz1
    
    ## Check rank / grid distribution
    if self.usingmpi and False:
        for ri in range(self.n_ranks):
            self.comm.Barrier()
            if (self.rank == ri):
                print('rank %04d : rx1=%i rx2=%i ry1=%i ry2=%i rz1=%i rz2=%i'%(self.rank, rx1,rx2, ry1,ry2, rz1,rz2))
                sys.stdout.flush()
    
    if self.usingmpi: self.comm.Barrier()
    
    # ===
    
    dtype = self['data/u'].dtype
    #itemsize = dtype.itemsize
    float_bytes = dtype.itemsize
    
    data_gb = float_bytes*self.nx*self.ny*self.nz*self.nt / 1024**3
    shape  = (self.nt,self.nz,self.ny,self.nx)
    chunks = h5_chunk_sizer(nxi=shape, constraint=chunk_constraint, size_kb=chunk_kb, base=chunk_base, itemsize=float_bytes)
    
    # === Initialize 4D arrays in HDF5
    
    if save_lambda2:
        
        self.scalars_dtypes_dict['lambda2'] = dtype
        
        if verbose:
            even_print('initializing data/lambda2','%0.2f [GB]'%(data_gb,))
        if ('data/lambda2' in self):
            del self['data/lambda2']
        dset = self.create_dataset(
                            'data/lambda2', 
                            shape=shape, 
                            dtype=dtype,
                            chunks=chunks,
                            )
        
        if self.usingmpi: self.comm.Barrier()
        
        ## write dummy data
        if self.rank==0:
            h5_ds_force_allocate_chunks(dset,verbose=verbose)
        
        if self.usingmpi: self.comm.Barrier()
        
        chunk_kb_ = np.prod(dset.chunks)*float_bytes / 1024. ## actual
        if verbose:
            even_print('chunk shape (t,z,y,x)','%s'%str(dset.chunks))
            even_print('chunk size','%i [KB]'%int(round(chunk_kb_)))
    
    if save_Q:
        
        self.scalars_dtypes_dict['Q'] = dtype
        
        if verbose:
            even_print('initializing data/Q','%0.2f [GB]'%(data_gb,))
        if ('data/Q' in self):
            del self['data/Q']
        dset = self.create_dataset(
                            'data/Q', 
                            shape=shape, 
                            dtype=dtype,
                            chunks=chunks,
                            )
        
        if self.usingmpi: self.comm.Barrier()
        
        ## write dummy data
        if self.rank==0:
            h5_ds_force_allocate_chunks(dset,verbose=verbose)
        
        if self.usingmpi: self.comm.Barrier()
        
        chunk_kb_ = np.prod(dset.chunks)*float_bytes / 1024. ## actual
        if verbose:
            even_print('chunk shape (t,z,y,x)', str(dset.chunks))
            even_print('chunk size', f'{int(round(chunk_kb_)):d} [KB]')
    
    if verbose: print(72*'-')
    
    # ===
    
    if verbose:
        progress_bar = tqdm(total=self.nt, ncols=100, desc='calc λ2', leave=False, file=sys.stdout)
    
    for ti in self.ti:
        
        # === Read u,v,w
        
        dset = self['data/u']
        dtype = dset.dtype
        float_bytes = dtype.itemsize
        if self.usingmpi: self.comm.Barrier()
        t_start = timeit.default_timer()
        if self.usingmpi:
            with dset.collective:
                u_ = dset[ti,rz1:rz2,ry1:ry2,rx1:rx2].T
        else:
            u_ = dset[ti,:,:,:].T
        if self.usingmpi: self.comm.Barrier()
        t_delta = timeit.default_timer() - t_start
        data_gb = float_bytes * self.nx * self.ny * self.nz * 1 / 1024**3
        if verbose:
            tqdm.write( even_print('read u', '%0.3f [GB]  %0.3f [s]  %0.3f [GB/s]'%(data_gb,t_delta,(data_gb/t_delta)), s=True ) )
        
        dset = self['data/v']
        dtype = dset.dtype
        float_bytes = dtype.itemsize
        if self.usingmpi: self.comm.Barrier()
        t_start = timeit.default_timer()
        if self.usingmpi:
            with dset.collective:
                v_ = dset[ti,rz1:rz2,ry1:ry2,rx1:rx2].T
        else:
            v_ = dset[ti,:,:,:].T
        if self.usingmpi: self.comm.Barrier()
        t_delta = timeit.default_timer() - t_start
        data_gb = float_bytes * self.nx * self.ny * self.nz * 1 / 1024**3
        if verbose:
            tqdm.write( even_print('read v', '%0.3f [GB]  %0.3f [s]  %0.3f [GB/s]'%(data_gb,t_delta,(data_gb/t_delta)), s=True ) )
        
        dset = self['data/w']
        dtype = dset.dtype
        float_bytes = dtype.itemsize
        if self.usingmpi: self.comm.Barrier()
        t_start = timeit.default_timer()
        if self.usingmpi:
            with dset.collective:
                w_ = dset[ti,rz1:rz2,ry1:ry2,rx1:rx2].T
        else:
            w_ = dset[ti,:,:,:].T
        if self.usingmpi: self.comm.Barrier()
        t_delta = timeit.default_timer() - t_start
        data_gb = float_bytes * self.nx * self.ny * self.nz * 1 / 1024**3
        if verbose:
            tqdm.write( even_print('read w', '%0.3f [GB]  %0.3f [s]  %0.3f [GB/s]'%(data_gb,t_delta,(data_gb/t_delta)), s=True ) )
        
        # ===
        
        if self.usingmpi:
            x_ = np.copy(self.x[rx1:rx2])
            y_ = np.copy(self.y[ry1:ry2])
            z_ = np.copy(self.z[rz1:rz2])
        else:
            x_ = np.copy(self.x)
            y_ = np.copy(self.y)
            z_ = np.copy(self.z)
        
        # === ∂(u)/∂(x,y,z)
        
        ddx_u = gradient(u_, x_, axis=0, acc=acc, edge_stencil=edge_stencil, d=1)
        ddy_u = gradient(u_, y_, axis=1, acc=acc, edge_stencil=edge_stencil, d=1)
        ddz_u = gradient(u_, z_, axis=2, acc=acc, edge_stencil=edge_stencil, d=1)
        
        # === ∂(v)/∂(x,y,z)
        
        ddx_v = gradient(v_, x_, axis=0, acc=acc, edge_stencil=edge_stencil, d=1)
        ddy_v = gradient(v_, y_, axis=1, acc=acc, edge_stencil=edge_stencil, d=1)
        ddz_v = gradient(v_, z_, axis=2, acc=acc, edge_stencil=edge_stencil, d=1)
        
        # === ∂(w)/∂(x,y,z)
        
        ddx_w = gradient(w_, x_, axis=0, acc=acc, edge_stencil=edge_stencil, d=1)
        ddy_w = gradient(w_, y_, axis=1, acc=acc, edge_stencil=edge_stencil, d=1)
        ddz_w = gradient(w_, z_, axis=2, acc=acc, edge_stencil=edge_stencil, d=1)
        
        ## Free memory
        u_ = None; del u_
        v_ = None; del v_
        w_ = None; del w_
        
        strain = np.copy( np.stack((np.stack((ddx_u, ddy_u, ddz_u), axis=3),
                                    np.stack((ddx_v, ddy_v, ddz_v), axis=3),
                                    np.stack((ddx_w, ddy_w, ddz_w), axis=3)), axis=4) )
        
        t_delta = timeit.default_timer() - t_start
        if verbose: tqdm.write( even_print('get strain ∂(u,v,v)/∂(x,y,z)' , '%0.3f [s]'%(t_delta,), s=True) )
        
        ## Free memory
        ddx_u = None; del ddx_u
        ddy_u = None; del ddy_u
        ddz_u = None; del ddz_u
        ddx_v = None; del ddx_v
        ddy_v = None; del ddy_v
        ddz_v = None; del ddz_v
        ddx_w = None; del ddx_w
        ddy_w = None; del ddy_w
        ddz_w = None; del ddz_w
        
        # === Get the rate-of-strain & vorticity tensors
        
        S = np.copy( 0.5*(strain + np.transpose(strain, axes=(0,1,2,4,3))) ) ## strain rate tensor (symmetric)
        Ω = np.copy( 0.5*(strain - np.transpose(strain, axes=(0,1,2,4,3))) ) ## rotation rate tensor (anti-symmetric)
        # np.testing.assert_allclose(S+Ω, strain, atol=1.e-6)
        
        ## Free memory
        strain = None; del strain
        
        # === Q : second invariant of characteristics equation: λ³ + Pλ² + Qλ + R = 0
        
        if save_Q:
            
            t_start = timeit.default_timer()
            
            O_norm  = np.linalg.norm(Ω, ord='fro', axis=(3,4)) ## Frobenius norm
            S_norm  = np.linalg.norm(S, ord='fro', axis=(3,4))
            Q       = 0.5*(O_norm**2 - S_norm**2)
            
            t_delta = timeit.default_timer() - t_start
            if verbose: tqdm.write(even_print('calc Q','%s'%format_time_string(t_delta), s=True))
            
            dset = self['data/Q']
            dtype = dset.dtype
            float_bytes = dtype.itemsize
            if self.usingmpi: self.comm.Barrier()
            t_start = timeit.default_timer()
            if self.usingmpi:
                with dset.collective:
                    dset[ti,rz1_orig:rz2_orig,ry1_orig:ry2_orig,rx1_orig:rx2_orig] = Q[xA:xB,yA:yB,zA:zB].T
            else:
                dset[ti,:,:,:] = Q.T
            if self.usingmpi: self.comm.Barrier()
            t_delta = timeit.default_timer() - t_start
            data_gb = float_bytes * self.nx * self.ny * self.nz / 1024**3
            
            if verbose: tqdm.write(even_print('write Q','%0.3f [GB]  %0.3f [s]  %0.3f [GB/s]'%(data_gb,t_delta,(data_gb/t_delta)), s=True))
            
            # # === second invariant : Q --> an equivalent formulation using eigenvalues (but much slower)
            # if False:
            #     Q_bak = np.copy(Q)
            #     t_start = timeit.default_timer()
            #     eigvals = np.linalg.eigvals(strain)
            #     P       = -1*np.sum(eigvals, axis=-1) ## first invariant : P
            #     SijSji  = np.einsum('xyzij,xyzji->xyz', S, S)
            #     OijOji  = np.einsum('xyzij,xyzji->xyz', Ω, Ω)
            #     Q       = 0.5*(P**2 - SijSji - OijOji)
            #     t_delta = timeit.default_timer() - t_start
            #     if verbose: tqdm.write(even_print('calc Q','%s'%format_time_string(t_delta), s=True))
            #     np.testing.assert_allclose(Q.imag, np.zeros_like(Q.imag, dtype=np.float32), atol=1e-6)
            #     Q = np.copy(Q.real)
            #     np.testing.assert_allclose(Q, Q_bak, rtol=1e-2, atol=1e-5)
            
            ## Free memory
            O_norm = None; del O_norm
            S_norm = None; del S_norm
            Q = None; del Q
        
        # === λ₂
        
        if save_lambda2:
            
            t_start = timeit.default_timer()
            
            # === S² and Ω²
            SikSkj = np.einsum('xyzik,xyzkj->xyzij', S, S)
            OikOkj = np.einsum('xyzik,xyzkj->xyzij', Ω, Ω)
            #np.testing.assert_allclose(np.matmul(S,S), SikSkj, atol=1e-6)
            #np.testing.assert_allclose(np.matmul(Ω,Ω), OikOkj, atol=1e-6)
            
            ## Free memory
            S = None; del S
            Ω = None; del Ω
            
            # === Eigenvalues of (S²+Ω²) --> a real symmetric (Hermitian) matrix
            eigvals            = np.linalg.eigvalsh(SikSkj+OikOkj, UPLO='L')
            #eigvals_sort_order = np.argsort(np.abs(eigvals), axis=3) ## sort order of λ --> magnitude (wrong)
            eigvals_sort_order = np.argsort(eigvals, axis=3) ## sort order of λ
            eigvals_sorted     = np.take_along_axis(eigvals, eigvals_sort_order, axis=3) ## do λ sort
            lambda2            = np.squeeze(eigvals_sorted[:,:,:,1]) ## λ2 is the second eigenvalue (index=1)
            t_delta            = timeit.default_timer() - t_start
            
            if verbose: tqdm.write(even_print('calc λ2','%s'%format_time_string(t_delta), s=True))
            
            dset = self['data/lambda2']
            dtype = dset.dtype
            float_bytes = dtype.itemsize
            if self.usingmpi: self.comm.Barrier()
            t_start = timeit.default_timer()
            if self.usingmpi:
                with dset.collective:
                    dset[ti,rz1_orig:rz2_orig,ry1_orig:ry2_orig,rx1_orig:rx2_orig] = lambda2[xA:xB,yA:yB,zA:zB].T
            else:
                dset[ti,:,:,:] = lambda2.T
            if self.usingmpi: self.comm.Barrier()
            t_delta = timeit.default_timer() - t_start
            data_gb = float_bytes * self.nx * self.ny * self.nz / 1024**3
            
            if verbose: tqdm.write(even_print('write λ2','%0.3f [GB]  %0.3f [s]  %0.3f [GB/s]'%(data_gb,t_delta,(data_gb/t_delta)), s=True))
            
            ## Free memory
            lambda2 = None; del lambda2
            eigvals = None; del eigvals
            eigvals_sort_order = None; del eigvals_sort_order
            eigvals_sorted = None; del eigvals_sorted
        
        if verbose: progress_bar.update()
        if verbose and (ti<self.nt-1): tqdm.write( '---' )
    if verbose: progress_bar.close()
    if verbose: print(72*'-')
    
    # ===
    
    self.get_header(verbose=False)
    if verbose: even_print(self.fname, '%0.2f [GB]'%(os.path.getsize(self.fname)/1024**3))
    
    if verbose: print(72*'-')
    if verbose: print('total time : turbx.rgd.calc_lambda2() : %s'%format_time_string((timeit.default_timer() - t_start_func)))
    if verbose: print(72*'-')
    return
