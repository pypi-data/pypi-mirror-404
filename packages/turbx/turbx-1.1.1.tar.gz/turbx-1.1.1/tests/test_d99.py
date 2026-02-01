#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import matplotlib.pyplot as plt
import numpy as np
from scipy.integrate import cumulative_trapezoid, trapezoid
from scipy.optimize import least_squares

from turbx import (
    Blasius_solution,
    calc_d1,
    calc_d2,
    calc_d3,
    calc_d99_1d,
    calc_profile_edge_1d,
    gradient,
)

'''
========================================================================
TODO: Make this into a test!
========================================================================
'''

# main()
# ======================================================================

if __name__ == '__main__':
    
    # === Get η99 of Blasius solution
    
    def __f_opt_eta99(eta99):
        _, fp, _ = Blasius_solution(eta99)
        root = fp - 0.99
        return root
    
    sol = least_squares(
        __f_opt_eta99,
        x0=[5.0],
        bounds=(0.,20.),
        xtol=1e-11,
        gtol=1e-11,
        method='trf',
        )
    eta99 = float(sol.x[0])
    print(f'η99 = {eta99:0.14f}') ## 4.90998951330668
    
    # === Make Blasius data
    
    n        = 200
    eta      = np.linspace(0,20,n) ## η
    #eta      = np.linspace(0,3,n) ## η
    y_ov_d99 = np.copy( eta / eta99 )
    
    # ===
    
    f, fp, fpp = Blasius_solution(eta)
    
    ## Plot
    plt.close('all')
    plt.rcParams.update({'font.size': 9})
    fig1 = plt.figure(figsize=(5.31/2,4), dpi=200)
    ax1 = plt.gca()
    ax1.plot(fp,y_ov_d99,c='red',lw=0.6)
    #ax1.set_ylim(0,1.5)
    ax1.set_ylim(bottom=0)
    ax1.set_ylabel(r'$y/\delta_{99}$')
    ax1.set_xlim(0,1.05)
    ax1.set_xlabel(r'$u/U_\infty$')
    fig1.tight_layout(pad=0.25)
    #plt.show()
    
    # === Dimensionalize data & get BL parameters
    
    U_inf = 5.     ## m/s
    nu    = 1.5e-5 ## m^2/s
    x     = 200.   ## m
    Re_x  = U_inf * x / nu
    
    y = np.copy( eta * np.sqrt(nu * x / U_inf) )
    u = U_inf * fp
    
    c0     = 0.3320573362149271
    u_tau  = U_inf * np.sqrt(c0) * Re_x**(-1/4)
    d99    = eta99 * np.sqrt(nu * x / U_inf)
    dnu    = nu / u_tau
    Re_tau = u_tau * d99 / nu
    print(f'Reτ = {Re_tau:0.14f}')
    np.testing.assert_allclose(Re_tau, eta99*np.sqrt(c0)*Re_x**(1/4), rtol=1e-11)
    np.testing.assert_allclose(Re_tau, d99/dnu, rtol=1e-11)
    
    uplus = np.copy( u / u_tau )
    yplus = np.copy( y / dnu   )
    
    uplus_inf = U_inf / u_tau
    cf        = 2/uplus_inf**2
    print(f'1000*cf = {1000*cf:0.14f}')
    
    # ===
    
    # def kernel_d1(eta):
    #     _,fp,_ = Blasius_solution(eta)
    #     return 1. - fp
    # 
    # def kernel_d2(eta):
    #     _,fp,_ = Blasius_solution(eta)
    #     return fp * (1. - fp)
    # 
    # def kernel_d3(eta):
    #     _,fp,_ = Blasius_solution(eta)
    #     return fp * (1. - fp*fp)
    
    # ## δ1 = c1 * sqrt(nu*x/U_inf)
    # ## δ2 = c2 * sqrt(nu*x/U_inf)
    # ## δ3 = c3 * sqrt(nu*x/U_inf)
    # from scipy.integrate import quad
    # c1, err = quad(kernel_d1, 0., 50., epsabs=1e-9, epsrel=1e-9, limit=int(1e3))
    # c2, err = quad(kernel_d2, 0., 50., epsabs=1e-9, epsrel=1e-9, limit=int(1e3))
    # c3, err = quad(kernel_d3, 0., 50., epsabs=1e-9, epsrel=1e-9, limit=int(1e3))
    # print(f'c1={c1:0.12f}')
    # print(f'c2={c2:0.12f}')
    # print(f'c3={c3:0.12f}')
    
    c1 = 1.720787657522
    c2 = 0.664114672431
    c3 = 1.044375475238
    
    ## Analytical δn
    d1 = c1 * np.sqrt(nu*x/U_inf)
    d2 = c2 * np.sqrt(nu*x/U_inf)
    d3 = c3 * np.sqrt(nu*x/U_inf)
    
    H12 = d1/d2
    H32 = d3/d2
    
    ## Assert: analytical δn vs numerical δn
    ## - these are grid-dependent
    np.testing.assert_allclose(d1, calc_d1(y=y,u=u), rtol=(1/n))
    np.testing.assert_allclose(d2, calc_d2(y=y,u=u), rtol=(1/n))
    np.testing.assert_allclose(d3, calc_d3(y=y,u=u), rtol=(1/n))
    
    ## Assert: calc_d1(), numerical only, using u_edge=u[-1]
    ## - should be identical to machine tolerance
    np.testing.assert_allclose(
        trapezoid(y=1.-(u/u[-1]), x=y),
        calc_d1(y=y,u=u),
        rtol=1e-11,
        )
    
    ## Assert: calc_d1(), numerical only, using u_edge=U_inf
    ## - should be identical to machine tolerance
    np.testing.assert_allclose(
        trapezoid(y=1.-(u/U_inf), x=y),
        calc_d1(y=y,u=u,u_edge=U_inf),
        rtol=1e-11,
        )
    
    # ==================================================================
    # Determine an edge (don't just use last index)
    # ==================================================================
    
    ddy_u = gradient(u=u,x=y,acc=6,edge_stencil='full')
    
    y_edge,j_edge = calc_profile_edge_1d(y=y, ddy_u=ddy_u, epsilon=1e-6, check_eps=False)
    
    ## Assert: calc_d1(), numerical only, using u_edge=U_inf
    ## - should be identical to machine tolerance
    np.testing.assert_allclose(
        cumulative_trapezoid(y=1.-(u/U_inf), x=y, initial=0.)[j_edge],
        calc_d1(y=y,u=u,u_edge=U_inf,j_edge=j_edge),
        rtol=1e-11,
        )
    
    ## Assert: calc_d2(), numerical only, using u_edge=U_inf
    ## - should be identical to machine tolerance
    np.testing.assert_allclose(
        cumulative_trapezoid(y=(u/U_inf)*(1.-(u/U_inf)), x=y, initial=0.)[j_edge],
        calc_d2(y=y,u=u,u_edge=U_inf,j_edge=j_edge),
        rtol=1e-11,
        )
    
    ## Assert: calc_d3(), numerical only, using u_edge=U_inf
    ## - should be identical to machine tolerance
    np.testing.assert_allclose(
        cumulative_trapezoid(y=(u/U_inf)*(1.-(u/U_inf)**2), x=y, initial=0.)[j_edge],
        calc_d3(y=y,u=u,u_edge=U_inf,j_edge=j_edge),
        rtol=1e-11,
        )
    
    # ==================================================================
    # δ99
    # ==================================================================
    
    ## Assert: analytical δ99 vs numerical δ99
    np.testing.assert_allclose(
        d99,
        calc_d99_1d(y=y, u=u, u_edge=U_inf),
        rtol=1e-5,
        )
    
    ## Assert: analytical δ99 vs numerical δ99
    np.testing.assert_allclose(
        d99,
        calc_d99_1d(y=y, u=u, u_edge=U_inf, j_edge=j_edge),
        rtol=1e-5,
        )
