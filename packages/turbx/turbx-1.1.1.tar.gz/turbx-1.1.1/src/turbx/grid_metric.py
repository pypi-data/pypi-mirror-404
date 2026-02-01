import timeit

import numpy as np
from tqdm import tqdm

from .gradient import gradient
from .utils import even_print

# ======================================================================

def get_metric_tensor_2d(x2d, y2d, acc=2, edge_stencil='full', **kwargs):
    '''
    Compute the grid metric tensor (inverse of grid Jacobian) for a 2D grid
    -----
    Computational Fluid Mechanics and Heat Transfer (2012) Pletcher, Tannehill, Anderson
    p.266-270, 335-337, 652
    '''
    
    verbose = kwargs.get('verbose',False)
    no_warn = kwargs.get('no_warn',False)
    
    if not isinstance(x2d, np.ndarray):
        raise ValueError('x2d should be of type np.ndarray')
    if not isinstance(y2d, np.ndarray):
        raise ValueError('y2d should be of type np.ndarray')
    
    if (x2d.ndim!=2):
        raise ValueError('x2d should have ndim=2 (xy)')
    if (y2d.ndim!=2):
        raise ValueError('y2d should have ndim=2 (xy)')
    
    if not (x2d.shape==y2d.shape):
        raise ValueError('x2d.shape!=y2d.shape')
    
    nx,ny = x2d.shape
    
    ## the 'computational' grid (unit Cartesian)
    ## --> [x_comp,y_comp]= [ξ,η] = [q1,q2]
    #x_comp = np.arange(nx, dtype=np.float64)
    #y_comp = np.arange(ny, dtype=np.float64)
    x_comp = 1.
    y_comp = 1.
    
    # === get Jacobian :: ∂(x,y)/∂(q1,q2)
    
    t_start = timeit.default_timer()
    
    dxdx = gradient(x2d, x_comp, axis=0, d=1, acc=acc, edge_stencil=edge_stencil, no_warn=no_warn)
    dydx = gradient(y2d, x_comp, axis=0, d=1, acc=acc, edge_stencil=edge_stencil, no_warn=no_warn)
    dxdy = gradient(x2d, y_comp, axis=1, d=1, acc=acc, edge_stencil=edge_stencil, no_warn=no_warn)
    dydy = gradient(y2d, y_comp, axis=1, d=1, acc=acc, edge_stencil=edge_stencil, no_warn=no_warn)
    
    J = np.stack((np.stack((dxdx, dydx), axis=2),
                  np.stack((dxdy, dydy), axis=2)), axis=3)
    
    t_delta = timeit.default_timer() - t_start
    if verbose: tqdm.write( even_print('get J','%0.3f [s]'%(t_delta,), s=True) )
    
    # === get metric tensor M = J^-1 = ∂(q1,q2)/∂(x,y) = ∂(ξ,η)/∂(x,y)
    
    if False: ## method 1
        
        t_start = timeit.default_timer()
        
        M = np.linalg.inv(J)
        
        # M_bak = np.copy(M)
        # M = np.zeros((nx,ny,2,2),dtype=np.float64)
        # for i in range(nx):
        #     for j in range(ny):
        #         M[i,j,:,:] = sp.linalg.inv( J[i,j,:,:] )
        # np.testing.assert_allclose(M_bak, M, atol=1e-12, rtol=1e-12)
        # print('check passed')
        
        t_delta = timeit.default_timer() - t_start
        if verbose: tqdm.write( even_print('get M','%0.3f [s]'%(t_delta,), s=True) )
    
    if True: ## method 2
        
        if ('M' in locals()):
            M_bak = np.copy(M)
            M = None; del M
        
        t_start = timeit.default_timer()
        
        ## Jacobian determinant
        Jac_det = dxdx*dydy - dydx*dxdy
        
        # Jac_det_bak = np.copy(Jac_det)
        # Jac_det = None; del Jac_det
        # Jac_det = np.linalg.det(J)
        # np.testing.assert_allclose(Jac_det, Jac_det_bak, atol=1e-14, rtol=1e-14)
        # print('check passed')
        
        M = np.zeros((nx,ny,2,2), dtype=np.float64)
        M[:,:,0,0] = +dydy / Jac_det ## ξ_x
        M[:,:,0,1] = -dxdy / Jac_det ## ξ_y
        M[:,:,1,0] = -dydx / Jac_det ## η_x
        M[:,:,1,1] = +dxdx / Jac_det ## η_y
        
        t_delta = timeit.default_timer() - t_start
        if verbose: tqdm.write( even_print('get M','%0.3f [s]'%(t_delta,), s=True) )
        
        if ('M_bak' in locals()):
            np.testing.assert_allclose(M[:,:,0,0], M_bak[:,:,0,0], atol=1e-14, rtol=1e-14)
            print('check passed: ξ_x')
            np.testing.assert_allclose(M[:,:,0,1], M_bak[:,:,0,1], atol=1e-14, rtol=1e-14)
            print('check passed: ξ_y')
            np.testing.assert_allclose(M[:,:,1,0], M_bak[:,:,1,0], atol=1e-14, rtol=1e-14)
            print('check passed: η_x')
            np.testing.assert_allclose(M[:,:,1,1], M_bak[:,:,1,1], atol=1e-14, rtol=1e-14)
            print('check passed: η_y')
            np.testing.assert_allclose(M, M_bak, atol=1e-14, rtol=1e-14)
            print('check passed: M')
    
    return M

def get_metric_tensor_3d(x3d, y3d, z3d, acc=2, edge_stencil='full', **kwargs):
    '''
    Compute the grid metric tensor (inverse of grid Jacobian) for a 3D grid
    -----
    Computational Fluid Mechanics and Heat Transfer (2012) Pletcher, Tannehill, Anderson
    p.266-270, 335-337, 652
    '''
    
    verbose = kwargs.get('verbose',False)
    no_warn = kwargs.get('no_warn',False)
    
    if not isinstance(x3d, np.ndarray):
        raise ValueError('x3d should be of type np.ndarray')
    if not isinstance(y3d, np.ndarray):
        raise ValueError('y3d should be of type np.ndarray')
    if not isinstance(z3d, np.ndarray):
        raise ValueError('z3d should be of type np.ndarray')
    
    if (x3d.ndim!=3):
        raise ValueError('x3d should have ndim=3 (xyz)')
    if (y3d.ndim!=3):
        raise ValueError('y3d should have ndim=3 (xyz)')
    if (z3d.ndim!=3):
        raise ValueError('z3d should have ndim=3 (xyz)')
    
    if not (x3d.shape==y3d.shape):
        raise ValueError('x3d.shape!=y3d.shape')
    if not (y3d.shape==z3d.shape):
        raise ValueError('y3d.shape!=z3d.shape')
    
    nx,ny,nz = x3d.shape
    
    ## the 'computational' grid (unit Cartesian)
    ## --> [x_comp,y_comp,z_comp ]= [ξ,η,ζ] = [q1,q2,q3]
    #x_comp = np.arange(nx, dtype=np.float64)
    #y_comp = np.arange(ny, dtype=np.float64)
    #z_comp = np.arange(nz, dtype=np.float64)
    x_comp = 1.
    y_comp = 1.
    z_comp = 1.
    
    # === get Jacobian :: ∂(x,y,z)/∂(q1,q2,q3)
    
    t_start = timeit.default_timer()
    
    dxdx = gradient(x3d, x_comp, axis=0, d=1, acc=acc, edge_stencil=edge_stencil, no_warn=no_warn)
    dydx = gradient(y3d, x_comp, axis=0, d=1, acc=acc, edge_stencil=edge_stencil, no_warn=no_warn)
    dzdx = gradient(z3d, x_comp, axis=0, d=1, acc=acc, edge_stencil=edge_stencil, no_warn=no_warn)
    
    dxdy = gradient(x3d, y_comp, axis=1, d=1, acc=acc, edge_stencil=edge_stencil, no_warn=no_warn)
    dydy = gradient(y3d, y_comp, axis=1, d=1, acc=acc, edge_stencil=edge_stencil, no_warn=no_warn)
    dzdy = gradient(z3d, y_comp, axis=1, d=1, acc=acc, edge_stencil=edge_stencil, no_warn=no_warn)
    
    dxdz = gradient(x3d, z_comp, axis=2, d=1, acc=acc, edge_stencil=edge_stencil, no_warn=no_warn)
    dydz = gradient(y3d, z_comp, axis=2, d=1, acc=acc, edge_stencil=edge_stencil, no_warn=no_warn)
    dzdz = gradient(z3d, z_comp, axis=2, d=1, acc=acc, edge_stencil=edge_stencil, no_warn=no_warn)
    
    J = np.stack((np.stack((dxdx, dydx, dzdx), axis=3),
                  np.stack((dxdy, dydy, dzdy), axis=3),
                  np.stack((dxdz, dydz, dzdz), axis=3)), axis=4)
    
    t_delta = timeit.default_timer() - t_start
    if verbose: tqdm.write( even_print('get J','%0.3f [s]'%(t_delta,), s=True) )
    
    # === get metric tensor M = J^-1 = ∂(q1,q2,q3)/∂(x,y,z) = ∂(ξ,η,ζ)/∂(x,y,z)
    
    if False: ## method 1
        
        t_start = timeit.default_timer()
        
        M = np.linalg.inv(J)
        
        # M_bak = np.copy(M)
        # for i in range(nx):
        #     for j in range(ny):
        #         for k in range(nz):
        #             M[i,j,k,:,:] = sp.linalg.inv( J[i,j,k,:,:] )
        # np.testing.assert_allclose(M_bak, M, atol=1e-12, rtol=1e-12)
        # print('check passed')
        
        t_delta = timeit.default_timer() - t_start
        if verbose: tqdm.write( even_print('get M','%0.3f [s]'%(t_delta,), s=True) )
    
    if True: ## method 2
        
        if ('M' in locals()):
            M_bak = np.copy(M)
            M = None; del M
        
        t_start = timeit.default_timer()
        
        a = J[:,:,:,0,0]
        b = J[:,:,:,0,1]
        c = J[:,:,:,0,2]
        d = J[:,:,:,1,0]
        e = J[:,:,:,1,1]
        f = J[:,:,:,1,2]
        g = J[:,:,:,2,0]
        h = J[:,:,:,2,1]
        i = J[:,:,:,2,2]
        
        # a = J[:,:,:,0,0]
        # b = J[:,:,:,1,0]
        # c = J[:,:,:,2,0]
        # d = J[:,:,:,0,1]
        # e = J[:,:,:,1,1]
        # f = J[:,:,:,2,1]
        # g = J[:,:,:,0,2]
        # h = J[:,:,:,1,2]
        # i = J[:,:,:,2,2]
        
        Jac_det = ( + a*e*i
                    + b*f*g
                    + c*d*h
                    - c*e*g
                    - b*d*i
                    - a*f*h )
        
        M = np.zeros((nx,ny,nz,3,3), dtype=np.float64)
        M[:,:,:,0,0] = +( dydy * dzdz - dydz * dzdy ) / Jac_det ## ξ_x
        M[:,:,:,0,1] = -( dxdy * dzdz - dxdz * dzdy ) / Jac_det ## ξ_y
        M[:,:,:,0,2] = +( dxdy * dydz - dxdz * dydy ) / Jac_det ## ξ_z
        M[:,:,:,1,0] = -( dydx * dzdz - dydz * dzdx ) / Jac_det ## η_x
        M[:,:,:,1,1] = +( dxdx * dzdz - dxdz * dzdx ) / Jac_det ## η_y
        M[:,:,:,1,2] = -( dxdx * dydz - dxdz * dydx ) / Jac_det ## η_z
        M[:,:,:,2,0] = +( dydx * dzdy - dydy * dzdx ) / Jac_det ## ζ_x
        M[:,:,:,2,1] = -( dxdx * dzdy - dxdy * dzdx ) / Jac_det ## ζ_y
        M[:,:,:,2,2] = +( dxdx * dydy - dxdy * dydx ) / Jac_det ## ζ_z
        
        t_delta = timeit.default_timer() - t_start
        if verbose: tqdm.write( even_print('get M','%0.3f [s]'%(t_delta,), s=True) )
        
        if ('M_bak' in locals()):
            np.testing.assert_allclose(M[:,:,:,0,0], M_bak[:,:,:,0,0], atol=1e-14, rtol=1e-14)
            print('check passed: ξ_x')
            np.testing.assert_allclose(M[:,:,:,0,1], M_bak[:,:,:,0,1], atol=1e-14, rtol=1e-14)
            print('check passed: ξ_y')
            np.testing.assert_allclose(M[:,:,:,0,2], M_bak[:,:,:,0,2], atol=1e-14, rtol=1e-14)
            print('check passed: ξ_z')
            np.testing.assert_allclose(M[:,:,:,1,0], M_bak[:,:,:,1,0], atol=1e-14, rtol=1e-14)
            print('check passed: η_x')
            np.testing.assert_allclose(M[:,:,:,1,1], M_bak[:,:,:,1,1], atol=1e-14, rtol=1e-14)
            print('check passed: η_y')
            np.testing.assert_allclose(M[:,:,:,1,2], M_bak[:,:,:,1,2], atol=1e-14, rtol=1e-14)
            print('check passed: η_z')
            np.testing.assert_allclose(M[:,:,:,2,0], M_bak[:,:,:,2,0], atol=1e-14, rtol=1e-14)
            print('check passed: ζ_x')
            np.testing.assert_allclose(M[:,:,:,2,1], M_bak[:,:,:,2,1], atol=1e-14, rtol=1e-14)
            print('check passed: ζ_y')
            np.testing.assert_allclose(M[:,:,:,2,2], M_bak[:,:,:,2,2], atol=1e-14, rtol=1e-14)
            print('check passed: ζ_z')
            np.testing.assert_allclose(M, M_bak, atol=1e-14, rtol=1e-14)
            print('check passed: M')
    
    return M
