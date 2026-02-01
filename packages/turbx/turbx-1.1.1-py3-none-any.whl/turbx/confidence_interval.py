import numpy as np
from scipy.stats import norm

# ======================================================================

def calc_var_bmbc(u,M,axis=0):
    '''
    Estimate N·σ² using "Batch Means and Batch Correlations" (BMBC)
    see §4 of https://doi.org/10.1016/j.jcp.2017.07.005
    N = n samples
    M = size of batch
    K = n batches
    - Output is equivalent to N·σ²
    -------------------------------------
    --> !! requires update for ND data !!
    '''
    if not isinstance(u,np.ndarray):
        raise TypeError('input should be numpy array')
    if (u.ndim!=1):
        raise NotImplementedError
    #if (u.dtype!=np.float64):
    #    u = np.copy(u.astype(np.float64))
    
    N = u.shape[axis]
    
    ## assert N is divisible by M
    if (N%M!=0):
        raise ValueError('N%M!=0')
    K = N//M ## n non-overlapping batches in series
    if (K<3): ## must have >2 batch means
        raise ValueError('K<3 where K=N/M')
    
    u_mean = float( np.mean(u,axis=0) ) ## sample mean, μ̂
    
    ## remove full series mean
    uI = np.copy( u - u_mean )
    uI_mean = float( np.mean(uI,axis=0) ) ## should be =0
    np.testing.assert_allclose(uI_mean, 0., atol=1e-5)
    
    uI_batched      = np.copy(np.reshape(uI,(K,M),order='C'))
    uI_batched_mean = np.mean( uI_batched , axis=1 ) ## \bar{x}_k Eq.29
    
    S0 = np.sum( uI_batched_mean**2 ) ## Eq.31
    S1 = np.sum( uI_batched_mean[:-1] * uI_batched_mean[1:] ) ## Eq.32
    
    sig2   = (S0 + 2*S1) / ((K-1)*(K-2)) ## Eq.30
    Nsig2  = sig2 * N
    S1ovS0 = S1/S0 ## normalized lag-1 correlation of batch means
    return Nsig2, S1ovS0

def confidence_interval_unbiased(mean, N_sigma2, N, confidence=0.99):
    '''
    Compute the confidence interval for the mean given UNBIASED N·σ²
    '''
    if not isinstance(N,(int,np.integer)):
        raise TypeError('N should be an integer')
    if (N<1):
        raise ValueError('N<1')
    sigma_Xbar = np.sign(N_sigma2) * np.sqrt( np.abs(N_sigma2) / N )
    alpha = 1. - confidence
    z = norm.ppf(1. - alpha / 2.) ## percent point function
    ci_low  = mean - z * sigma_Xbar
    ci_high = mean + z * sigma_Xbar
    return ci_low, ci_high
