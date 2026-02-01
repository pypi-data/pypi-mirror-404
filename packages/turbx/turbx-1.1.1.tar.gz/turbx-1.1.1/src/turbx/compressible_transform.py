import numpy as np
from scipy.integrate import cumulative_trapezoid

from .gradient import gradient

# ======================================================================

def comp_transform_TL(y,u,utau,rho,mu,**kwargs):
    '''
    Trettel & Larsson (2016)
    https://doi.org/10.1063/1.4942022
    '''
    acc          = kwargs.get('acc',6)
    edge_stencil = kwargs.get('edge_stencil','full')
    ddy_rho      = kwargs.get('ddy_rho',None)
    ddy_mu       = kwargs.get('ddy_mu',None)
    
    ## Calculate if not passed
    if ddy_rho is None:
        ddy_rho = gradient(rho, y, acc=acc, edge_stencil=edge_stencil)
    if ddy_mu is None:
        ddy_mu = gradient(mu, y, acc=acc, edge_stencil=edge_stencil)
    
    rho_w     = rho[0]
    mu_w      = mu[0]
    u_plus    = u / utau
    tau_wall  = rho_w * utau**2
    sc_l_in   = mu_w / ( utau * rho_w ) ## δν
    #y_plus    = y * utau * rho_w / mu_w
    
    ## Eq.28
    bracket   = 1. + ((1./(2.*rho))*ddy_rho*y) - ((1/mu)*ddy_mu*y)
    integrand = np.sqrt(rho/rho_w) * bracket
    uTL_plus  = cumulative_trapezoid(y=integrand, x=u_plus, initial=0.) ## U+
    
    u_sl = np.sqrt( tau_wall / rho ) ## semilocal friction velocity (NOT transformed U+)
    y_sl = y * u_sl * rho / mu       ## semilocal coordinate
    
    ## Re-dimensionalize first two returned profiles by uτ,δν
    return uTL_plus*utau, y_sl*sc_l_in, uTL_plus, y_sl

def comp_transform_VD(u,rho):
    '''
    van Driest velocity transform
    uVD(y) = ∫ √(ρ/ρ_w) du
    van Driest (1951)
    https://doi.org/10.2514/8.1895
    '''
    rho_w     = rho[0]
    integrand = np.sqrt(rho/rho_w)
    uVD       = cumulative_trapezoid(y=integrand, x=u, initial=0.)
    return uVD

def comp_transform_VIPL(y,u,rho,mu,a=1.5,b=0.5):
    '''
    Volpiani et al. (2020)
    https://doi.org/10.1103/PhysRevFluids.5.052602
    '''
    rho_w = rho[0]
    mu_w  = mu[0]
    M     = mu/mu_w
    R     = rho/rho_w
    F     = R**b * M**(-a)
    yVP   = cumulative_trapezoid(y=F, x=y, initial=0.)
    G     = R**b * M**(1-a)
    uVP   = cumulative_trapezoid(y=G, x=u, initial=0.)
    return uVP,yVP

def comp_transform_GFM(y,uFv,rho,mu,r_uII_vII,utau,ddy_u_Fv=None,acc=6,edge_stencil='full'):
    '''
    Griffin, Fu & Moin (2021)
    https://doi.org/10.1073/pnas.2111144118
    '''
    if ddy_u_Fv is None:
        ddy_u_Fv = gradient(uFv, y, acc=acc, edge_stencil=edge_stencil)
    
    ny       = y.shape[0]
    rho_w    = rho[0]
    mu_w     = mu[0]
    tau_wall = utau**2 * rho_w
    sc_l_in  = mu_w / ( utau * rho_w ) ## δν
    y_plus   = y * utau * rho_w / mu_w
    uFv_plus = uFv / utau
    mu_plus  = mu  / mu_w
    
    tau_visc_plus = mu * ddy_u_Fv / tau_wall    ## τv+
    tau_R_plus    = -1. * r_uII_vII / tau_wall ## τR+
    tau_plus      = tau_visc_plus + tau_R_plus ## τ+
    
    u_sl = np.sqrt( tau_wall / rho ) ## u_{sl} : semilocal friction velocity
    #sc_l_sl = mu / ( u_sl * rho )    ## ℓ_{sl} : semilocal length scale
    y_star  = y * u_sl * rho / mu    ## y* = y_{sl} = y/ℓ_{sl} : semilocal coordinate
    
    duFvplus_dyplus = gradient(uFv_plus, y_plus, acc=acc, edge_stencil=edge_stencil)
    duFvplus_dystar = gradient(uFv_plus, y_star, acc=acc, edge_stencil=edge_stencil)
    
    #duFvplus_dyplus = ddy_u_Fv / (utau / sc_l_in) ## ∂[uFv+]/∂y+ -- OK, sc_l_in is a constant over [y]
    #duFvplus_dystar = ddy_u_Fv / (utau / sc_l_sl) ## ∂[uFv+]/∂y* -- WRONG, sc_l_sl is NOT constant over [y]
    
    # np.testing.assert_allclose(
    #     duFvplus_dyplus,
    #     gradient(uFv_plus, y_plus, acc=acc, edge_stencil=edge_stencil),
    #     rtol=1e-6,
    #     atol=1e-12,
    #     )
    
    # np.testing.assert_allclose(
    #     duFvplus_dystar,
    #     gradient(uFv_plus, y_star, acc=acc, edge_stencil=edge_stencil),
    #     rtol=1e-6,
    #     atol=1e-12,
    #     )
    
    S_eq_plus = (1./mu_plus) * duFvplus_dystar ## Eq.1
    S_TL_plus = mu_plus * duFvplus_dyplus      ## Eq.2
    
    ## Eq.4 St+ = [τ+·Seq+] / [ τ+ + Seq+ - STL+ ]
    A = tau_plus * S_eq_plus
    B = tau_plus + S_eq_plus - S_TL_plus
    B = np.where(np.abs(B) < 1e-12, 1e-12, B)
    S_t_plus = A / B
    
    ## Eq.3 Assertion
    if False:
        ratio_v = np.full((ny,),0.,dtype=np.float64)
        ratio_R = np.full((ny,),0.,dtype=np.float64)
        np.divide(tau_visc_plus, S_TL_plus, out=ratio_v, where=np.abs(S_TL_plus) > 1e-12)
        np.divide(tau_R_plus,    S_eq_plus, out=ratio_R, where=np.abs(S_eq_plus) > 1e-12)
        tau_plus_chk = S_t_plus * (ratio_v + ratio_R)
        mask = ( (np.abs(S_TL_plus) > 1e-12) & (np.abs(S_eq_plus) > 1e-12) )
        np.testing.assert_allclose(
            tau_plus[mask],
            tau_plus_chk[mask],
            rtol=1e-6,
            )
    
    ## Ut+[y*] = ∫St+ dy*
    uGFM_plus = cumulative_trapezoid(y=S_t_plus, x=y_star, initial=0.)
    
    ## Re-dimensionalize first two returned profiles by uτ,δν
    return uGFM_plus*utau, y_star*sc_l_in, uGFM_plus, y_star
