import numpy as np
import scipy as sp

# ======================================================================

def gradient(u, x=None, d=1, axis=0, acc=6, edge_stencil='full', return_coeffs=False, no_warn=True):
    '''
    Numerical Gradient Approximation Using Finite Differences
    -----
    - calculates stencil given arbitrary accuracy & derivative order
    - handles non-uniform grids
    - accuracy order is only mathematically valid for:
       - uniform coordinate array
       - inner points which have full central stencil
    - handles N-D numpy arrays (gradient performed over axis denoted by axis arg)
    -----
    u    : input array to perform differentiation upon
    x    : coordinate vector (np.ndarray) OR dx (float) in the case of a uniform grid
    d    : derivative order
    axis : axis along which to perform gradient
    acc  : accuracy order (only fully valid for inner points with central stencil on uniform grid)
    -----
    edge_stencil  : type of edge stencil to use ('half','full')
    return_coeffs : if True, then return stencil & coefficient information
    -----
    # stencil_npts : number of index pts in (central) stencil
    #     --> no longer an input
    #     --> using 'acc' (accuracy order) instead and calculating npts from formula
    #     - stencil_npts=3 : stencil=[      -1,0,+1      ]
    #     - stencil_npts=5 : stencil=[   -2,-1,0,+1,+2   ]
    #     - stencil_npts=7 : stencil=[-3,-2,-1,0,+1,+2,+3]
    #     - edges are filled out with appropriate clipping of central stencil
    -----
    turbx.gradient( u , x , d=1 , acc=2 , edge_stencil='half' , axis=0 )
    ...reproduces...
    np.gradient(u, x, edge_order=1, axis=0)
    
    turbx.gradient( u , x , d=1 , acc=2 , edge_stencil='full' , axis=0 )
    ...reproduces...
    np.gradient(u, x, edge_order=2, axis=0)
    -----
    https://en.wikipedia.org/wiki/Finite_difference_coefficient
    https://web.media.mit.edu/~crtaylor/calculator.html
    -----
    Fornberg B. (1988) Generation of Finite Difference Formulas on
    Arbitrarily Spaced Grids, Mathematics of Computation 51, no. 184 : 699-706.
    http://www.ams.org/journals/mcom/1988-51-184/S0025-5718-1988-0935077-0/S0025-5718-1988-0935077-0.pdf
    '''
    
    u = np.asanyarray(u)
    nd = u.ndim
    
    # print('contiguous   : %s'%str( u.data.contiguous   ) )
    # print('C-contiguous : %s'%str( u.data.c_contiguous ) )
    # print('F-contiguous : %s'%str( u.data.f_contiguous ) )
    
    if (nd==0):
        raise ValueError('turbx.gradient() requires input that is at least 1D')
    
    axes = tuple(range(nd))
    
    if not isinstance(axis, int):
        raise ValueError('axis should be of type int')
    if (axis not in axes):
        raise ValueError('axis=%i is not valid for array with u.ndim=%s'%(axis,str(u.ndim)))
    
    nx = u.shape[axis] ## size of axis over which gradient will be performed
    
    if (nx<3):
        raise ValueError('nx<3')
    
    if (x is not None):
        if isinstance(x, float):
            if (x<=0.):
                raise ValueError('if x is a float it should be >0.')
        elif isinstance(x, int):
            x = float(x)
        elif isinstance(x, np.ndarray):
            if (x.ndim!=1):
                raise ValueError('x should be 1D if it is of type np.ndarray')
            if (x.shape[0]!=nx):
                raise ValueError('size of x does not match data axis specified')
            if (not np.all(np.diff(x) > 0.)) and (not np.all(np.diff(x) < 0.)):
                    raise AssertionError('x is not monotonically increasing/decreasing')
            
            ## optimization: check if x is actually uniformly spaced, in which case x=Δx
            dx0 = x[1]-x[0]
            if np.all(np.isclose(np.diff(x), dx0, rtol=1e-12)): 
                #print('turbx.gradient() : x arr with x.shape=%s seems like it is actually uniformly spaced. applying x=%0.8e'%(str(x.shape),dx0))
                x = dx0
        
        else:
            raise ValueError('x should be a 1D np.ndarray or float')
    else:
        x = 1. ## if x not provided, assume uniform unit coordinate vector
    
    if isinstance(x, float):
        uniform_grid = True
    elif isinstance(x, np.ndarray):
        uniform_grid = False
    else:
        raise ValueError('turbx.gradient() : this should never happen... check!')
    
    if not isinstance(d, int):
        raise ValueError('d (derivative order) should be of type int')
    if not (d>0):
        raise ValueError('d (derivative order) should be >0')
    
    if not isinstance(acc, int):
        raise ValueError('acc (accuracy order) should be of type int')
    if not (acc>=2):
        raise ValueError('acc (accuracy order) should be >=2')
    if (acc%2!=0):
        raise ValueError('acc (accuracy order) should be an integer multiple of 2')
    
    ## for the d'th derivative with accuracy=acc, the following formula gives the n pts of the (central) stencil
    stencil_npts = 2*int(np.floor((d+1)/2)) - 1 + acc
    
    if not isinstance(stencil_npts, int):
        raise ValueError('stencil_npts must be of type \'int\'')
    if (stencil_npts<3):
        raise ValueError('stencil_npts should be >=3')
    if ((stencil_npts-1)%2 != 0):
        raise ValueError('(stencil_npts-1) should be divisible by 2 (for central stencil)')
    if (stencil_npts > nx):
        raise ValueError('stencil_npts > nx')
    
    if all([ (edge_stencil!='half') , (edge_stencil!='full') ]):
        raise ValueError('edge_stencil=%s not valid. options are: \'full\', \'half\''%str(edge_stencil))
    
    # ===
    
    n_full_central_stencils = nx - stencil_npts + 1
    
    if ( n_full_central_stencils < 5 ) and not no_warn:
        print('\nWARNING\n'+72*'-')
        print('n pts with full central stencils = %i (<5)'%n_full_central_stencils)
        #print('nx//3=%i'%(nx//3))
        print('--> consider reducing acc arg (accuracy order)')
        print(72*'-'+'\n')
    
    stencil_width = stencil_npts-1
    sw2           = stencil_width//2
    
    # === build up stencil & coefficients vector
    
    fdc_vec = [] ## vector of finite difference coefficient information
    
    ## left side
    for i in range(0,sw2):
        
        ## full
        stencil_L = np.arange(-i,stencil_width+1-i)
        
        ## half
        if (edge_stencil=='half') and not all([(acc==2),(d>=2)]):
            stencil_L = np.arange(-i,sw2+1)
        
        i_range = np.arange( 0 , stencil_L.shape[0] )
        
        if uniform_grid:
            fdc = fd_coeff_calculator( stencil_L , d=d , dx=x )
        else:
            fdc = fd_coeff_calculator( stencil_L , d=d , x=x[i_range] )
        
        fdc_vec.append( [ fdc , i_range , stencil_L ] )
    
    ## inner pts
    stencil = np.arange(stencil_npts) - sw2
    if uniform_grid:
        fdc_inner = fd_coeff_calculator( stencil , d=d , dx=x )
    for i in range(sw2,nx-sw2):
        
        i_range  = np.arange(i-sw2,i+sw2+1)
        
        if uniform_grid:
            fdc = fdc_inner
        else:
            fdc = fd_coeff_calculator( stencil , d=d , x=x[i_range] )
        
        fdc_vec.append( [ fdc , i_range , stencil ] )
    
    ## right side
    for i in range(nx-sw2,nx):
        
        ## full
        stencil_R = np.arange(-stencil_width+(nx-i-1),nx-i)
        
        ## half
        if (edge_stencil=='half') and not all([(acc==2),(d>=2)]):
            stencil_R = np.arange(-sw2,nx-i)
        
        i_range  = np.arange( nx-stencil_R.shape[0] , nx )
        
        if uniform_grid:
            fdc = fd_coeff_calculator( stencil_R , d=d , dx=x )
        else:
            fdc = fd_coeff_calculator( stencil_R , d=d , x=x[i_range] )
        
        fdc_vec.append( [ fdc , i_range , stencil_R ] )
    
    # === debug
    
    # print('i_range')
    # for fdc_vec_ in fdc_vec:
    #     print(fdc_vec_[1])
    # print('')
    # print('stencil')
    # for fdc_vec_ in fdc_vec:
    #     print(fdc_vec_[2])
    
    # === evaluate gradient
    
    if (nd==1): ## 1D
        
        u_ddx = np.zeros_like(u)
        for i in range(len(fdc_vec)):
            fdc, i_range, stencil = fdc_vec[i]
            u_ddx[i] = np.dot( fdc , u[i_range] )
    
    else: ## N-D
        
        ## the order in memory of the incoming data
        if u.data.contiguous:
            if u.data.c_contiguous:
                order='C'
            elif u.data.f_contiguous:
                order='F'
            else:
                raise ValueError
        else:
            order='C'
        
        ## if the array is C-ordered, use axis=0 as the axis to shift to
        ## if the array is F-ordered, use axis=-1 as the axis to shift to
        if order=='C':
            shift_pos=0 ## 0th axis
        elif order=='F':
            shift_pos=nd-1 ## last axis
        
        ## shift gradient axis
        u = np.swapaxes(u, axis, shift_pos)
        shape_new = u.shape
        if (shift_pos==0):
            size_all_but_ax = np.prod(np.array(shape_new)[1:])
        elif (shift_pos==nd-1):
            size_all_but_ax = np.prod(np.array(shape_new)[:-1])
        else:
            raise ValueError
        
        ## reshape N-D to 2D
        ## --> shift_pos=0    : gradient axis is 0, all other axes are flattened on axis=1)
        ## --> shift_pos=last : ...
        if (shift_pos==0):
            u = np.reshape(u, (nx, size_all_but_ax), order=order)
        elif (shift_pos==nd-1):
            u = np.reshape(u, (size_all_but_ax, nx), order=order)
        else:
            raise ValueError
        
        u_ddx = np.zeros_like(u,order=order)
        for i in range(nx):
            fdc, i_range, stencil = fdc_vec[i]
            ia=min(i_range)
            ib=max(i_range)+1
            if (shift_pos==0):
                u_ddx[i,:] = np.einsum('ij,i->j', u[ia:ib,:], fdc)
            else:
                u_ddx[:,i] = np.einsum('ji,i->j', u[:,ia:ib], fdc)
        
        ## reshape 2D back to original N-D
        u_ddx = np.reshape(u_ddx, shape_new, order=order)
        
        ## shift gradient axis back to original position
        u_ddx = np.swapaxes(u_ddx, shift_pos, axis)
    
    ## the original data array should have been de-referenced during this func
    u = None; del u
    
    if return_coeffs:
        return u_ddx, fdc_vec
    else:
        return u_ddx

def fd_coeff_calculator(stencil, d=1, x=None, dx=None):
    '''
    Calculate Finite Difference Coefficients for Arbitrary Stencil
    -----
    stencil : indices of stencil pts e.g. np.array([-2,-1,0,1,2])
    d       : derivative order
    x       : locations of grid points corresponding to stencil indices
    dx      : spacing of grid points in the case of uniform grid
    -----
    https://en.wikipedia.org/wiki/Finite_difference_coefficient
    https://web.media.mit.edu/~crtaylor/calculator.html
    -----
    Fornberg B. (1988) Generation of Finite Difference Formulas on
    Arbitrarily Spaced Grids, Mathematics of Computation 51, no. 184 : 699-706.
    http://www.ams.org/journals/mcom/1988-51-184/S0025-5718-1988-0935077-0/S0025-5718-1988-0935077-0.pdf
    '''
    
    stencil = np.asanyarray(stencil)
    
    if not isinstance(stencil, np.ndarray):
        raise ValueError('stencil should be of type np.ndarray')
    if (stencil.ndim!=1):
        raise ValueError('stencil should be 1D')
    if (stencil.shape[0]<2):
        raise ValueError('stencil size should be >=2')
    if (0 not in stencil):
        raise ValueError('stencil does not contain 0')
    if not np.issubdtype(stencil.dtype, np.integer):
        raise ValueError('stencil.dtype not a subdtype of np.integer')
    
    if not isinstance(d, int):
        raise ValueError('d (derivative order) should be of type int')
    if not (d>0):
        raise ValueError('d (derivative order) should be >0')
    
    if (dx is None) and (x is None):
        raise ValueError('one of args \'dx\' or \'x\' should be defined')
    if (dx is not None) and (x is not None):
        raise ValueError('only one of args \'dx\' or \'x\' should be defined')
    if (dx is not None):
        if not isinstance(dx, float):
            raise ValueError('dx should be of type float')
    
    if (x is not None):
        if not isinstance(x, np.ndarray):
            raise ValueError('x should be of type np.ndarray')
        if (x.shape[0] != stencil.shape[0]):
            raise ValueError('x, stencil should have same shape')
        if (not np.all(np.diff(x) > 0.)) and (not np.all(np.diff(x) < 0.)):
            raise AssertionError('x is not monotonically increasing/decreasing')
    
    ## overwrite stencil (int index) to be coordinate array (delta from 0 position)
    
    i0 = np.where(stencil==0)[0][0]
    
    if (x is not None):
        stencil = x - x[i0] 
    
    if (dx is not None):
        stencil = dx * stencil.astype(np.float64)
    
    nn = stencil.shape[0]
    
    dvec = np.zeros( (nn,) , dtype=np.float64 )
    #dvec = np.zeros( (nn,) , dtype=np.longdouble )
    dfac=1
    for i in range(d):
        dfac *= (i+1)
    dvec[d] = dfac
    
    ## increase precision
    #stencil = np.copy(stencil).astype(np.longdouble)
    
    #stencil_abs_max         = np.abs(stencil).max()
    stencil_abs_min_nonzero = np.abs(stencil[[ i for i in range(stencil.size) if i!=i0 ]]).min()
    
    '''
    scale/normalize the coordinate stencil (to avoid ill-conditioning)
    - if coordinates are already small/large, the Vandermonde matrix becomes
       HIGHLY ill-conditioned due to row exponents
    - coordinates are normalized here so that smallest absolute non-zero delta coord. is =1
    - RHS vector (dvec) gets normalized too
    - FD coefficients are (theoretically) unaffected
    '''
    normalize_stencil = True
    
    if normalize_stencil:
        stencil /= stencil_abs_min_nonzero
    
    mat = np.zeros( (nn,nn) , dtype=np.float64)
    #mat = np.zeros( (nn,nn) , dtype=np.longdouble)
    for i in range(nn):
        mat[i,:] = np.power( stencil , i )
    
    ## condition_number = np.linalg.cond(mat, p=-2)
    
    # mat_inv = np.linalg.inv( mat )
    # coeffv  = np.dot( mat_inv , dvec )
    
    if normalize_stencil:
        for i in range(nn):
            dvec[i] /= np.power( stencil_abs_min_nonzero , i )
    
    #coeffv = np.linalg.solve(mat, dvec)
    coeffv = sp.linalg.solve(mat, dvec)
    
    return coeffv
