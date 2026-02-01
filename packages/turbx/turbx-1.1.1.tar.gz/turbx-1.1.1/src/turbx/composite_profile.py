import numpy as np
import scipy as sp

'''
========================================================================
Composite profile of Chauhan et al. (2009)
https://doi.org/10.1088/0169-5983/41/2/021404
========================================================================
'''

# ======================================================================

class composite_profile_CMN2009():
    '''
    Tool for calculating composite profile described in Chauhan et al. (2009)
    'Criteria for assessing experiments in zero pressure gradient boundary layers'
    Chauhan, Monkewitz and Nagib
    https://doi.org/10.1088/0169-5983/41/2/021404
    '''
    
    def __init__(self, Re_tau, k=0.384, Pi=0.55, a=None, C=None, a2=132.8410, a3=-166.2041, a4=71.9114):
        '''
        k is the Von Kármán constant κ (asymptotic ≈0.384)
        Reτ is the friction Reynolds number δ+ = δ/δν = δ·uτ/ν
        C is the log law semilog constant (asymptotic ≈4.127, sometimes 5.0-5.2 in classic literature)
        a is a parameter directly related to C, see paper
        Π is the Coles wake parameter
        -----
        a = -10.3061 corresponds to C = 4.17
        '''
        self.k = k
        self.Re_tau = Re_tau
        self.Pi = Pi
        self.a2 = a2
        self.a3 = a3
        self.a4 = a4
        
        ## assert that exacly one of a or C was set
        if (a is None) and (C is None):
            raise ValueError('set one of a or C')
        if (a is not None) and (C is not None):
            raise ValueError('set either a or C, not both')
        
        if (C is not None): ## find 'a' given C
            
            self.C = C
            
            if not isinstance(C,float):
                raise ValueError
            
            def __f_opti(a,C):
                y_plus_inf = 1e12
                B_asymptotic = (1/k)*np.log((y_plus_inf-a)/-a) + self.__uplus_inner_B(y_plus_inf,a,k) - (1/k)*np.log(y_plus_inf)
                root = np.abs(B_asymptotic-C)
                return root
            
            sol = sp.optimize.least_squares(fun=__f_opti,
                                            args=(C,),
                                            x0=-10.,
                                            xtol=1e-15,
                                            ftol=1e-15,
                                            gtol=1e-15,
                                            method='dogbox',
                                            bounds=(-100.,+100.))
            if not sol.success:
                raise ValueError
            
            self.a = float(sol.x[0])
        
        else:
            
            self.a = a
            
            def __f_opti(C,a):
                y_plus_inf = 1e12
                B_asymptotic = (1/k)*np.log((y_plus_inf-a)/-a) + self.__uplus_inner_B(y_plus_inf,a,k) - (1/k)*np.log(y_plus_inf)
                root = np.abs(B_asymptotic-C)
                return root
            
            sol = sp.optimize.least_squares(fun=__f_opti,
                                            args=(a,),
                                            x0=-10.,
                                            xtol=1e-15,
                                            ftol=1e-15,
                                            gtol=1e-15,
                                            method='dogbox',
                                            bounds=(-100.,+100.))
            if not sol.success:
                raise ValueError
            
            self.C = float(sol.x[0])
    
    def get_uplus_inner(self,y_plus):
        '''
        Calculate inner U+ profile
        '''
        
        a = self.a ## related to B for log law
        k = self.k
        
        ## this B is a function of y+ for U+_inner i.e. is a vector
        B = self.__uplus_inner_B(y_plus,a,k)
        
        ## the 'inner' U+ profile
        u_plus_inner = np.copy( (1/k)*np.log((y_plus-a)/-a) + B )
        
        ## log-law constant is [U+] - (1/k)ln(y+) for [y+ -> inf]
        y_plus_inf = 1e14
        B_asymptotic = (1/k)*np.log((y_plus_inf-a)/-a) + self.__uplus_inner_B(y_plus_inf,a,k) - (1/k)*np.log(y_plus_inf)
        self.B = B_asymptotic
        #print(f'B={B_asymptotic:0.14f}')
        
        return u_plus_inner
    
    def __uplus_inner_B(self,y_plus,a,k):
        
        alpha = (-1/k - a)/2
        beta  = np.sqrt(-2*a*alpha - alpha**2)
        R     = np.sqrt( alpha**2 + beta**2 )
        
        #T1 = (4*alpha+a) * np.log( -(a/R)*np.sqrt( (y_plus-alpha)**2 + beta**2 ) / ( y_plus - a ) ) \
        #     + (alpha/beta)*(4*alpha + 5*a)*( np.arctan((y_plus-alpha)/beta) + np.arctan(alpha/beta) )
        T1 = (4*alpha+a) * np.log( -(a/R)*np.sqrt( (y_plus-alpha)**2 + beta**2 ) / ( y_plus - a ) ) \
             + (alpha/beta)*(4*alpha + 5*a)*( np.arctan2((y_plus-alpha),beta) + np.arctan2(alpha,beta) )
        
        T2 = R**2 / (a*(4*alpha-a)) * T1
        
        return T2
    
    def f_wake_Chauhan_exp(self,eta,Pi,a2,a3,a4):
        '''
        Exponential wake function W from Chauhan 2009
        '''
        T1 = 1. - np.exp( -(1/4)*( 5*a2 + 6*a3 + 7*a4 )*eta**4  + a2*eta**5 + a3*eta**6 + a4*eta**7 )
        T2 = 1. - np.exp( -(a2 + 2*a3 + 3*a4)/4 )
        T3 = 1. - 1/(2*Pi) * np.log(eta)
        return (T1/T2) * T3
    
    def get_wake(self, y_ov_delta, Pi):
        '''
        See Chauhan 2009
        '''
        
        a2 = self.a2
        a3 = self.a3
        a4 = self.a4
        
        if (y_ov_delta[0]!=0.):
            raise ValueError('y_ov_delta should start at 0')
        W = np.zeros_like(y_ov_delta)
        W[:] = np.nan
        i_valid = np.where( (y_ov_delta>0.) & (y_ov_delta<=1.) )
        eta = np.copy(y_ov_delta[i_valid])
        W[i_valid] = self.f_wake_Chauhan_exp(eta,Pi,a2,a3,a4)
        W[np.where(y_ov_delta==0.)] = 0.
        #if np.isnan(W).any():
        #    raise ValueError
        return W
    
    def get_integral_quantities(self, y_plus, u_plus, interp_kind='cubic'):
        '''
        δ*=δ1, θ=δ2, Reθ, Reδ1, Reδ2, H
        '''
        
        if not isinstance(y_plus, np.ndarray):
            raise ValueError
        if not isinstance(u_plus, np.ndarray):
            raise ValueError
        if (y_plus.ndim!=1):
            raise ValueError('y_plus.ndim!=1')
        if (u_plus.ndim!=1):
            raise ValueError('u_plus.ndim!=1')
        if (u_plus.shape != y_plus.shape):
            raise ValueError
        
        ## y_max < δ
        if (y_plus.max() < self.Re_tau):
            raise ValueError('y+_max of profile cannot be <Reτ --> y_max < δ')
        
        ## these are simply used locally to dimensionalize
        nu = 1e-5 ## [m^2/s]
        d = 37. ## [m]
        
        u_tau = nu * self.Re_tau / d ## [m/s]
        
        #sc_l_in = nu / u_tau
        sc_l_in = d / self.Re_tau
        
        U_inf_plus = self.get_uplus_inner(y_plus=self.Re_tau) + (2*self.Pi/self.k)
        U_inf = U_inf_plus * u_tau ## [m/s]
        
        u = np.copy( u_plus * u_tau ) ## [m/s]
        y = np.copy( y_plus * sc_l_in ) ## [m]
        
        integrand_theta = (u/U_inf)*(1-(u/U_inf))
        integrand_dstar = 1-(u/U_inf)
        
        #print(y.max())
        #print(d)
        #if not np.isclose(y.max(), d, rtol=1e-6):
        #    raise AssertionError
        
        theta_     = sp.integrate.cumulative_trapezoid(y=integrand_theta, x=y, initial=0.)
        theta_func = sp.interpolate.interp1d(y, theta_, kind=interp_kind, bounds_error=False, fill_value='extrapolate')
        theta      = theta_func(d)
        
        dstar_     = sp.integrate.cumulative_trapezoid(y=integrand_dstar, x=y, initial=0.)
        dstar_func = sp.interpolate.interp1d(y, dstar_, kind=interp_kind, bounds_error=False, fill_value='extrapolate')
        dstar      = dstar_func(d)
        
        Re_theta = theta * U_inf / nu
        Re_dstar = dstar * U_inf / nu
        H        = dstar / theta
        
        #dRC = U_inf_plus / dstar ## Δ=U_inf+/δ
        
        return Re_theta, Re_dstar, H
    
    def calc_uplus_composite(self,y_plus):
        
        y_ov_delta = np.copy( y_plus / self.Re_tau )
        i_gt_1 = np.where(y_ov_delta>1.)
        
        u_plus_inner = self.get_uplus_inner(y_plus)
        W = self.get_wake(y_ov_delta, Pi=self.Pi)
        i_nan = np.where(np.isnan(W))
        
        np.testing.assert_array_equal(i_gt_1,i_nan)
        
        ## U+_composite = U+_inner + U+_wake
        u_plus = np.copy( u_plus_inner + (2*self.Pi/self.k)*W )
        
        ## for y>δ, U+ = U+_inf
        U_inf_plus = self.get_uplus_inner(y_plus=self.Re_tau) + (2*self.Pi/self.k)
        u_plus[i_gt_1] = U_inf_plus
        
        return u_plus
    
    def __call__(self,y_plus):
        '''
        Calling object returns u+(y+)
        '''
        return self.calc_uplus_composite(y_plus)
