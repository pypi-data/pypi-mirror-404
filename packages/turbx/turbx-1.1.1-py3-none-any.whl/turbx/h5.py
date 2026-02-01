import sys

import h5py
import numpy as np
from tqdm import tqdm

# ======================================================================

def h5_chunk_sizer(nxi, **kwargs):
    '''
    Solve for HDF5 dataset chunk size.

    Parameters:
    ----------
    nxi : iterable
        The shape of the full HDF5 dataset.
    constraint : iterable
        Per-axis constraint. Each element can be:
            - None         → flexible
            - int (>0)     → fixed chunk size
            - 'full' or -1 → chunk size equals axis size
            - ('max', int) → chunk size must be ≤ int
    '''
    
    size_kb    = kwargs.get('size_kb'    , 2*1024 ) ## target chunk size in [KB] --> default = 2 [MB]
    itemsize   = kwargs.get('itemsize'   , 4      ) ## dtype.itemsize --> default single precision i.e. 4 [B]
    constraint = kwargs.get('constraint' , None   ) ## iterable of nxi constraints --> int,None,'full'/-1
    base       = kwargs.get('base'       , 2      ) ## axis chunk size = ceil[size/(<int>*base)] where <int> is incremented
    
    ## if no constraint given, all axes are fully flexible
    if constraint is None:
        constraint = [ None for i in range(len(nxi)) ]
    
    ## check inputs
    if not hasattr(constraint, '__iter__') or len(nxi) != len(constraint):
        raise ValueError('nxi and constraint must be iterable and the same length')
    if not isinstance(base,int):
        raise TypeError('base must be an integer')
    if (base<1):
        raise TypeError('base must be an integer')
    
    # === increment divisor on largest axis, with divisor=<int>*base
    
    nxi = list(nxi)
    div = [ 1 for i in range(len(nxi)) ] ## divisor vector, initialize with int ones
    
    ## list of axes indices which are 'flexible' ... this is updated dynamically in loop
    i_flexible = [ i for i,c in enumerate(constraint) if c is None or isinstance(c,tuple) ]
    
    while True:
        
        div_last = list(div) ## make a copy
        #print(f'div_last = {str(tuple(div_last))}')
        
        chunks = []
        for i in range(len(nxi)):
            
            dim = nxi[i]
            
            if (constraint[i] is None):
                C = max( int(np.floor(dim/div[i])) , 1 ) ## divide by divisor
            elif (constraint[i] == 'full') or (constraint[i] == -1):
                C = dim ## chunk axis shape is == dset axis shape
            elif isinstance(constraint[i], int) and (constraint[i]>0):
                C = constraint[i] ## chunk axis shape is just the constraint
            elif isinstance(constraint[i], tuple) and (constraint[i][0]=='max') and isinstance(constraint[i][1],int):
                max_val = constraint[i][1]
                C = min( max( int(np.floor(dim/div[i])) , 1 ) , max_val )
            else:
                raise ValueError(f'problem with constraint[{i:d}] = {str(constraint[i])}')
            chunks.append(C)
        
        #print(f'chunks = {str(tuple(chunks))}')
        
        ## recalculate i_flexible
        i_flexible = []
        for i,c in enumerate(constraint):
            if chunks[i] == 1: ## already at min, is not flexible
                continue
            if c is None:
                i_flexible.append(i)
            elif isinstance(c,tuple) and c[0]=='max':
                if chunks[i] > 1:
                    i_flexible.append(i)
        
        #print(f'i_flexible = {str(i_flexible)}')
        
        ## there are no flexible axes --> exit loop
        if len(i_flexible)==0:
            break
        
        ## the current size of a chunk
        chunk_size_kb = np.prod(chunks)*itemsize / 1024.
        #print(f'chunk size {chunk_size_kb:0.1f} [KB] / {np.prod(chunks)*itemsize:d} [B]')
        
        if ( chunk_size_kb <= size_kb ): ## if chunk size is < target, then break
            break
        else: ## otherwise, increase the divisor of the greatest 'flexible' axis
            
            ## get index of (flexible) axis with greatest size
            aa = [ i for i,c in enumerate(chunks) if (i in i_flexible) ]
            bb = [ c for i,c in enumerate(chunks) if (i in i_flexible) ]
            i_gt = aa[np.argmax(bb)]
            
            ## update divisor
            div[i_gt] *= base
        
        #print(f'div = {str(tuple(div))}')
        #print('---')
        
        ## check if in infinite loop (divisor not being updated)
        if (div_last is not None) and (div == div_last):
            raise ValueError(f'invalid parameters for h5_chunk_sizer() : constraint={str(constraint)}, size_kb={size_kb:d}, base={base:d}')
    
    return tuple(chunks)

def h5_visititems_print_attrs(name, obj):
    '''
    callable for input to h5py.Group.visititems() to print names & attributes
    '''
    n_slashes = name.count('/')
    shift = n_slashes*2*' '
    item_name = name.split('/')[-1]
    
    if isinstance(obj,h5py._hl.dataset.Dataset):
        print(shift + item_name + ' --> shape=%s, dtype=%s'%( str(obj.shape), str(obj.dtype) ) )
    else:
        print(shift + item_name)
    
    ## print attributes
    for key, val in obj.attrs.items():
        try:
            print(shift + 2*' ' + f'{key} = {str(val)} --> dtype={str(val.dtype)}')
        except AttributeError:
            print(shift + 2*' ' + f'{key} = {str(val)} --> type={str(type(val).__name__)}')

def h5_print_contents(h5filehandle):
    '''
    Print file-level attributes and recursively print names & attributes of all groups and datasets.
    '''
    
    ## file-level attributes
    for key, val in h5filehandle.attrs.items():
        try:
            print(f'{key} = {str(val)} --> dtype={str(val.dtype)}')
        except AttributeError:
            print(f'{key} = {str(val)} --> type={str(type(val).__name__)}')
    
    def visitor(name, obj):
        n_slashes = name.count('/')
        shift     = n_slashes * 2 * ' '
        item_name = name.split('/')[-1]
        
        if isinstance(obj, h5py._hl.dataset.Dataset):
            print(shift + item_name + ' --> shape=%s, dtype=%s' % (str(obj.shape), str(obj.dtype)))
        else:
            print(shift + item_name)
        
        for key, val in obj.attrs.items():
            try:
                print(shift + 2 * ' ' + f'{key} = {str(val)} --> dtype={str(val.dtype)}')
            except AttributeError:
                print(shift + 2 * ' ' + f'{key} = {str(val)} --> type={str(type(val).__name__)}')
    
    # Use the visitor function with visititems
    h5filehandle.visititems(visitor)
    
    return

class h5_visit_container:
    '''
    callable for input to h5py.Group.visit() which stores dataset/group names
    '''
    def __init__(self):
        self.names = []
    def __call__(self, name):
        if (name not in self.names):
            self.names.append(name)

def h5_ds_force_allocate_chunks(ds, verbose=False, quick=False):
    '''
    Force allocation of all chunks in an ND dataset by writing real data
    '''
    if not isinstance(ds, h5py.Dataset):
        raise TypeError('ds must be a h5py.Dataset object')
    
    shape = ds.shape
    dtype = ds.dtype
    chunk_shape = ds.chunks
    rng = np.random.default_rng(seed=1)
    
    ## for contiguous datasets, fill the entire array
    if chunk_shape is None:
        #ds[...] = np.zeros(shape, dtype=dtype) ## might lead to optimizations under the hood
        #ds[...] = rng.uniform(-1,+1,size=shape).astype(dtype)
        ds[...] = rng.random(size=shape, dtype=dtype)
        return
    
    ## info needed for iterating through chunks
    chunk_starts = [range(0, dim, cdim) for dim, cdim in zip(shape, chunk_shape)]
    chunk_grid_shape = [len(r) for r in chunk_starts]
    total_chunks = np.prod(chunk_grid_shape)
    
    if verbose:
        progress_bar = tqdm(
            total=total_chunks,
            ncols=100,
            desc='allocate chunks',
            leave=True,
            file=sys.stdout,
            mininterval=0.1,
            smoothing=0.,
            #bar_format="\033[B{l_bar}{bar}| {n}/{total} [{percentage:.1f}%] {elapsed}/{remaining}\033[A\n\b",
            bar_format="{l_bar}{bar}| {n}/{total} [{percentage:.1f}%] {elapsed}/{remaining}",
            ascii="░█",
            colour='#FF6600',
            )
    
    for chunk_idx in np.ndindex(*chunk_grid_shape):
        starts = [r[i] for r, i in zip(chunk_starts, chunk_idx)]
        
        if quick: ## just write a single element to allocate the chunk
            ds[tuple(starts)] = 0
        else:
            slices = tuple(
                slice(start, min(start + size, dim))
                for start, size, dim in zip(starts, chunk_shape, shape)
                )
            actual_shape = tuple(slc.stop - slc.start for slc in slices)
            #ds[slices] = np.zeros(actual_shape, dtype=dtype) ## might lead to optimizations under the hood
            #ds[slices] = rng.uniform(-1,+1,size=actual_shape).astype(dtype)
            ds[slices] = rng.random(size=actual_shape, dtype=dtype)
        
        if verbose: progress_bar.update()
    if verbose: progress_bar.close()
    return
