import os
import sys
import timeit
from pathlib import PurePosixPath

import numpy as np
import psutil
from mpi4py import MPI
from tqdm import tqdm

from .h5 import h5_chunk_sizer
from .utils import even_print, format_time_string

# ======================================================================

def _calc_mean(self, **kwargs):
    '''
    Calculate mean in [t] --> leaves [x,y,z,1]
    --> save to new RGD file
    -----
    - uses accumulator buffers and does *(1/n) at end to calculate mean
    - allows for low RAM usage, as the time dim can be sub-chunked (ct=N)
    '''
    
    rgd_meta = type(self) ## workaround for using rgd()
    
    if (self.rank==0):
        verbose = True
    else:
        verbose = False
    
    if verbose: print('\n'+'rgd.calc_mean()'+'\n'+72*'-')
    t_start_func = timeit.default_timer()
    
    rx = kwargs.get('rx',1)
    ry = kwargs.get('ry',1)
    rz = kwargs.get('rz',1)
    rt = kwargs.get('rt',1)
    
    fn_rgd_mean  = kwargs.get('fn_rgd_mean',None)
    #sfm         = kwargs.get('scalars',None) ## scalars to take (for mean)
    ti_min       = kwargs.get('ti_min',None)
    favre        = kwargs.get('favre',True)
    reynolds     = kwargs.get('reynolds',True)
    
    ct           = kwargs.get('ct',1) ## number of [t] chunks
    
    force        = kwargs.get('force',False)
    
    chunk_kb         = kwargs.get('chunk_kb',4*1024) ## h5 chunk size: default 4 [MB]
    chunk_constraint = kwargs.get('chunk_constraint',(1,None,None,None)) ## the 'constraint' parameter for sizing h5 chunks
    chunk_base       = kwargs.get('chunk_base',2)
    
    stripe_count   = kwargs.pop('stripe_count'   , 16 ) ## for initializing mean file
    stripe_size_mb = kwargs.pop('stripe_size_mb' , 2  )
    
    if (rt!=1):
        raise AssertionError('rt!=1')
    if (rx*ry*rz != self.n_ranks):
        raise AssertionError('rx*ry*rz != self.n_ranks')
    if (rx>self.nx):
        raise AssertionError('rx>self.nx')
    if (ry>self.ny):
        raise AssertionError('ry>self.ny')
    if (rz>self.nz):
        raise AssertionError('rz>self.nz')
    if (ti_min is not None):
        if not isinstance(ti_min, int):
            raise TypeError('ti_min must be type int')
    
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
    
    nx = self.nx
    ny = self.ny
    nz = self.nz
    nt = self.nt
    
    ## mean file name (for writing)
    if (fn_rgd_mean is None):
        fname_path = os.path.dirname(self.fname)
        fname_base = os.path.basename(self.fname)
        fname_root, fname_ext = os.path.splitext(fname_base)
        fname_mean_h5_base = fname_root+'_mean.h5'
        #fn_rgd_mean = os.path.join(fname_path, fname_mean_h5_base)
        fn_rgd_mean = str(PurePosixPath(fname_path, fname_mean_h5_base))
        #fn_rgd_mean = Path(fname_path, fname_mean_h5_base)
    
    if verbose: even_print('fn_rgd'          , self.fname    )
    if verbose: even_print('fn_rgd_mean'     , fn_rgd_mean   )
    if verbose: even_print('do Favre avg'    , str(favre)    )
    if verbose: even_print('do Reynolds avg' , str(reynolds) )
    if verbose: print(72*'-')
    if verbose: even_print('nx',f'{self.nx:d}')
    if verbose: even_print('ny',f'{self.ny:d}')
    if verbose: even_print('nz',f'{self.nz:d}')
    if verbose: even_print('nt',f'{self.nt:d}')
    if verbose: print(72*'-')
    if verbose: even_print('rx',f'{rx:d}')
    if verbose: even_print('ry',f'{ry:d}')
    if verbose: even_print('rz',f'{rz:d}')
    if verbose: even_print('ct',f'{ct:d}')
    if verbose: print(72*'-')
    
    ## get times to take for avg
    if (ti_min is not None):
        ti_for_avg = np.copy( self.ti[ti_min:] )
    else:
        ti_for_avg = np.copy( self.ti )
    
    nt_avg       = ti_for_avg.shape[0]
    t_avg_start  = self.t[ti_for_avg[0]]
    t_avg_end    = self.t[ti_for_avg[-1]]
    duration_avg = t_avg_end - t_avg_start
    
    #if not isinstance(ct, (int,np.int32,np.int64)):
    if not isinstance(ct, int):
        raise ValueError
    if (ct<1):
        raise ValueError
    
    ## [t] sub chunk range
    ctl_ = np.array_split( ti_for_avg, min(ct,nt_avg) )
    ctl = [[b[0],b[-1]+1] for b in ctl_ ]
    
    ## check that no sub ranges are <=1
    for a_ in [ ctl_[1]-ctl_[0] for ctl_ in ctl ]:
        if (a_ <= 1):
            raise ValueError
    
    ## assert constant Δt, later attach dt as attribute to mean file
    dt0 = np.diff(self.t)[0]
    if not np.all(np.isclose(np.diff(self.t), dt0, rtol=1e-7)):
        raise ValueError
    
    if verbose: even_print('n timesteps avg','%i/%i'%(nt_avg,self.nt))
    if verbose: even_print('t index avg start','%i'%(ti_for_avg[0],))
    if verbose: even_print('t index avg end','%i'%(ti_for_avg[-1],))
    if verbose: even_print('t avg start','%0.2f [-]'%(t_avg_start,))
    if verbose: even_print('t avg end','%0.2f [-]'%(t_avg_end,))
    if verbose: even_print('duration avg','%0.2f [-]'%(duration_avg,))
    if verbose: even_print('Δt','%0.2f [-]'%(dt0,))
    #if verbose: print(72*'-')
    
    ## performance
    t_read = 0.
    t_write = 0.
    data_gb_read = 0.
    data_gb_write = 0.
    
    #scalars_re = ['u','v','w','p','T','rho']
    scalars_fv = ['u','v','w','T'] ## 'p','rho'
    
    ## do a loop through to get names
    scalars_mean_names  = []
    #scalars_mean_dtypes = []
    for scalar in self.scalars:
        
        ##dtype = self.scalars_dtypes_dict[scalar]
        #dtype = np.float64 ## always save mean as double
        
        if reynolds:
            if True: ## always
                sc_name = scalar
                scalars_mean_names.append(sc_name)
                #scalars_mean_dtypes.append(dtype)
        if favre:
            if (scalar in scalars_fv):
                sc_name = f'r_{scalar}'
                scalars_mean_names.append(sc_name)
                #scalars_mean_dtypes.append(dtype)
    
    #with rgd(fn_rgd_mean, 'w', force=force, driver='mpio', comm=MPI.COMM_WORLD) as hf_mean:
    with rgd_meta(fn_rgd_mean, 'w', force=force, driver=self.driver, comm=self.comm, stripe_count=stripe_count, stripe_size_mb=stripe_size_mb) as hf_mean:
        
        ## initialize the mean file from the opened unsteady rgd file
        hf_mean.init_from_rgd(self.fname)
        
        ## set some top-level attributes (in MEAN file)
        hf_mean.attrs['duration_avg'] = duration_avg ## duration of mean
        #hf_mean.attrs['duration_avg'] = self.duration
        hf_mean.attrs['dt'] = dt0
        #hf_mean.attrs['fclass'] = 'rgd'
        hf_mean.attrs['fsubtype'] = 'mean'
        
        if verbose: print(72*'-')
        
        # === initialize datasets in mean file
        for scalar in self.scalars:
            
            data_gb_mean = np.dtype(np.float64).itemsize * self.nx*self.ny*self.nz * 1 / 1024**3
            
            shape  = (1,self.nz,self.ny,self.nx)
            chunks = h5_chunk_sizer(nxi=shape, constraint=chunk_constraint, size_kb=chunk_kb, base=chunk_base, itemsize=np.dtype(np.float64).itemsize)
            
            if reynolds:
                
                ## do the Re mean of all scalars in file, regardless whether explicitly in scalars_re or not
                #if scalar in scalars_re:
                if True:
                    
                    if ('data/%s'%scalar in hf_mean):
                        del hf_mean['data/%s'%scalar]
                    if verbose:
                        even_print( f'initializing data/{scalar}' , f'{data_gb_mean:0.3f} [GB]' )
                    dset = hf_mean.create_dataset(
                                                f'data/{scalar}',
                                                shape=shape,
                                                dtype=np.float64, ## mean dsets always double
                                                chunks=chunks,
                                                )
                    hf_mean.scalars.append('data/%s'%scalar)
                    
                    chunk_kb_ = np.prod(dset.chunks)*dset.dtype.itemsize / 1024. ## actual
                    if verbose:
                        even_print('chunk shape (t,z,y,x)','%s'%str(dset.chunks))
                        even_print('chunk size','%i [KB]'%int(round(chunk_kb_)))
            
            if favre:
                
                if (scalar in scalars_fv):
                    if ('data/%s_fv'%scalar in hf_mean):
                        del hf_mean['data/%s_fv'%scalar]
                    if verbose:
                        even_print( f'initializing data/{scalar}_fv' , f'{data_gb_mean:0.3f} [GB]' )
                    dset = hf_mean.create_dataset(f'data/{scalar}_fv',
                                                  shape=shape,
                                                  dtype=np.float64, ## mean dsets always double
                                                  chunks=chunks,
                                                  )
                    hf_mean.scalars.append('data/%s_fv'%scalar)
                    
                    chunk_kb_ = np.prod(dset.chunks)*dset.dtype.itemsize / 1024. ## actual
                    if verbose:
                        even_print('chunk shape (t,z,y,x)','%s'%str(dset.chunks))
                        even_print('chunk size','%i [KB]'%int(round(chunk_kb_)))
        
        if self.usingmpi: self.comm.Barrier()
        #if verbose: print(72*'-')
        
        ## accumulator array for local rank --> initialize
        data_sum = np.zeros(shape=(nxr,nyr,nzr,1), dtype={'names':scalars_mean_names, 'formats':[np.float64 for _ in scalars_mean_names]})
        
        # ==========================================================
        # check memory
        # ==========================================================
        
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
        
        shape_read_local = (nxr,nyr,nzr,nt//ct)
        data_gb_local    = np.dtype(np.float64).itemsize * np.prod(shape_read_local) / 1024**3
        if verbose: even_print('read shape (local)', f'[{nxr:d},{nyr:d},{nzr:d},{nt//ct:d}]')
        if verbose: even_print('read size (local)', f'{int(np.ceil(data_gb_local)):d} [GB]')
        
        shape_read_global = (nx,ny,nz,nt//ct)
        data_gb_global    = np.dtype(np.float64).itemsize * np.prod(shape_read_global) / 1024**3
        if verbose: even_print('read shape (global)'   , f'[{nx:d},{ny:d},{nz:d},{nt//ct:d}]')
        if verbose: even_print('read size (global)'    , f'{int(np.ceil(data_gb_global)):d} [GB]')
        if verbose: even_print('read size (global) ×3' , f'{int(np.ceil(data_gb_global*3)):d} [GB]')
        ram_usage_est = data_gb_global*3/total_free
        
        if verbose: even_print('RAM usage estimate', f'{100*ram_usage_est:0.1f} [%]')
        self.comm.Barrier()
        if (ram_usage_est>0.60):
            print('RAM consumption might be too high. exiting.')
            self.comm.Abort(1)
        
        # ==========================================================
        # main loop
        # ==========================================================
        
        if self.usingmpi: self.comm.Barrier()
        if verbose: print(72*'-')
        
        if verbose:
            progress_bar = tqdm(
                total=ct,
                ncols=100,
                desc='mean',
                leave=True,
                file=sys.stdout,
                mininterval=0.1,
                smoothing=0.,
                #bar_format="\033[B{l_bar}{bar}| {n}/{total} [{percentage:.1f}%] {elapsed}/{remaining}\033[A\n\b",
                bar_format="{l_bar}{bar}| {n}/{total} [{percentage:.1f}%] {elapsed}/{remaining}",
                ascii="░█",
                colour='#FF6600',
                )
        
        ct_counter=0
        for ctl_ in ctl:
            ct_counter += 1
            ct1, ct2 = ctl_
            ntc = ct2 - ct1
            
            if (ct>1):
                if verbose:
                    mesg = f'[t] sub chunk {ct_counter:d}/{ct:d}'
                    tqdm.write( mesg )
                    tqdm.write( '-'*len(mesg) )
            
            ## Read ρ for Favre averaging
            if favre:
                
                dset = self['data/rho']
                
                if self.usingmpi: self.comm.Barrier()
                t_start = timeit.default_timer()
                
                if self.usingmpi: 
                    with dset.collective:
                        rho = dset[ct1:ct2,rz1:rz2,ry1:ry2,rx1:rx2].T
                else:
                    rho = dset[ct1:ct2,:,:,:].T
                
                if self.usingmpi: self.comm.Barrier()
                t_delta = timeit.default_timer() - t_start
                
                data_gb = dset.dtype.itemsize * self.nx*self.ny*self.nz * ntc / 1024**3
                if verbose:
                    txt = even_print('read: rho', '%0.2f [GB]  %0.2f [s]  %0.3f [GB/s]'%(data_gb,t_delta,(data_gb/t_delta)), s=True)
                    tqdm.write(txt)
                
                t_read       += t_delta
                data_gb_read += data_gb
                
                ## convert to double
                rho = rho.astype(np.float64)
            
            ## Read data, perform sum Σ
            for scalar in self.scalars:
                
                dset = self[f'data/{scalar}']
                
                if self.usingmpi: self.comm.Barrier()
                t_start = timeit.default_timer()
                
                if self.usingmpi:
                    with dset.collective:
                        data = dset[ct1:ct2,rz1:rz2,ry1:ry2,rx1:rx2].T
                else:
                    data = dset[ct1:ct2,:,:,:].T
                
                if self.usingmpi: self.comm.Barrier()
                t_delta = timeit.default_timer() - t_start
                
                data_gb = dset.dtype.itemsize * self.nx*self.ny*self.nz * ntc / 1024**3
                
                if verbose:
                    txt = even_print('read: %s'%scalar, '%0.2f [GB]  %0.2f [s]  %0.3f [GB/s]'%(data_gb,t_delta,(data_gb/t_delta)), s=True)
                    tqdm.write(txt)
                
                t_read       += t_delta
                data_gb_read += data_gb
                
                ## convert to double
                data = data.astype(np.float64)
                
                # === do sum, add to accumulator
                if reynolds:
                    sc_name = scalar
                    data_sum[sc_name] += np.sum(data, axis=-1, dtype=np.float64, keepdims=True)
                if favre:
                    if (scalar in scalars_fv):
                        sc_name = f'r_{scalar}'
                        data_sum[sc_name] += np.sum(data*rho, axis=-1, dtype=np.float64, keepdims=True)
                
                if self.usingmpi: self.comm.Barrier()
            
            ## check RAM
            #mem_avail_gb = psutil.virtual_memory().available/1024**3
            mem_free_gb  = psutil.virtual_memory().free/1024**3
            if verbose:
                tqdm.write(even_print('mem free', '%0.1f [GB]'%mem_free_gb, s=True))
            
            if verbose: progress_bar.update()
            if verbose: tqdm.write(72*'-')
        if verbose: progress_bar.close()
        
        # ==========================================================
        # multiply accumulators by (1/n)
        # ==========================================================
        
        for scalar in self.scalars:
            if reynolds:
                sc_name = scalar
                data_sum[sc_name] *= (1/nt_avg)
            if favre:
                if (scalar in scalars_fv):
                    sc_name = f'r_{scalar}'
                    data_sum[sc_name] *= (1/nt_avg)
        
        # ==========================================================
        # 'data_sum' now contains averages, not sums!
        # ==========================================================
        
        ## Favre avg : φ_tilde = avg[ρ·φ]/avg[ρ]
        rho_mean = np.copy( data_sum['rho'] )
        
        # === write
        for scalar in self.scalars:
            
            if reynolds:
                
                dset = hf_mean[f'data/{scalar}']
                
                data_out = np.copy( data_sum[scalar] )
                
                ## if storing as single precision, pre-convert
                if (dset.dtype==np.float32):
                    data_out = np.copy( data_sum[scalar].astype(np.float32) )
                
                if self.usingmpi: self.comm.Barrier()
                t_start = timeit.default_timer()
                if self.usingmpi:
                    with dset.collective:
                        dset[:,rz1:rz2,ry1:ry2,rx1:rx2] = data_out.T
                else:
                    dset[:,:,:,:] = data_out.T
                if self.usingmpi: self.comm.Barrier()
                t_delta = timeit.default_timer() - t_start
                
                data_gb_mean = data_out.dtype.itemsize * self.nx*self.ny*self.nz * 1 / 1024**3
                
                if verbose:
                    txt = even_print(f'write: {scalar}', '%0.2f [GB]  %0.2f [s]  %0.3f [GB/s]'%(data_gb_mean,t_delta,(data_gb_mean/t_delta)), s=True)
                    tqdm.write(txt)
                
                t_write       += t_delta
                data_gb_write += data_gb_mean
            
            if favre:
                if (scalar in scalars_fv):
                    
                    dset = hf_mean[f'data/{scalar}_fv']
                    
                    ## φ_tilde = avg[ρ·φ]/avg[ρ]
                    data_out = np.copy( data_sum[f'r_{scalar}'] / rho_mean )
                    
                    ## if storing as single precision, pre-convert
                    if (dset.dtype==np.float32):
                        data_out = np.copy( data_out.astype(np.float32) )
                    
                    if self.usingmpi: self.comm.Barrier()
                    t_start = timeit.default_timer()
                    if self.usingmpi:
                        with dset.collective:
                            dset[:,rz1:rz2,ry1:ry2,rx1:rx2] = data_out.T
                    else:
                        dset[:,:,:,:] = data_out.T
                    if self.usingmpi: self.comm.Barrier()
                    t_delta = timeit.default_timer() - t_start
                    
                    data_gb_mean = data_out.dtype.itemsize * self.nx*self.ny*self.nz * 1 / 1024**3
                    
                    if verbose:
                        txt = even_print(f'write: {scalar}_fv', '%0.2f [GB]  %0.2f [s]  %0.3f [GB/s]'%(data_gb_mean,t_delta,(data_gb_mean/t_delta)), s=True)
                        tqdm.write(txt)
                    
                    t_write       += t_delta
                    data_gb_write += data_gb_mean
        
        # === replace dims/t array --> take last time of series
        t = np.array([self.t[-1]],dtype=np.float64)
        if ('dims/t' in hf_mean):
            del hf_mean['dims/t']
        hf_mean.create_dataset('dims/t', data=t)
        
        if hasattr(hf_mean, 'duration_avg'):
            if verbose: even_print('duration avg', '%0.2f [-]'%hf_mean.duration_avg)
    
    if verbose: print(72*'-')
    if verbose: even_print('time read',format_time_string(t_read))
    if verbose: even_print('time write',format_time_string(t_write))
    if verbose: even_print('read total avg', '%0.2f [GB]  %0.3f [s]  %0.3f [GB/s]'%(data_gb_read,t_read,(data_gb_read/t_read)))
    if verbose: even_print('write total avg', '%0.2f [GB]  %0.3f [s]  %0.3f [GB/s]'%(data_gb_write,t_write,(data_gb_write/t_write)))
    
    ## report file
    self.comm.Barrier()
    if verbose:
        print(72*'-')
        even_print( os.path.basename(fn_rgd_mean), f'{(os.path.getsize(fn_rgd_mean)/1024**3):0.1f} [GB]')
    if verbose: print(72*'-')
    if verbose: print('total time : rgd.calc_mean() : %s'%format_time_string((timeit.default_timer() - t_start_func)))
    if verbose: print(72*'-')
    return
