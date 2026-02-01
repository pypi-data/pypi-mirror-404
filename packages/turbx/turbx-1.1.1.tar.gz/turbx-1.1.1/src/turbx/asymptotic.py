import numpy as np
from scipy.integrate import cumulative_trapezoid
from scipy.optimize import least_squares
from scipy.special import exp1

# ======================================================================

def asymptotic_Wplus_eta(eta, y_plus, Re_theta):
    '''
    Monkewitz et al. (2007)
    Full-boundary-layer wake function
    -----
    This function generates a Re-dependent full-layer W+
      (not just W+_outer) using the U+ composite profile
    '''
    kappa = 0.384
    Cstar = 3.354
    
    ## Shape factor
    H12 = asymptotic_H12_Retheta(Re_theta)
    
    ## Coles-Fernholz
    ue_plus = (1./kappa)*np.log(H12*Re_theta) + Cstar
    
    ## Composite velocity
    uplus_composite = asymptotic_uplus_composite(y_plus, eta, Re_theta)
    
    ## Wake (velocity defect)
    return ue_plus - uplus_composite

def asymptotic_uplus_inner(y_plus):
    '''
    Monkewitz et al. (2007)
    Inner mean velocity U^+_{inner}(y^+)
    Obtained by integrating the Padé indicator function
    Eqs. (5)-(7)
    '''
    y_plus = np.asarray(y_plus)
    
    k = 0.384
    
    ## Padé P23 coefficients (Eq. 5)
    b0 = 1.000e-2 / k
    b1 = 1.100e-2
    b2 = 1.100e-4
    
    P23 = b0 * (1. + b1*y_plus + b2*y_plus**2) / (
          1. + b1*y_plus + b2*y_plus**2 + k*b0*b2*y_plus**3
          )
    
    ## Padé P25 coefficients (Eq. 6)
    h1 = -1.000e-2
    h2 =  6.000e-3
    h3 =  9.977e-4
    h4 =  2.200e-5
    h5 =  1.000e-6
    
    P25 = (1. - b0) * (1. + h1*y_plus + h2*y_plus**2) / (
          1. + h1*y_plus + h2*y_plus**2 + h3*y_plus**3 + h4*y_plus**4 + h5*y_plus**5
          )
    
    d_uplus_d_yplus = P23 + P25 ## d[u+]/dy+
    
    ## scipy.integrate.quad() could be used for continuous integration
    
    ## discrete trapezoidal integration
    uplus_inner = cumulative_trapezoid(y=d_uplus_d_yplus, x=y_plus, initial=0.)
    return uplus_inner

def asymptotic_uplus_composite(y_plus, eta, Re_theta):
    '''
    Monkewitz et al. (2007)
    Composite mean velocity U^+(y^+,η)
    Eq. (15), with U_e^+ from H12(Re_θ)
    '''
    y_plus = np.asarray(y_plus)
    eta    = np.asarray(eta)
    n      = y_plus.shape[0]
    
    kappa  = 0.384
    B      = 4.17   ## log-law intercept
    Cstar  = 3.354  ## C* (Monkewitz / Nagib)
    
    ## Inner velocity (Padé-based)
    uplus_inner = asymptotic_uplus_inner(y_plus)
    
    ## Shape factor and edge velocity
    H12       = asymptotic_H12_Retheta(Re_theta)
    ue_plus = (1.0/kappa)*np.log(H12*Re_theta) + Cstar
    
    ## Outer velocity
    Wplus_outer = asymptotic_Wplus_eta_outer(eta)
    uplus_outer = ue_plus - Wplus_outer
    
    ## Overlap (log law)
    uplus_log     = np.full((n,),0.,dtype=np.float64)
    uplus_log[1:] = (1.0/kappa)*np.log(y_plus[1:]) + B
    uplus_log[0]  = B
    
    ## Additive composite
    uplus_composite = uplus_inner + uplus_outer - uplus_log
    uplus_composite[0] = 0.
    
    return uplus_composite

def asymptotic_Wplus_eta_outer(eta):
    '''
    Monkewitz et al. (2007)
    https://doi.org/10.1063/1.2780196
    Eq.9
    '''
    ny  = eta.shape[0]
    k   = 0.384 ## κ
    w0  = 0.6332
    wn1 = -0.096 ## w_{-1}
    w2  = 28.5
    w8  = 33000.
    
    Wplus_outer = np.full((ny,),np.nan,dtype=np.float64)
    
    ii = np.where(eta>0)[0]
    η = eta[ii]
    
    ## W_+ = ((1/κ) E1(η) + w0) * 0.5 * [1 - tanh(w_{-1}/η + w2 η^2 + w8 η^8)]
    Wplus_outer[ii] = ( (1./k)*exp1(eta[ii]) + w0 ) \
                      * 0.5 \
                      * ( 1. - np.tanh( (wn1/η) + w2*η**2 + w8*η**8 ) )
    
    return Wplus_outer

def asymptotic_H12_Retheta(Re_theta):
    '''
    H12 = δ1/δ2 = δ*/θ
    Reθ = θ·ue·ρe/μe
    -----
    Monkewitz et al. (2007)
    https://doi.org/10.1063/1.2780196
    Nagib et al. (2007)
    https://doi.org/10.1098/rsta.2006.1948
    '''
    
    ## Asymptotic constants
    Cs = 3.354 ## C*
    k  = 0.384 ## κ
    I2 = 7.135 ## Iww (Monkewitz) | C′ (Nagib)
    
    Re_theta = np.atleast_1d(np.asarray(Re_theta, dtype=np.float64))
    n = Re_theta.shape[0]
    H12 = np.full((n,),np.nan,dtype=np.float64)
    
    def __f_root_nonlin_H12(H12,Re_theta):
        ue_plus = (1/k)*np.log(H12*Re_theta) + Cs ## Coles-Fernholz
        H12_test = 1. / ( 1. - (I2/ue_plus) )
        root = H12_test - H12
        return root
    
    def __f_H12_Retheta(Re_theta):
        n = Re_theta.shape[0]
        H12_out = np.zeros((n,),dtype=np.float64)
        for i in range(n):
            sol = least_squares(
                    fun=__f_root_nonlin_H12,
                    args=(Re_theta[i],),
                    x0=1.35,
                    xtol=1e-15,
                    ftol=1e-15,
                    gtol=1e-15,
                    method='dogbox',
                    bounds=(1,2),
                    )
            if not sol.success:
                raise ValueError
            H12_out[i] = float(sol.x[0])
        return H12_out
    
    H12 = __f_H12_Retheta(Re_theta)
    
    if n==1:
        return float(H12[0])
    
    return H12

def asymptotic_H32_Retheta(Re_theta,I3):
    '''
    H32 = δ3/δ2
    Reθ = θ·ue·ρe/μe
    '''
    
    ## Asymptotic constants (same as H12 function)
    Cs  = 3.354 ## C*
    k   = 0.384 ## κ
    I2  = 7.135 ## Iww (Monkewitz) | C′ (Nagib)
    
    if isinstance(Re_theta,(int,np.int32,np.int64,float,np.float32,np.float64)):
        Re_theta = np.array([Re_theta,],np.float64)
    elif isinstance(Re_theta, np.ndarray):
        pass
    elif isinstance(Re_theta, list):
        Re_theta = np.array(Re_theta,np.float64)
    else:
        raise ValueError
    
    ## H12(Reθ)
    H12 = asymptotic_H12_Retheta(Re_theta)
    
    if isinstance(H12,float):
        H12 = np.array([H12,],np.float64)
    
    n = Re_theta.shape[0]
    H32 = np.zeros((n,),dtype=np.float64)
    
    for i in range(n):
        ue_plus = (1/k)*np.log(H12[i]*Re_theta[i]) + Cs ## Coles–Fernholz
        H32[i] = (2. - 3.*(I2/ue_plus) + I3/(ue_plus**2)) / (1. - (I2/ue_plus))
    
    if H32.shape[0]==1:
        H32 = float(H32)
    
    return H32