import math
import os
import sys
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import scipy as sp
import tqdm

# ======================================================================

def get_overlapping_window_size(asz, n_win, overlap_fac):
    '''
    get window length and overlap given a
    desired number of windows and a nominal overlap factor
    -----
    --> the output should be passed to get_overlapping_windows()
        to do the actual padding & windowing
    '''
    if not isinstance(asz, (int,np.int32,np.int64)):
        raise TypeError('arg asz must be type int')
    if not isinstance(n_win, (int,np.int32,np.int64)):
        raise TypeError('arg n_win must be type int')
    if (overlap_fac >= 1.):
        raise ValueError('arg overlap_fac must be <1')
    if (overlap_fac < 0.):
        raise ValueError('arg overlap_fac must be >0')
    n_ends = n_win+1
    n_mids = n_win
    
    # === solve for float-valued window 'mid' size & 'end' size
    def eqn(soltup, asz=asz, overlap_fac=overlap_fac):
        (endsz,midsz) = soltup
        eq1 = asz - n_ends*endsz - n_mids*midsz
        eq2 = overlap_fac*(midsz+2*endsz) - endsz
        return [eq1, eq2]
    
    guess = asz*0.5
    endsz,midsz = sp.optimize.fsolve(eqn, (guess,guess), (asz,overlap_fac))
    win_len     = midsz + 2*endsz
    overlap     = endsz
    
    win_len = max(math.ceil(win_len),1)
    overlap = max(math.floor(overlap),0)
    
    return win_len, overlap

def get_overlapping_windows(a, win_len, overlap):
    '''
    subdivide 1D array into overlapping windows
    '''
    #pad_mode = kwargs.get('pad_mode','append')
    ##
    if not isinstance(a, np.ndarray):
        raise TypeError('arg a must be type np.ndarray')
    if not isinstance(win_len, int):
        raise TypeError('arg win_len must be type int')
    if not isinstance(overlap, int):
        raise TypeError('arg overlap must be type int')
    ##
    asz   = a.size
    skip  = win_len - overlap
    n_pad = (win_len - asz%skip)%skip
    #a_pad = np.concatenate(( np.zeros(n_pad,dtype=a.dtype) , np.copy(a) )) ## prepend
    a_pad = np.concatenate(( np.copy(a) , np.zeros(n_pad,dtype=a.dtype) )) ## append
    ##
    b = np.lib.stride_tricks.sliding_window_view(a_pad, win_len, axis=0)
    b = np.copy(b[::skip,:])
    n_win = b.shape[0]
    ##
    if (n_pad > 0.5*win_len):
        print('WARNING: n_pad > overlap')
    ##
    return b, n_win, n_pad

def ccor(ui,uj,**kwargs):
    '''
    1D normalized cross-correlation
    '''
    if (ui.ndim!=1):
        raise AssertionError('ui.ndim!=1')
    if (uj.ndim!=1):
        raise AssertionError('uj.ndim!=1')
    
    mode     = kwargs.get('mode','full')
    get_lags = kwargs.get('get_lags',False)
    
    if get_lags:
        lags = sp.signal.correlation_lags(ui.shape[0], uj.shape[0], mode=mode)
    else:
        lags = None
    
    #R    = sp.signal.correlate(ui, uj, mode=mode, method='direct')
    R    = sp.signal.correlate(ui, uj, mode=mode, method='fft') ## 'fft' is O(100)x faster for size O(10000) arrays
    norm = np.sqrt(np.sum(ui**2)) * np.sqrt(np.sum(uj**2))
    
    if (norm==0.):
        #R = np.ones((R.shape[0],), dtype=ui.dtype)
        R = np.zeros((R.shape[0],), dtype=ui.dtype)
    else:
        R /= norm
    
    if get_lags:
        return lags, R
    else:
        return R

def ccor_naive(u,v):
    '''
    1D normalized cross-correlation (naive version)
    - this kernel is designed as a check for ccor()
    '''
    if (u.ndim!=1):
        raise AssertionError('u.ndim!=1')
    if (v.ndim!=1):
        raise AssertionError('v.ndim!=1')
    
    ii = np.arange(u.shape[0],dtype=np.int32)
    jj = np.arange(v.shape[0],dtype=np.int32)
    
    ## lags (2D)
    ll     = np.stack(np.meshgrid(ii,jj,indexing='ij'), axis=-1)
    ll     = ll[:,:,0] - ll[:,:,1]
    
    ## lags (1D)
    lmin   = ll.min()
    lmax   = ll.max()
    n_lags = lmax-lmin+1
    lags   = np.arange(lmin,lmax+1)
    
    uu, vv = np.meshgrid(u,v,indexing='ij')
    uv     = np.stack((uu,vv), axis=-1)
    uvp    = np.prod(uv,axis=-1)
    
    c=-1
    R = np.zeros(n_lags, dtype=np.float64)
    for lag in lags:
        c+=1
        X = np.where(ll==lag)
        #N = X[0].shape[0]
        R_ = np.sum(uvp[X]) / ( np.sqrt(np.sum(u**2)) * np.sqrt(np.sum(v**2)) )
        R[c] = R_
    return lags, R

def ccor_vec(ui,uj,axis=0):
    '''
    normalized cross-correlation, vectorized wrapper
    ---
    Parameters:
        ui, uj : ndarray
            Input arrays with the same shape.
        axis : int
            Axis along which to compute the cross-correlation.
    Returns:
        R : ndarray
            Cross-correlation results normalized where norms are non-zero.
    '''
    
    if ui.shape != uj.shape:
        raise ValueError('ui and uj must have the same shape.')
    
    nd = ui.ndim
    if (nd<2):
        raise ValueError('nd<2')
    
    shape_orig = ui.shape
    axes = tuple(range(ui.ndim))
    
    if not isinstance(axis, int):
        raise ValueError('axis should be of type int')
    if (axis not in axes):
        raise ValueError(f'axis={axis:d} is not valid for array with ui.ndim={str(ui.ndim)}')
    
    ## normalization for output array
    norm = np.sqrt( np.sum( ui**2, axis=axis, keepdims=True ) ) * np.sqrt( np.sum( uj**2, axis=axis, keepdims=True ) )
    
    nx = ui.shape[axis] ## size of axis over which gradient will be performed
    shift_pos=nd-1 ## last axis
    
    ## shift cross-correlation axis to last axis
    nx = ui.shape[axis] ## size of axis over which gradient will be performed
    ui = np.swapaxes(ui, axis, shift_pos)
    uj = np.swapaxes(uj, axis, shift_pos)
    shape_new = ui.shape
    size_all_but_ax = np.prod(np.array(shape_new)[:-1])
    
    ## shape of output
    n_lags = 2*nx - 1
    shape_out = list(shape_orig)
    shape_out[axis] = n_lags
    shape_out = tuple(shape_out)
    
    ## reshape N-D to 2D
    ## cross-correlation axis is 1, all other axes are flattened on axis=0)
    ui  = np.reshape(ui, (size_all_but_ax,nx), order='C')
    uj  = np.reshape(uj, (size_all_but_ax,nx), order='C')
    
    ## vectorize kernel
    __ccor_kernel = np.vectorize(
        lambda u,v: sp.signal.correlate(u,v, mode='full', method='direct'),
        signature="(n),(n)->(m)",
    )
    
    ## run kernel
    R = __ccor_kernel(ui, uj)
    
    ## 2D to N-D
    R = np.reshape(R, (*shape_new[:-1],n_lags), order='C')
    
    ## shift cross-correlation axis back to original position
    R = np.swapaxes(R, axis, shift_pos)
    if (R.shape != shape_out):
        raise ValueError
    
    ## normalize
    mask = norm != 0
    mask = np.broadcast_to(mask, shape_out)
    norm = np.broadcast_to(norm, shape_out)
    R[mask] /= norm[mask]
    R[~mask] = 0.
    return R

def compute_bootstrap_statistic(x, f_statistic, **kwargs):
    '''
    Compute bootstrapped confidence intervals for a given statistic (function) using threads
    '''
    
    verbose          = kwargs.get('verbose',False)
    n_resamples      = kwargs.get('n_resamples',10_000)
    confidence_level = kwargs.get('confidence_level',0.99)
    max_workers      = kwargs.get('max_workers',None)
    entropy          = kwargs.get('entropy',None)
    desc             = kwargs.get('desc','compute_bootstrap_statistic()')
    
    if not isinstance(x, np.ndarray):
        raise ValueError('x must be numpy array')
    if x.ndim != 1:
        raise ValueError('x.ndim must be 1')
    
    n_samples = x.shape[0]
    sq = np.random.SeedSequence(entropy=entropy)
    seeds = sq.spawn(n_resamples) ## generate N unique child seeds for local RNGs
    # for seed_ in seeds: ## check
    #     print( int(seed_.generate_state(1)[0]) )
    def __bootstrap_worker(seed):
        local_rng = np.random.default_rng(seed=seed) ## a local RNG
        sample = local_rng.choice(x, size=n_samples, replace=True)
        return f_statistic(sample)
    
    if max_workers is None:
        max_workers = os.cpu_count()
    
    if verbose:
        progress_bar = tqdm(
            total=n_resamples,
            ncols=100,
            desc=desc,
            smoothing=0.,
            leave=False,
            file=sys.stdout,
            bar_format="{l_bar}{bar}| {n}/{total} [{percentage:.1f}%] {elapsed}/{remaining}\n\033[F\r",
            ascii="░█",
            )
    
    stats = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = executor.map( __bootstrap_worker , seeds )
        for stat in futures:
            stats.append(stat)
            if verbose:
                progress_bar.update()
    if verbose:
        progress_bar.close()
    stats = np.array(stats, dtype=np.float64)
    alpha = (1 - confidence_level) * 100 / 2
    ci_low, ci_high = np.percentile( stats , [ alpha , 100-alpha ] )
    return ci_low, ci_high
