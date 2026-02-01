import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import fsolve

# ======================================================================


def Blasius_solution(eta,c0=0.3320573362149271):
    '''
    Blasius similarity ODE:
        f‴ + (1/2)·f·f″ = 0
    
    BCs:
        f(0)=0,  f′(0)=0,  f′(∞)=1
    
    State:
        y=[f, f′, f″],  y′=[f′, f″, -(1/2)·f·f″]
    
    Returns:
        f(η), f′(η)=u/U∞, f″(η)
    '''
    
    scalar_input = np.isscalar(eta)
    eta = np.atleast_1d(np.asarray(eta, dtype=float))
    
    if eta.size > 1 and not np.all(np.diff(eta) > 0):
        raise ValueError("eta must be strictly increasing")
    
    def Blasius_rhs(_,y): ## _ is dummy 't' for solve_ivp
        f, fp, fpp = y
        return [fp, fpp, -0.5 * f * fpp]
    
    ## Shooting for f′′(0)
    if False:
        
        def residual(c0):
            sol = solve_ivp(
                Blasius_rhs,
                (0., eta_test[-1]),
                y0=[0., 0., float(c0)],
                method='RK45',
                atol=1e-12,
                rtol=1e-12
                )
            return 1. - sol.y[1, -1]
        
        eta_test = np.linspace(0., 20., int(1e4))
        
        c0 = fsolve(
                residual,
                x0=0.33205733621490,
                xtol=1e-12
                )[0]
        print(f'c0={c0:0.16f}')
    
    ## Integration
    sol = solve_ivp(
            Blasius_rhs,
            (0., eta[-1]),
            y0=[0., 0., c0],
            method='RK45',
            atol=1e-12,
            rtol=1e-12,
            dense_output=True
            )
    
    if not sol.success:
        raise RuntimeError(sol.message)
    
    f, fp, fpp = sol.sol(eta)
    
    if scalar_input:
        return f[0], fp[0], fpp[0]
    
    return f, fp, fpp
