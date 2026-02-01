import os
import sys
import timeit

import numpy as np
from tqdm import tqdm

from .h5 import h5_chunk_sizer
from .utils import even_print, format_time_string

# ======================================================================

def _populate_abc_flow(self, **kwargs):
    '''
    Populate (unsteady) ABC flow dummy data
    -----
    https://en.wikipedia.org/wiki/Arnold%E2%80%93Beltrami%E2%80%93Childress_flow
    '''
    
    if (self.rank==0):
        verbose = True
    else:
        verbose = False
    
    if verbose: print('\n'+'rgd.populate_abc_flow()'+'\n'+72*'-')
    t_start_func = timeit.default_timer()
    
    rx = kwargs.get('rx',1)
    ry = kwargs.get('ry',1)
    rz = kwargs.get('rz',1)
    ##
    chunk_kb = kwargs.get('chunk_kb',4*1024) ## 4 [MB]
    
    self.nx = nx = kwargs.get('nx',100)
    self.ny = ny = kwargs.get('ny',100)
    self.nz = nz = kwargs.get('nz',100)
    self.nt = nt = kwargs.get('nt',100)
    
    data_gb = 3 * 4*nx*ny*nz*nt / 1024.**3
    if verbose: even_print(self.fname, '%0.2f [GB]'%(data_gb,))
    
    self.x = x = np.linspace(0., 2*np.pi, nx, dtype=np.float32)
    self.y = y = np.linspace(0., 2*np.pi, ny, dtype=np.float32)
    self.z = z = np.linspace(0., 2*np.pi, nz, dtype=np.float32)
    #self.t = t = np.linspace(0., 10.,     nt, dtype=np.float32)
    self.t = t = 0.1 * np.arange(nt, dtype=np.float32)
    
    if (rx*ry*rz != self.n_ranks):
        raise AssertionError('rx*ry*rz != self.n_ranks')
    
    # ===
    
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
    
    rx1, rx2 = rxl[t4d[0]] #; nxr = rx2 - rx1
    ry1, ry2 = ryl[t4d[1]] #; nyr = ry2 - ry1
    rz1, rz2 = rzl[t4d[2]] #; nzr = rz2 - rz1
    #rt1, rt2 = rtl[t4d[3]]; ntr = rt2 - rt1
    
    ## per-rank dim range
    xr = x[rx1:rx2]
    yr = y[ry1:ry2]
    zr = z[rz1:rz2]
    #tr = t[rt1:rt2]
    tr = np.copy(t)
    
    ## write dims
    self.create_dataset('dims/x', data=x)
    self.create_dataset('dims/y', data=y)
    self.create_dataset('dims/z', data=z)
    self.create_dataset('dims/t', data=t)
    
    shape  = (self.nt,self.nz,self.ny,self.nx)
    chunks = h5_chunk_sizer(nxi=shape, constraint=(1,None,None,None), size_kb=chunk_kb, base=4, itemsize=4)
    
    ## initialize
    data_gb = 4*nx*ny*nz*nt / 1024.**3
    for scalar in ['u','v','w']:
        if ('data/%s'%scalar in self):
            del self['data/%s'%scalar]
        if verbose:
            even_print('initializing data/%s'%(scalar,),'%0.2f [GB]'%(data_gb,))
        dset = self.create_dataset('data/%s'%scalar, 
                                    shape=shape,
                                    dtype=np.float32,
                                    chunks=chunks,
                                    )
        
        chunk_kb_ = np.prod(dset.chunks)*4 / 1024. ## actual
        if verbose:
            even_print('chunk shape (t,z,y,x)','%s'%str(dset.chunks))
            even_print('chunk size','%i [KB]'%int(round(chunk_kb_)))
    
    if verbose: print(72*'-')
    
    # === make 4D ABC flow data
    
    t_start = timeit.default_timer()
    A = np.sqrt(3)
    B = np.sqrt(2)
    C = 1.
    na = np.newaxis
    u = (A + 0.5 * tr[na,na,na,:] * np.sin(np.pi*tr[na,na,na,:])) * np.sin(zr[na,na,:,na]) + \
        B * np.cos(yr[na,:,na,na]) + \
        0.*xr[:,na,na,na]
    v = B * np.sin(xr[:,na,na,na]) + \
        C * np.cos(zr[na,na,:,na]) + \
        0.*yr[na,:,na,na] + \
        0.*tr[na,na,na,:]
    w = C * np.sin(yr[na,:,na,na]) + \
        (A + 0.5 * tr[na,na,na,:] * np.sin(np.pi*tr[na,na,na,:])) * np.cos(xr[:,na,na,na]) + \
        0.*zr[na,na,:,na]
    
    t_delta = timeit.default_timer() - t_start
    if verbose: even_print('calc flow','%0.3f [s]'%(t_delta,))
    
    # ===
    
    data_gb = 4*nx*ny*nz*nt / 1024.**3
    
    self.comm.Barrier()
    t_start = timeit.default_timer()
    ds = self['data/u']
    with ds.collective:
        ds[:,rz1:rz2,ry1:ry2,rx1:rx2] = u.T
    self.comm.Barrier()
    t_delta = timeit.default_timer() - t_start
    if verbose: even_print('write: u','%0.2f [GB]  %0.3f [s]  %0.3f [GB/s]'%(data_gb,t_delta,(data_gb/t_delta)))
    
    self.comm.Barrier()
    t_start = timeit.default_timer()
    ds = self['data/v']
    with ds.collective:
        ds[:,rz1:rz2,ry1:ry2,rx1:rx2] = v.T
    self.comm.Barrier()
    t_delta = timeit.default_timer() - t_start
    if verbose: even_print('write: v','%0.2f [GB]  %0.3f [s]  %0.3f [GB/s]'%(data_gb,t_delta,(data_gb/t_delta)))
    
    self.comm.Barrier()
    t_start = timeit.default_timer()
    ds = self['data/w']
    with ds.collective:
        ds[:,rz1:rz2,ry1:ry2,rx1:rx2] = w.T
    self.comm.Barrier()
    t_delta = timeit.default_timer() - t_start
    if verbose: even_print('write: w','%0.2f [GB]  %0.3f [s]  %0.3f [GB/s]'%(data_gb,t_delta,(data_gb/t_delta)))
    
    # ===
    
    if verbose: print('\n'+72*'-')
    if verbose: print('total time : rgd.populate_abc_flow() : %s'%format_time_string((timeit.default_timer() - t_start_func)))
    if verbose: print(72*'-')
    return

def _populate_white_noise(self, **kwargs):
    '''
    Populate white noise dummy data
    --> hardcoded single precision output
    '''
    
    if (self.rank==0):
        verbose = True
    else:
        verbose = False
    
    if verbose: print('\n'+'rgd.populate_white_noise()'+'\n'+72*'-')
    t_start_func = timeit.default_timer()
    
    rx = kwargs.get('rx',1)
    ry = kwargs.get('ry',1)
    rz = kwargs.get('rz',1)
    rt = kwargs.get('rt',1)
    
    N = kwargs.get('N',1) ## number of timesteps to write at a time
    
    chunk_kb         = kwargs.get('chunk_kb',2*1024)
    chunk_constraint = kwargs.get('chunk_constraint',(1,None,None,None))
    chunk_base       = kwargs.get('chunk_base',2)
    
    self.nx = nx = kwargs.get('nx',128)
    self.ny = ny = kwargs.get('ny',128)
    self.nz = nz = kwargs.get('nz',128)
    self.nt = nt = kwargs.get('nt',128)
    
    if not isinstance(N, int):
        raise TypeError('N must be type int')
    if (self.nt%N !=0 ):
        raise ValueError(f'{self.nt:d}%{N:d}!=0')
    
    #data_gb = 3 * 4*nx*ny*nz*nt / 1024.**3
    data_gb = 1 * 4*nx*ny*nz*nt / 1024.**3
    
    if verbose: even_print(self.fname, '%0.2f [GB]'%(data_gb,))
    if verbose: even_print('nx','%i'%self.nx)
    if verbose: even_print('ny','%i'%self.ny)
    if verbose: even_print('nz','%i'%self.nz)
    if verbose: even_print('nt','%i'%self.nt)
    if verbose: even_print('rx','%i'%rx)
    if verbose: even_print('ry','%i'%ry)
    if verbose: even_print('rz','%i'%rz)
    if verbose: even_print('rt','%i'%rt)
    if verbose: print(72*'-')
    
    self.x = x = np.linspace(0., 2*np.pi, nx, dtype=np.float32)
    self.y = y = np.linspace(0., 2*np.pi, ny, dtype=np.float32)
    self.z = z = np.linspace(0., 2*np.pi, nz, dtype=np.float32)
    #self.t = t = np.linspace(0., 10.,     nt, dtype=np.float32)
    self.t = t = 0.1 * np.arange(nt, dtype=np.float32)
    
    if (rx*ry*rz*rt != self.n_ranks):
        raise AssertionError('rx*ry*rz*rt != self.n_ranks')
    if (rx>self.nx):
        raise AssertionError('rx>self.nx')
    if (ry>self.ny):
        raise AssertionError('ry>self.ny')
    if (rz>self.nz):
        raise AssertionError('rz>self.nz')
    
    if self.usingmpi:
        comm4d = self.comm.Create_cart(dims=[rx,ry,rz,rt], periods=[False,False,False,False], reorder=False)
        t4d    = comm4d.Get_coords(self.rank)
        
        rxl_   = np.array_split(np.arange(self.nx,dtype=np.int64),min(rx,self.nx))
        ryl_   = np.array_split(np.arange(self.ny,dtype=np.int64),min(ry,self.ny))
        rzl_   = np.array_split(np.arange(self.nz,dtype=np.int64),min(rz,self.nz))
        #rtl_   = np.array_split(np.arange(self.nt,dtype=np.int64),min(rt,self.nt))
        rxl    = [[b[0],b[-1]+1] for b in rxl_ ]
        ryl    = [[b[0],b[-1]+1] for b in ryl_ ]
        rzl    = [[b[0],b[-1]+1] for b in rzl_ ]
        #rtl    = [[b[0],b[-1]+1] for b in rtl_ ]
        
        rx1, rx2 = rxl[t4d[0]] ; nxr = rx2 - rx1
        ry1, ry2 = ryl[t4d[1]] ; nyr = ry2 - ry1
        rz1, rz2 = rzl[t4d[2]] ; nzr = rz2 - rz1
        #rt1, rt2 = rtl[t4d[3]] #; ntr = rt2 - rt1
        
        ## ## per-rank dim range
        ## xr = x[rx1:rx2]
        ## yr = y[ry1:ry2]
        ## zr = z[rz1:rz2]
        ## tr = t[rt1:rt2]
    
    else:
        nxr = nx
        nyr = ny
        nzr = nz
        #ntr = nt
    
    ## write dims (independent)
    self.create_dataset('dims/x', data=x, chunks=None)
    self.create_dataset('dims/y', data=y, chunks=None)
    self.create_dataset('dims/z', data=z, chunks=None)
    self.create_dataset('dims/t', data=t, chunks=None)
    
    shape  = (self.nt,self.nz,self.ny,self.nx)
    float_bytes = 4
    chunks = h5_chunk_sizer(nxi=shape, constraint=chunk_constraint, size_kb=chunk_kb, base=chunk_base, itemsize=float_bytes)
    
    #self.scalars = ['u','v','w']
    self.scalars = ['u']
    self.scalars_dtypes = [ np.dtype(np.float32) for s in self.scalars ]
    
    ## initialize datasets
    data_gb = 4*nx*ny*nz*nt / 1024.**3
    
    if self.usingmpi: self.comm.Barrier()
    t_start_initialize = timeit.default_timer()
    
    for scalar in self.scalars:
        
        if ('data/%s'%scalar in self):
            del self['data/%s'%scalar]
        if verbose:
            even_print('initializing data/%s'%(scalar,),'%0.2f [GB]'%(data_gb,))
        
        if self.usingmpi: self.comm.Barrier()
        t_start = timeit.default_timer()
        
        dset = self.create_dataset(
                                f'data/{scalar}', 
                                shape=shape,
                                dtype=np.float32,
                                chunks=chunks,
                                )
        
        if self.usingmpi: self.comm.Barrier()
        t_delta = timeit.default_timer() - t_start
        
        if verbose: even_print(f'initialize data/{scalar}', f'{data_gb:0.2f} [GB]  {t_delta:0.2f} [s]  {(data_gb/t_delta):0.3f} [GB/s]')
        
        chunk_kb_ = np.prod(dset.chunks)*4 / 1024. ## actual
        if verbose:
            even_print('chunk shape (t,z,y,x)','%s'%str(dset.chunks))
            even_print('chunk size','%i [KB]'%int(round(chunk_kb_)))
    
    if self.usingmpi: self.comm.Barrier()
    t_initialize = timeit.default_timer() - t_start_initialize
    
    if 1: ## write N ts at a time
        
        data_gb_write = 0.
        t_write = 0.
        
        rng = np.random.default_rng(seed=self.rank) ## random number generator
        data = np.zeros(shape=(nxr,nyr,nzr,N), dtype=np.float32)
        
        if verbose:
            progress_bar = tqdm(total=len(self.scalars)*(nt//N), ncols=100, desc='write', leave=False, file=sys.stdout, smoothing=0.)
        
        for scalar in self.scalars:
            for ti in range(nt//N):
                
                cy1 = ti * N
                cy2 = (ti+1) * N
                
                data[:,:,:,:] = rng.uniform(-1, +1, size=(nxr,nyr,nzr,N)).astype(np.float32)
                
                ds = self[f'data/{scalar}']
                if self.usingmpi: self.comm.Barrier()
                t_start = timeit.default_timer()
                if self.usingmpi:
                    with ds.collective:
                        ds[cy1:cy2,rz1:rz2,ry1:ry2,rx1:rx2] = data.T
                else:
                    ds[cy1:cy2,:,:,:] = data.T
                if self.usingmpi: self.comm.Barrier()
                t_delta = timeit.default_timer() - t_start
                data_gb = 4*nx*ny*nz*N / 1024**3
                
                t_write       += t_delta
                data_gb_write += data_gb
                
                if verbose: progress_bar.update()
        if verbose: progress_bar.close()
    
    if verbose: print(72*'-')
    if verbose: even_print('time initialize',format_time_string(t_initialize))
    if verbose: even_print('write total', '%0.2f [GB]  %0.3f [s]  %0.3f [GB/s]'%(data_gb_write,t_write,(data_gb_write/t_write)))
    if verbose: even_print(self.fname, '%0.2f [GB]'%(os.path.getsize(self.fname)/1024**3))
    if verbose: print(72*'-')
    if verbose: print('total time : rgd.populate_white_noise() : %s'%format_time_string((timeit.default_timer() - t_start_func)))
    if verbose: print(72*'-')
    return
