import numpy as np
from scipy.integrate import cumulative_trapezoid
from scipy.interpolate import PchipInterpolator, interp1d
from scipy.optimize import least_squares, root_scalar

'''
========================================================================
1D boundary layer profile kernels
========================================================================
'''

def _check_validity_yx(y,x):
    '''
    Check 1D coordinate [y] and generic 1D variable [x]
    '''
    if not isinstance(y,np.ndarray):
        raise ValueError('y must be type np.ndarray')
    if not isinstance(x,np.ndarray):
        raise ValueError('x must be type np.ndarray')
    if y.ndim != 1 or x.ndim != 1:
        raise ValueError('.ndim != 1')
    if y.shape[0] != x.shape[0]:
        raise ValueError('y,x shapes not equal')
    if not np.all(np.diff(y) > 0): ## check (+) monotonicity
        raise ValueError("y must be monotonically increasing")
    if y[0] < -1e-4:
        raise ValueError("y[0] < 0")
    if not np.isclose(y[0], 0., atol=1e-4):
        raise ValueError("y[0] not sufficiently close to 0")
    return

def _check_validity_jn(j_edge,n):
    '''
    Check edge index j_edge with respect to 1D shape n
    '''
    if not isinstance(j_edge,(int,np.integer)):
        raise ValueError("j_edge must be int")
    if j_edge>=n:
        raise ValueError("j_edge>=n")
    if j_edge<-n:
        raise ValueError("j_edge<-n")
    if j_edge==0:
        raise RuntimeError('j_edge==0')
    return

def _determine_ju_edge(y,u,j_edge,u_edge,**kwargs):
    '''
    Helper function to handle the various
      j_edge,u_edge arg-passing patterns
    '''
    n     = y.shape[0]
    check = kwargs.get('check',True)
    rtol  = kwargs.get('rtol',1e-4)
    
    ## (1/4) Both j_edge & u_edge provided: just check
    if j_edge is not None and u_edge is not None:
        if check:
            np.testing.assert_allclose(u[j_edge], u_edge, rtol=rtol)
    
    ## (2/4) Neither j_edge nor u_edge provided: take max(u)
    elif j_edge is None and u_edge is None:
        u_edge = u.max()
        j_edge = int(np.argmax(u))
        np.testing.assert_allclose(u[j_edge], u_edge, rtol=1e-6)
    
    ## (3/4) j_edge passed but no u_edge
    elif j_edge is not None and u_edge is None:
        u_edge = float(u[j_edge])
    
    ## (4/4) u_edge given but no j_edge
    elif j_edge is None and u_edge is not None:
        jj = np.where( u >= u_edge )[0] ## Freestream indices
        if jj.shape[0]==0: ## No index is > u_edge
            j_edge = n-1 ## Index of last element
        else:
            j_edge = int(jj.min()) ## Lowest 'freestream' index
    
    else:
        raise ValueError
    
    return j_edge, u_edge

# ======================================================================

def calc_d1(y, u, rho=None, j_edge=None, u_edge=None, rho_edge=None, **kwargs):
    '''
    Displacement (mass-flux deficit) thickness δ1 = δ*
    -----
    δ1 = ∫ ( 1 - ρu / (ρe·ue) ) dy
    '''
    check = kwargs.get('check',True)
    rtol  = kwargs.get('rtol',1e-4)
    
    y = np.asarray(y)
    u = np.asarray(u)
    
    ## Assert 0D scalars
    for val in (u_edge, rho_edge):
        if val is not None and not isinstance(val, (float,np.floating)):
            raise ValueError('An arg intended as 0D scalar has non-float type')
    
    ## If ρ_edge is passed, then ρ must also be passed
    if rho_edge is not None and rho is None:
        raise ValueError('ρ_edge passed but ρ not passed')
    
    if rho is None: ## no ρ passed, set ρ=const=1 (incomp.)
        rho = np.ones_like(u)
    rho = np.asarray(rho)
    
    _check_validity_yx(y,u)
    _check_validity_yx(y,rho)
    n = y.shape[0]
    j_edge, u_edge = _determine_ju_edge(y,u,j_edge,u_edge,check=check,rtol=rtol)
    _check_validity_jn(j_edge,n)
    if rho_edge is None:
        rho_edge = rho[j_edge]
    
    integrand = 1. - (rho*u)/(rho_edge*u_edge) ## δ1 integrand
    d1 = cumulative_trapezoid(y=integrand, x=y, initial=0.)[j_edge] ## δ1
    return d1

def calc_d2(y, u, rho=None, j_edge=None, u_edge=None, rho_edge=None, **kwargs):
    '''
    Momentum deficit thickness δ2 = θ
    -----
    δ2 = ∫ ( ρu / (ρe·ue) ) ( 1 - u / ue ) dy
    '''
    check = kwargs.get('check',True)
    rtol  = kwargs.get('rtol',1e-4)
    
    y = np.asarray(y)
    u = np.asarray(u)
    
    ## Assert 0D scalars
    for val in (u_edge, rho_edge):
        if val is not None and not isinstance(val, (float,np.floating)):
            raise ValueError('An arg intended as 0D scalar has non-float type')
    
    ## If ρ_edge is passed, then ρ must also be passed
    if rho_edge is not None and rho is None:
        raise ValueError('ρ_edge passed but ρ not passed')
    
    if rho is None: ## no ρ passed, set ρ=const=1 (incomp.)
        rho = np.ones_like(u)
    rho = np.asarray(rho)
    
    _check_validity_yx(y,u)
    _check_validity_yx(y,rho)
    n = y.shape[0]
    j_edge, u_edge = _determine_ju_edge(y,u,j_edge,u_edge,check=check,rtol=rtol)
    _check_validity_jn(j_edge,n)
    if rho_edge is None:
        rho_edge = rho[j_edge]
    
    integrand = (rho*u)/(rho_edge*u_edge) * (1. - u/u_edge) ## δ2 integrand
    d2 = cumulative_trapezoid(y=integrand, x=y, initial=0.)[j_edge] ## δ2
    return d2

def calc_d3(y, u, rho=None, j_edge=None, u_edge=None, rho_edge=None, **kwargs):
    '''
    Kinetic energy deficit thickness δ3
    -----
    δ3 = ∫ ( ρu / (ρe·ue) ) ( 1 - (u / ue)^2 ) dy
    '''
    check = kwargs.get('check',True)
    rtol  = kwargs.get('rtol',1e-4)
    
    y = np.asarray(y)
    u = np.asarray(u)
    
    ## Assert 0D scalars
    for val in (u_edge, rho_edge):
        if val is not None and not isinstance(val, (float,np.floating)):
            raise ValueError('An arg intended as 0D scalar has non-float type')
    
    ## If ρ_edge is passed, then ρ must also be passed
    if rho_edge is not None and rho is None:
        raise ValueError('ρ_edge passed but ρ not passed')
    
    if rho is None: ## no ρ passed, set ρ=const=1 (incomp.)
        rho = np.ones_like(u)
    rho = np.asarray(rho)
    
    _check_validity_yx(y,u)
    _check_validity_yx(y,rho)
    n = y.shape[0]
    j_edge, u_edge = _determine_ju_edge(y,u,j_edge,u_edge,check=check,rtol=rtol)
    _check_validity_jn(j_edge,n)
    if rho_edge is None:
        rho_edge = rho[j_edge]
    
    integrand = (rho*u)/(rho_edge*u_edge) * (1. - (u/u_edge)**2) ## δ3 integrand
    d3 = cumulative_trapezoid(y=integrand, x=y, initial=0.)[j_edge] ## δ3
    return d3

def calc_dRC(y, u, u_tau, rho=None, j_edge=None, u_edge=None, rho_edge=None, rho_wall=None, **kwargs):
    '''
    Rotta-Clauser Δ = ∫W+dy = ∫(ρe+ue+ - ρ+u+) dy
    -----
    W  = (ρe·ue - ρ·u)/(ρe·ue) = 1 - (ρu/(ρe·ue))
    W+ = (ρe·ue - ρ·u)/(ρw·uτ) = ρe+ue+ - ρ+u+
    '''
    check = kwargs.get('check',True)
    rtol  = kwargs.get('rtol',1e-4)
    
    y = np.asarray(y)
    u = np.asarray(u)
    
    ## Assert 0D scalars
    for val in (u_edge, rho_edge):
        if val is not None and not isinstance(val, (float,np.floating)):
            raise ValueError('An arg intended as 0D scalar has non-float type')
    if not isinstance(u_tau,(float,np.floating)):
        raise ValueError('u_tau must be type float')
    
    ## If ρ_edge is passed, then ρ must also be passed
    if rho_edge is not None and rho is None:
        raise ValueError('ρ_edge passed but ρ not passed')
    
    if rho is None: ## no ρ passed, set ρ=const=1 (incomp.)
        rho = np.ones_like(u)
    rho = np.asarray(rho)
    
    _check_validity_yx(y,u)
    _check_validity_yx(y,rho)
    n = y.shape[0]
    j_edge, u_edge = _determine_ju_edge(y,u,j_edge,u_edge,check=check,rtol=rtol)
    _check_validity_jn(j_edge,n)
    if rho_edge is None:
        rho_edge = rho[j_edge]
    
    ## Get/check rho_wall
    if rho_wall is None:
        rho_wall = rho[0]
    np.testing.assert_allclose(rho_wall, rho[0], rtol=1e-4)
    
    Wplus = (rho_edge*u_edge - rho*u) / (rho_wall*u_tau) ## W+
    dRC = cumulative_trapezoid(y=Wplus, x=y, initial=0.)[j_edge] ## Δ = ∫W+dy
    return dRC

def calc_I2(y, u, u_tau, rho=None, j_edge=None, u_edge=None, rho_edge=None, rho_wall=None, **kwargs):
    '''
    Second moment of the velocity defect
    I2 = ∫ (W+)^2 d(y/Δ) = ∫ (W+)^2 dη
    W+ = (ρe·ue - ρ·u)/(ρw·uτ) = ρe+ue+ - ρ+u+
    Δ  = ∫W+dy = ∫(ρe+ue+ - ρ+u+) dy
    -----
    Monkewitz Chauhan Nagib (2007) : https://doi.org/10.1063/1.2780196
    Nagib Chauhan Monkewitz (2007) : https://doi.org/10.1098/rsta.2006.1948
    '''
    check = kwargs.get('check',True)
    rtol  = kwargs.get('rtol',1e-4)
    
    y = np.asarray(y)
    u = np.asarray(u)
    
    ## Assert 0D scalars
    for val in (u_edge, rho_edge):
        if val is not None and not isinstance(val, (float,np.floating)):
            raise ValueError('An arg intended as 0D scalar has non-float type')
    if not isinstance(u_tau,(float,np.floating)):
        raise ValueError('u_tau must be type float')
    
    ## If ρ_edge is passed, then ρ must also be passed
    if rho_edge is not None and rho is None:
        raise ValueError('ρ_edge passed but ρ not passed')
    
    if rho is None: ## no ρ passed, set ρ=const=1 (incomp.)
        rho = np.ones_like(u)
    rho = np.asarray(rho)
    
    _check_validity_yx(y,u)
    _check_validity_yx(y,rho)
    n = y.shape[0]
    j_edge, u_edge = _determine_ju_edge(y,u,j_edge,u_edge,check=check,rtol=rtol)
    _check_validity_jn(j_edge,n)
    if rho_edge is None:
        rho_edge = rho[j_edge]
    
    ## Get/check rho_wall
    if rho_wall is None:
        rho_wall = rho[0]
    np.testing.assert_allclose(rho_wall, rho[0], rtol=1e-4)
    
    ## W+
    Wplus = (rho_edge*u_edge - rho*u) / (rho_wall*u_tau)
    
    dRC = cumulative_trapezoid(y=Wplus, x=y, initial=0.)[j_edge] ## Δ = ∫W+dy
    
    ## I2 = ∫ (W+)^2 d(y/Δ) = ∫ (W+)^2 dη = (1/Δ) ∫ (W+)^2 dy
    I2_dRC = cumulative_trapezoid(y=Wplus**2, x=y, initial=0.)[j_edge]
    
    I2 = I2_dRC / dRC
    
    return I2

def calc_I3(y, u, u_tau, rho=None, j_edge=None, u_edge=None, rho_edge=None, rho_wall=None, **kwargs):
    '''
    Third moment of the velocity defect
    -----
    I3 = ∫ (W+)^3 d(y/Δ) = ∫ (W+)^3 dη
    W+ = (ρe·ue - ρ·u)/(ρw·uτ) = ρe+ue+ - ρ+u+
    Δ  = ∫W+dy = ∫(ρe+ue+ - ρ+u+) dy
    '''
    check = kwargs.get('check',True)
    rtol  = kwargs.get('rtol',1e-4)
    
    y = np.asarray(y)
    u = np.asarray(u)
    
    ## Assert 0D scalars
    for val in (u_edge, rho_edge):
        if val is not None and not isinstance(val, (float,np.floating)):
            raise ValueError('An arg intended as 0D scalar has non-float type')
    if not isinstance(u_tau,(float,np.floating)):
        raise ValueError('u_tau must be type float')
    
    ## If ρ_edge is passed, then ρ must also be passed
    if rho_edge is not None and rho is None:
        raise ValueError('ρ_edge passed but ρ not passed')
    
    if rho is None: ## no ρ passed, set ρ=const=1 (incomp.)
        rho = np.ones_like(u)
    rho = np.asarray(rho)
    
    _check_validity_yx(y,u)
    _check_validity_yx(y,rho)
    n = y.shape[0]
    j_edge, u_edge = _determine_ju_edge(y,u,j_edge,u_edge,check=check,rtol=rtol)
    _check_validity_jn(j_edge,n)
    if rho_edge is None:
        rho_edge = rho[j_edge]
    
    ## Get/check rho_wall
    if rho_wall is None:
        rho_wall = rho[0]
    np.testing.assert_allclose(rho_wall, rho[0], rtol=1e-4)
    
    ## W+
    Wplus = (rho_edge*u_edge - rho*u) / (rho_wall*u_tau)
    
    dRC = cumulative_trapezoid(y=Wplus, x=y, initial=0.)[j_edge] ## Δ = ∫W+dy
    
    ## I3 = ∫ (W+)^3 d(y/Δ) = (1/Δ) ∫ (W+)^3 dy
    I3_dRC = cumulative_trapezoid(y=Wplus**3, x=y, initial=0.)[j_edge]
    
    I3 = I3_dRC / dRC
    
    return I3

# ======================================================================

def calc_wake_parameter_1d(yplus, uplus, dplus, uplus_delta=None, **kwargs):
    '''
    Calculate the Coles wake parameter Π (1D kernel)
    
    Π = (κ/2)·[u+(δ) - (1/κ)·ln(δ+) - B]
    
    Coles profile:
      u+ = (1/κ)·ln(y+) + B + (2Π/κ)·W(y/δ)
        at y=δ, W(y/δ)==1
    
    Within the scope of this function, δ is generic i.e. not necessarily δ99
    
    Refs:
    -----
    Coles (1956)            : https://doi.org/10.1017/S0022112056000135
    Pirozzoli (2004)        : https://doi.org/10.1063/1.1637604
    Smits & Dussauge (2006) : https://doi.org/10.1007/b137383
    Chauhan et al. (2009)   : https://doi.org/10.1088/0169-5983/41/2/021404
    Nagib et al. (2007)     : https://doi.org/10.1098/rsta.2006.1948
    '''
    
    ## Von Kármán constant (κ)
    k = kwargs.get('k',0.384)
    
    ## Log-law intercept (B) : u+ = (1/κ)·ln(y+) + B
    ## see Nagib et al. (2007)
    B = kwargs.get('B',4.173)
    
    interp_kind = kwargs.get('interp_kind','cubic') ## 'linear','cubic'
    
    ## Check input y+,u+
    if (yplus.ndim!=1):
        raise ValueError('yplus must be 1D')
    if (uplus.ndim!=1):
        raise ValueError('uplus must be 1D')
    if (uplus.shape[0]!=yplus.shape[0]):
        raise ValueError("u,y shapes don't match")
    if not np.all(np.diff(yplus) > 0): ## check (+) monotonicity
        raise ValueError("y must be monotonically increasing")
    
    ## Check input δ+ and optional input u+(δ)
    if not isinstance(dplus,(float,np.floating)):
        raise ValueError('dplus must be type float')
    if uplus_delta is not None and not isinstance(uplus_delta,(float,np.floating)):
        raise ValueError('uplus_delta must be type float')
    
    ## u_{log}^+(δ) : Extrapolated u^+(δ) of log-law
    uplus_delta_loglaw = (1/k)*np.log(dplus) + B
    
    ## u+(δ)
    uplus_delta_func = interp1d(yplus, uplus, kind=interp_kind, bounds_error=True)
    uplus_delta_sol  = uplus_delta_func(dplus)
    
    ## If 'uplus_delta' was supplied, perform consistency check
    if uplus_delta is not None:
        np.testing.assert_allclose(uplus_delta_sol, uplus_delta, rtol=1e-5)
    
    uplus_delta = uplus_delta_sol
    
    Π = (k/2)*( uplus_delta - uplus_delta_loglaw )
    
    return Π

def calc_profile_edge_1d(y, ddy_u, **kwargs):
    '''
    Determine the edge index of a 1D boundary-layer profile.
    The edge is defined as the first location where |du/dy|<ϵ.
    
    Note: |-ωz|<ϵ can be found (instead of |du/dy|<ϵ) by passing -ωz as arg 'ddy_u'
    
    Note: The 'ddy_u' arg is automatically normalized by ddy_u[0], whereby ddy_u[0]==1.
      This is effectively a transformation to pseudo-'+' units. The purpose of this is
      to keep consistent sensitivity for the ϵ parameter.
    
    Parameters
    ----------
    y : np.ndarray
        1D wall-normal coordinate (units arbitrary)
    ddy_u : np.ndarray
        Precomputed du/dy
    
    Keyword Arguments
    -----------------
    epsilon : float, default=5e-5
        Edge-detection threshold for |du/dy| (or |ωz|)
    check_eps : bool, default=True
        Abort when no point satisfies |du/dy|<ϵ
    
    Returns
    -------
    y_edge : float
        Wall-normal location of the boundary-layer edge
    j_edge : int
        Index of boundary-layer edge
    '''
    
    epsilon   = kwargs.get('epsilon',5e-5)
    check_eps = kwargs.get('check_eps',True)
    
    ## Checks
    _check_validity_yx(y,ddy_u)
    n = y.shape[0]
    
    ## !!! Normalize such that |du/dy|_w == 1 !!!
    ## This is required for ϵ value/sensitivity to be consistent
    ddy_u = np.copy( ddy_u / ddy_u[0] )
    
    # === Determine j_edge
    
    ## Static ϵ
    j_edge = n-1
    for j in range(n):
        if np.abs(ddy_u[j]) < epsilon: ## |d□/dy|<ϵ
            j_edge = j
            break
    
    # ## Variable ϵ
    # keep_going = True
    # while keep_going:
    #     j_edge = n-1
    #     for j in range(n):
    #         if np.abs(ddy_u[j]) < epsilon: ## |d□/dy|<ϵ
    #             j_edge = j
    #             break
    #     if j_edge==n-1: ## Got to end, recalibrate ϵ & keep going
    #         epsilon *= 1.05
    #         msg = f'[WARNING] Recalibrating: ϵ={epsilon:0.3e}'
    #         #print(msg)
    #         tqdm.write(msg)
    #     else:
    #         keep_going = False
    
    if j_edge<3: ## Less than 3 points in profile
        raise ValueError('j_edge<3')
    if np.abs(ddy_u[j_edge])>=epsilon and check_eps:
        print('\n')
        print(f'[ERROR] j_edge={j_edge:d}')
        print(f'[ERROR] abs(ddy_u[{j_edge:d}])={np.abs(ddy_u[j_edge])}, ϵ={epsilon:0.3e}')
        print('\n')
        raise ValueError
    
    ## First point satisfying |d□/dy|<ϵ
    y_edge = float( y[j_edge] )
    
    if False: ## LEGACY: Find interpolated |d□/dy|==ϵ
        
        intrp_func = PchipInterpolator(y, ddy_u, axis=0, extrapolate=False)
        
        def __f_opt_edge_locator(y_test, intrp_func, epsilon):
            ddy_u_test = intrp_func(y_test)
            root = np.abs( ddy_u_test ) - epsilon
            return root
        
        sol = least_squares(
                    fun=__f_opt_edge_locator,
                    args=(intrp_func,epsilon,),
                    x0 = y[0] + 0.99*(y[j_edge]-y[0]),
                    xtol=1e-12,
                    ftol=1e-12,
                    gtol=1e-12,
                    method='trf',
                    bounds=(y[0], y[j_edge]),
                    )
        if not sol.success:
            raise ValueError
        if ( sol.x.shape[0] != 1 ):
            raise ValueError
        
        y_edge = float(sol.x[0])
        
        if ( y_edge > y[j_edge] ):
            raise ValueError
    
    ## Debug plot
    # import matplotlib.pyplot as plt
    # plt.close('all')
    # fig1 = plt.figure(figsize=(2*(16/9),2), dpi=300)
    # ax1 = plt.gca()
    # ax1.set_xscale('log', base=10)
    # ax1.plot(ddy_u, y, lw=0.8, )
    # #ax1.set_xlim(1e-30, 1e1)
    # ax1.axhline(y=y_edge, linestyle='dashed', c='gray', zorder=1, lw=0.5)
    # ax1.axvline(x=epsilon, linestyle='dashed', c='gray', zorder=1, lw=0.5)
    # fig1.tight_layout(pad=0.25)
    # plt.show()
    
    return y_edge, j_edge

def calc_d99_1d(y, u, j_edge=None, u_edge=None, **kwargs):
    '''
    Determine δ99 location of 1D profile
    - y : 1D coordinate vector
    - u : Profile variable (streamwise velocity u, pseudovelocity ŭ)
    - j_edge : (optional) edge index
    - u_edge : (optional) edge value
    '''
    interp_kind = kwargs.get('interp_kind','cubic')
    check = kwargs.get('check',True)
    rtol = kwargs.get('rtol',1e-4)
    
    y = np.asarray(y)
    u = np.asarray(u)
    
    ## Assert 0D scalars
    if u_edge is not None and not isinstance(u_edge, (float,np.floating)):
        raise ValueError('u_edge must be None or float')
    
    _check_validity_yx(y,u)
    n = y.shape[0]
    j_edge, u_edge = _determine_ju_edge(y,u,j_edge,u_edge,check=check,rtol=rtol)
    _check_validity_jn(j_edge,n)
    y_edge = y[j_edge]
    
    ## Index vs slice semantics
    ## If e.g. j_edge==-1, then [:j_edge] doesnt take last value, whereas
    ##   if j_edge==n, then [:j_edge] will take last value. This step makes
    ##   a 'slice' selector 'sl' which is negative-index consistent.
    if j_edge == -1:
        sl = slice(None) ## Take everything
    else:
        sl = slice(j_edge+1) ## Inclusive semantics
    
    ## Primary u(y) interpolation callable
    intrp_func = interp1d(
        x=y[sl],
        y=u[sl],
        kind=interp_kind,
        bounds_error=True,
        )
    
    ## Debug plot
    #import matplotlib as mpl
    #import matplotlib.pyplot as plt
    #plt.close('all')
    #fig1 = plt.figure(figsize=(5,5), dpi=200)
    #ax1 = fig1.gca()
    #ax1.plot(y[sl],u[sl],marker='o')
    #ax1.plot(y[sl],intrp_func(y[sl]),c='pink')
    
    ## Does the solution/intersection actually exist?
    if u[sl].max() < u_edge*0.99:
        print('\n')
        print(f'[ERROR] u.max()     = {u[sl].max():0.12f}')
        print(f'[ERROR] u_edge*0.99 = {u_edge*0.99:0.12f}')
        print('[ERROR] No solution exists: u.max() < u_edge*0.99')
        print('\n')
        raise RuntimeError
    
    ## Optimizer: callable root function for determining δ99
    def __f_opt_d99_locator(y_test, intrp_func, u_edge):
        root = 0.99*u_edge - intrp_func(y_test)
        return root
    
    # ## Perform least-squares solve
    # sol = least_squares(
    #         fun=__f_opt_d99_locator,
    #         args=(intrp_func,u_edge),
    #         x0=0.,
    #         xtol=1e-12,
    #         ftol=1e-12,
    #         gtol=1e-12,
    #         method='trf',
    #         bounds=(y.min(), y_edge),
    #         )
    # if not sol.success:
    #     raise ValueError(sol.message)
    # d99 = float(sol.x[0]) ## δ99
    
    # === Get 'root_scalar' bracket indices
    
    eps = np.finfo(u.dtype).eps * 10. ## Float comparison tolerance
    
    ## First pass: get bracket upper bound (index right above FIRST discrete crossing)
    j_bracket_high = None
    for j in range(y[sl].shape[0]):
        if u[j] - 0.99*u_edge > eps:
            j_bracket_high = j
            break
    if j_bracket_high is None:
        raise RuntimeError('Could not find bracket high')
    
    ## Second pass for lower bracket bound
    j_bracket_low = None
    for jj in range(j_bracket_high):
        j = j_bracket_high-jj
        if u[j] - 0.99*u_edge < -eps:
            j_bracket_low = j
            break
    if j_bracket_low is None:
        raise RuntimeError('Could not find bracket low')
    
    ## Perform solve with 'root_scalar'
    sol = root_scalar(
            f=__f_opt_d99_locator,
            args=(intrp_func,u_edge),
            method="brentq",
            bracket=(y[j_bracket_low],y[j_bracket_high]),
            xtol=1e-12,
            rtol=1e-12,
            )
    if not sol.converged:
        raise ValueError
    d99 = float(sol.root) ## δ99
    
    ## Check solution is within bounds
    if d99 > y_edge:
        raise ValueError('δ99 > y_edge')
    if d99 < y.min():
        raise ValueError('δ99 < y.min()')
    
    ## Debug plot
    # if not np.isclose(0.99*u_edge, u99, rtol=1e-5):
    #     ax1.axhline(y=u_edge, ls='solid', c='purple')
    #     ax1.axhline(y=0.99*u_edge, ls='solid', c='orange')
    #     ax1.axvline(x=d99, ls='solid', c='red')
    #     plt.show()
    
    ## Final assertion: u(δ99)==0.99·u_edge
    u99 = intrp_func(d99)
    np.testing.assert_allclose(0.99*u_edge, u99, rtol=1e-5)
    
    return d99

def calc_bl_integral_quantities_1d(
    y,
    u,
    rho,
    d99,
    u_tau, rho_wall, mu_wall,
    u_edge, rho_edge, mu_edge,
    j_edge,
    **kwargs,
    ):
    '''
    Convenience wrapper to calculating several integral metrics at once
    -----
    All inputs should be dimensional!
    1D vectors: y,u,rho
    0D scalars: d99, u_tau, rho_wall, mu_wall, u_edge, rho_edge, mu_edge
    0D index: j_edge
    
    Returns
    -------
    dd : dict
      δ1=δ*, δ2=θ, δ3, H12, H32, Reθ, Reτ, Reδ99, ...
    '''
    check = kwargs.get('check',True)
    rtol  = kwargs.get('rtol',1e-4)
    
    y   = np.asarray(y)
    u   = np.asarray(u)
    rho = np.asarray(rho)
    _check_validity_yx(y,u)
    _check_validity_yx(y,rho)
    n = y.shape[0]
    _check_validity_jn(j_edge,n)
    
    ## Assert 0D scalars
    for val in (d99, u_tau, rho_wall, mu_wall, u_edge, rho_edge, mu_edge):
        if not isinstance(val, (float,np.floating)):
            raise ValueError('An arg intended as 0D scalar has non-float type')
    
    # ## Consistency checks for edge quantities
    # if check:
    #     np.testing.assert_allclose(u_edge   , u[j_edge]   , rtol=rtol)
    #     np.testing.assert_allclose(rho_edge , rho[j_edge] , rtol=rtol)
    
    # === Compressible integrals (root names)
    
    d1 = calc_d1(
        y, u,
        rho=rho,
        j_edge=j_edge,
        u_edge=u_edge,
        rho_edge=rho_edge,
        check=check,
        rtol=rtol,
        )
    dstar = d1
    
    d2 = calc_d2(
        y, u,
        rho=rho,
        j_edge=j_edge,
        u_edge=u_edge,
        rho_edge=rho_edge,
        check=check,
        rtol=rtol,
        )
    theta = d2
    
    d3 = calc_d3(
        y, u,
        rho=rho,
        j_edge=j_edge,
        u_edge=u_edge,
        rho_edge=rho_edge,
        check=check,
        rtol=rtol,
        )
    
    dRC = calc_dRC(
        y, u,
        u_tau=u_tau,
        rho=rho,
        j_edge=j_edge,
        u_edge=u_edge,
        rho_edge=rho_edge,
        rho_wall=rho_wall,
        check=check,
        rtol=rtol,
        )
    
    I2 = calc_I2(
        y, u,
        u_tau=u_tau,
        rho=rho,
        j_edge=j_edge,
        u_edge=u_edge,
        rho_edge=rho_edge,
        rho_wall=rho_wall,
        check=check,
        rtol=rtol,
        )
    
    I3 = calc_I3(
        y, u,
        u_tau=u_tau,
        rho=rho,
        j_edge=j_edge,
        u_edge=u_edge,
        rho_edge=rho_edge,
        rho_wall=rho_wall,
        check=check,
        rtol=rtol,
        )
    
    # === Kinetic (u-only) integrals
    
    d1_k = calc_d1(
        y, u,
        rho=None, ## !! ρ ignored
        j_edge=j_edge,
        u_edge=u_edge,
        rho_edge=None, ## !! ρ ignored
        check=check,
        rtol=rtol,
        )
    dstar_k = d1_k
    
    d2_k = calc_d2(
        y, u,
        rho=None, ## !! ρ ignored
        j_edge=j_edge,
        u_edge=u_edge,
        rho_edge=None, ## !! ρ ignored
        check=check,
        rtol=rtol,
        )
    theta_k = d2_k
    
    d3_k = calc_d3(
        y, u,
        rho=None, ## !! ρ ignored
        j_edge=j_edge,
        u_edge=u_edge,
        rho_edge=None, ## !! ρ ignored
        check=check,
        rtol=rtol,
        )
    
    dRC_k = calc_dRC(
        y, u,
        u_tau=u_tau,
        rho=None, ## !! ρ ignored
        j_edge=j_edge,
        u_edge=u_edge,
        rho_edge=None, ## !! ρ ignored
        rho_wall=None, ## !! ρ ignored
        check=check,
        rtol=rtol,
        )
    
    I2_k = calc_I2(
        y, u,
        u_tau=u_tau,
        rho=None, ## !! ρ ignored
        j_edge=j_edge,
        u_edge=u_edge,
        rho_edge=None, ## !! ρ ignored
        rho_wall=None, ## !! ρ ignored
        check=check,
        rtol=rtol,
        )
    
    I3_k = calc_I3(
        y, u,
        u_tau=u_tau,
        rho=None, ## !! ρ ignored
        j_edge=j_edge,
        u_edge=u_edge,
        rho_edge=None, ## !! ρ ignored
        rho_wall=None, ## !! ρ ignored
        check=check,
        rtol=rtol,
        )
    
    ## Shape factors
    H12    = d1   / d2
    H12_k  = d1_k / d2_k
    H32    = d3   / d2
    H32_k  = d3_k / d2_k
    
    ## Reynolds numbers
    Re_tau     = d99     * u_tau  * rho_wall / mu_wall ## Reτ   = δ99·uτ·ρw / μw
    Re_theta   = theta   * u_edge * rho_edge / mu_edge ## Reθ   = θ·ue·ρe / μe
    Re_dstar   = dstar   * u_edge * rho_edge / mu_edge ## Reδ*  = δ*·ue·ρe / μe
    Re_d2      = theta   * u_edge * rho_edge / mu_wall ## Reδ2  = θ·ue·ρe / μw
    Re_d99     = d99     * u_edge * rho_edge / mu_edge ## Reδ99 = δ99·ue·ρe / μe
    Re_theta_k = theta_k * u_edge * rho_edge / mu_edge ## Reθk  = θk·ue·ρe / μe
    Re_dstar_k = dstar_k * u_edge * rho_edge / mu_edge ## Reδ*k = δ*k·ue·ρe / μe
    
    ## Dictionary to return
    dd = {
        'd1':d1,
        'd1_k':d1_k,
        'dstar':dstar,
        'dstar_k':dstar_k,
        
        'd2':d2,
        'd2_k':d2_k,
        'theta':theta,
        'theta_k':theta_k,
        
        'd3':d3,
        'd3_k':d3_k,
        
        'dRC':dRC,
        'dRC_k':dRC_k,
        
        'H12':H12,
        'H12_k':H12_k,
        'H32':H32,
        'H32_k':H32_k,
        
        'I2':I2,
        'I2_k':I2_k,
        'I3':I3,
        'I3_k':I3_k,
        
        'Re_tau':Re_tau,
        'Re_theta':Re_theta,
        'Re_dstar':Re_dstar,
        'Re_d2':Re_d2,
        'Re_d99':Re_d99,
        'Re_theta_k':Re_theta_k,
        'Re_dstar_k':Re_dstar_k,
        }
    
    return dd
