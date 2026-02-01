import sys
import timeit

import numpy as np
from scipy.integrate import cumulative_trapezoid
from scipy.interpolate import CubicSpline, interp1d
from scipy.optimize import least_squares
from tqdm import tqdm

from .bl import (
    calc_d1,
    calc_d2,
    calc_d3,
    calc_d99_1d,
    calc_dRC,
    calc_I2,
    calc_I3,
    calc_profile_edge_1d,
    calc_wake_parameter_1d,
)
from .gradient import gradient
from .grid_metric import get_metric_tensor_2d
from .utils import even_print, format_time_string

'''
========================================================================
Collection of routines that pre-compute useful quantities
========================================================================
'''

# ======================================================================

def _calc_gradients(self, acc=6, edge_stencil='full', **kwargs):
    '''
    Calculate spatial gradients of averaged quantities
    '''
    
    verbose  = kwargs.get('verbose',True)
    do_favre = kwargs.get('favre',True)
    
    if verbose: print('\n'+'ztmd.calc_gradients()'+'\n'+72*'-')
    t_start_func = timeit.default_timer()
    
    if verbose: even_print('acc','%i'%(acc,))
    if verbose: even_print('edge_stencil','%s'%(edge_stencil,))
    if verbose: even_print('do_favre',str(do_favre))
    
    ## check
    if not hasattr(self,'rectilinear') and not hasattr(self,'curvilinear'):
        raise AssertionError('neither rectilinear nor curvilinear attr set')
    
    if hasattr(self,'rectilinear'):
        if self.rectilinear:
            if verbose: even_print('grid type','rectilinear')
    if hasattr(self,'curvilinear'):
        if self.curvilinear:
            if verbose: even_print('grid type','curvilinear')
    
    if (self.x.ndim==1) and (self.y.ndim==1):
        if hasattr(self,'rectilinear'):
            if not self.rectilinear:
                raise AssertionError
        if hasattr(self,'curvilinear'):
            if self.curvilinear:
                raise AssertionError
    elif (self.x.ndim==2) and (self.y.ndim==2):
        if hasattr(self,'rectilinear'):
            if self.rectilinear:
                raise AssertionError
        if hasattr(self,'curvilinear'):
            if not self.curvilinear:
                raise AssertionError
    else:
        raise ValueError
    
    # ===
    
    if self.curvilinear: ## get metric tensor 2D
        
        M = get_metric_tensor_2d(self.x, self.y, acc=acc, edge_stencil=edge_stencil, verbose=False)
        
        ddx_q1 = np.copy( M[:,:,0,0] ) ## ξ_x
        ddx_q2 = np.copy( M[:,:,1,0] ) ## η_x
        ddy_q1 = np.copy( M[:,:,0,1] ) ## ξ_y
        ddy_q2 = np.copy( M[:,:,1,1] ) ## η_y
        
        if verbose: even_print('ξ_x','%s'%str(ddx_q1.shape))
        if verbose: even_print('η_x','%s'%str(ddx_q2.shape))
        if verbose: even_print('ξ_y','%s'%str(ddy_q1.shape))
        if verbose: even_print('η_y','%s'%str(ddy_q2.shape))
        
        M = None; del M
        
        ## the 'computational' grid (unit Cartesian)
        #x_comp = np.arange(nx, dtype=np.float64)
        #y_comp = np.arange(ny, dtype=np.float64)
        x_comp = 1.
        y_comp = 1.
    
    print(72*'-')
    
    # === get gradients of [u,v,p,T,ρ,μ]
    
    if ('data/u' in self):
        
        u = np.copy( self['data/u'][()].T )
        
        if self.rectilinear:
            ddx_u = gradient(u, self.x, axis=0, acc=acc, edge_stencil=edge_stencil, d=1)
            ddy_u = gradient(u, self.y, axis=1, acc=acc, edge_stencil=edge_stencil, d=1)
        elif self.curvilinear:
            ddx_u_comp = gradient(u, x_comp, axis=0, acc=acc, edge_stencil=edge_stencil, d=1)
            ddy_u_comp = gradient(u, y_comp, axis=1, acc=acc, edge_stencil=edge_stencil, d=1)
            ddx_u      = ddx_u_comp*ddx_q1 + ddy_u_comp*ddx_q2
            ddy_u      = ddx_u_comp*ddy_q1 + ddy_u_comp*ddy_q2
        else:
            raise ValueError
        
        if ('data/ddx_u' in self): del self['data/ddx_u']
        self.create_dataset('data/ddx_u', data=ddx_u.T, chunks=None)
        
        if ('data/ddy_u' in self): del self['data/ddy_u']
        self.create_dataset('data/ddy_u', data=ddy_u.T, chunks=None)
        
        if verbose: even_print('ddx[u]','%s'%str(ddx_u.shape))
        if verbose: even_print('ddy[u]','%s'%str(ddy_u.shape))
    
    if ('data/v' in self):
        
        v = np.copy( self['data/v'][()].T )
        
        if self.rectilinear:
            ddx_v = gradient(v, self.x, axis=0, acc=acc, edge_stencil=edge_stencil, d=1)
            ddy_v = gradient(v, self.y, axis=1, acc=acc, edge_stencil=edge_stencil, d=1)
        elif self.curvilinear:
            ddx_v_comp = gradient(v, x_comp, axis=0, acc=acc, edge_stencil=edge_stencil, d=1)
            ddy_v_comp = gradient(v, y_comp, axis=1, acc=acc, edge_stencil=edge_stencil, d=1)
            ddx_v      = ddx_v_comp*ddx_q1 + ddy_v_comp*ddx_q2
            ddy_v      = ddx_v_comp*ddy_q1 + ddy_v_comp*ddy_q2
        else:
            raise ValueError
        
        if ('data/ddx_v' in self): del self['data/ddx_v']
        self.create_dataset('data/ddx_v', data=ddx_v.T, chunks=None)
        
        if ('data/ddy_v' in self): del self['data/ddy_v']
        self.create_dataset('data/ddy_v', data=ddy_v.T, chunks=None)
        
        if verbose: even_print('ddx[v]','%s'%str(ddx_v.shape))
        if verbose: even_print('ddy[v]','%s'%str(ddy_v.shape))
    
    if ('data/p' in self):
        
        p = np.copy( self['data/p'][()].T )
        
        if self.rectilinear:
            ddx_p = gradient(p, self.x, axis=0, acc=acc, edge_stencil=edge_stencil, d=1)
            ddy_p = gradient(p, self.y, axis=1, acc=acc, edge_stencil=edge_stencil, d=1)
        elif self.curvilinear:
            ddx_p_comp = gradient(p, x_comp, axis=0, acc=acc, edge_stencil=edge_stencil, d=1)
            ddy_p_comp = gradient(p, y_comp, axis=1, acc=acc, edge_stencil=edge_stencil, d=1)
            ddx_p      = ddx_p_comp*ddx_q1 + ddy_p_comp*ddx_q2
            ddy_p      = ddx_p_comp*ddy_q1 + ddy_p_comp*ddy_q2
        else:
            raise ValueError
        
        if ('data/ddx_p' in self): del self['data/ddx_p']
        self.create_dataset('data/ddx_p', data=ddx_p.T, chunks=None)
        
        if ('data/ddy_p' in self): del self['data/ddy_p']
        self.create_dataset('data/ddy_p', data=ddy_p.T, chunks=None)
        
        if verbose: even_print('ddx[p]','%s'%str(ddx_p.shape))
        if verbose: even_print('ddy[p]','%s'%str(ddy_p.shape))
    
    if ('data/T' in self):
        
        T = np.copy( self['data/T'][()].T )
        
        if self.rectilinear:
            ddx_T = gradient(T, self.x, axis=0, acc=acc, edge_stencil=edge_stencil, d=1)
            ddy_T = gradient(T, self.y, axis=1, acc=acc, edge_stencil=edge_stencil, d=1)
        elif self.curvilinear:
            ddx_T_comp = gradient(T, x_comp, axis=0, acc=acc, edge_stencil=edge_stencil, d=1)
            ddy_T_comp = gradient(T, y_comp, axis=1, acc=acc, edge_stencil=edge_stencil, d=1)
            ddx_T      = ddx_T_comp*ddx_q1 + ddy_T_comp*ddx_q2
            ddy_T      = ddx_T_comp*ddy_q1 + ddy_T_comp*ddy_q2
        else:
            raise ValueError
        
        if ('data/ddx_T' in self): del self['data/ddx_T']
        self.create_dataset('data/ddx_T', data=ddx_T.T, chunks=None)
        
        if ('data/ddy_T' in self): del self['data/ddy_T']
        self.create_dataset('data/ddy_T', data=ddy_T.T, chunks=None)
        
        if verbose: even_print('ddx[T]','%s'%str(ddx_T.shape))
        if verbose: even_print('ddy[T]','%s'%str(ddy_T.shape))
    
    if ('data/rho' in self):
        
        rho = np.copy( self['data/rho'][()].T )
        
        if self.rectilinear:
            ddx_rho = gradient(rho, self.x, axis=0, acc=acc, edge_stencil=edge_stencil, d=1)
            ddy_rho = gradient(rho, self.y, axis=1, acc=acc, edge_stencil=edge_stencil, d=1)
        elif self.curvilinear:
            ddx_r_comp = gradient(rho, x_comp, axis=0, acc=acc, edge_stencil=edge_stencil, d=1)
            ddy_r_comp = gradient(rho, y_comp, axis=1, acc=acc, edge_stencil=edge_stencil, d=1)
            ddx_rho    = ddx_r_comp*ddx_q1 + ddy_r_comp*ddx_q2
            ddy_rho    = ddx_r_comp*ddy_q1 + ddy_r_comp*ddy_q2
        else:
            raise ValueError
        
        if ('data/ddx_rho' in self): del self['data/ddx_rho']
        self.create_dataset('data/ddx_rho', data=ddx_rho.T, chunks=None)
        
        if ('data/ddy_rho' in self): del self['data/ddy_rho']
        self.create_dataset('data/ddy_rho', data=ddy_rho.T, chunks=None)
        
        if verbose: even_print('ddx[ρ]','%s'%str(ddx_rho.shape))
        if verbose: even_print('ddy[ρ]','%s'%str(ddy_rho.shape))
    
    if ('data/mu' in self):
        
        mu = np.copy( self['data/mu'][()].T )
        
        if self.rectilinear:
            ddx_mu = gradient(mu, self.x, axis=0, acc=acc, edge_stencil=edge_stencil, d=1)
            ddy_mu = gradient(mu, self.y, axis=1, acc=acc, edge_stencil=edge_stencil, d=1)
        elif self.curvilinear:
            ddx_mu_comp = gradient(mu, x_comp, axis=0, acc=acc, edge_stencil=edge_stencil, d=1)
            ddy_mu_comp = gradient(mu, y_comp, axis=1, acc=acc, edge_stencil=edge_stencil, d=1)
            ddx_mu      = ddx_mu_comp*ddx_q1 + ddy_mu_comp*ddx_q2
            ddy_mu      = ddx_mu_comp*ddy_q1 + ddy_mu_comp*ddy_q2
        else:
            raise ValueError
        
        if ('data/ddx_mu' in self): del self['data/ddx_mu']
        self.create_dataset('data/ddx_mu', data=ddx_mu.T, chunks=None)
        
        if ('data/ddy_mu' in self): del self['data/ddy_mu']
        self.create_dataset('data/ddy_mu', data=ddy_mu.T, chunks=None)
        
        if verbose: even_print('ddx[μ]','%s'%str(ddx_mu.shape))
        if verbose: even_print('ddy[μ]','%s'%str(ddy_mu.shape))
    
    # === vorticity
    
    ## z-vorticity :: ω_z
    vort_z = ddx_v - ddy_u
    
    if ('data/vort_z' in self): del self['data/vort_z']
    self.create_dataset('data/vort_z', data=vort_z.T, chunks=None)
    if verbose: even_print('ω_z','%s'%str(vort_z.shape))
    
    ## divergence (in xy-plane)
    div_xy = ddx_u + ddy_v
    
    if ('data/div_xy' in self): del self['data/div_xy']
    self.create_dataset('data/div_xy', data=div_xy.T, chunks=None)
    if verbose: even_print('div_xy','%s'%str(div_xy.shape))
    
    # === 
    
    if ('data/utang' in self):
        
        utang = np.copy( self['data/utang'][()].T )
        
        if self.rectilinear:
            ddx_utang = gradient(utang, self.x, axis=0, acc=acc, edge_stencil=edge_stencil, d=1)
            ddy_utang = gradient(utang, self.y, axis=1, acc=acc, edge_stencil=edge_stencil, d=1)
        elif self.curvilinear:
            ddx_utang_comp = gradient(utang, x_comp, axis=0, acc=acc, edge_stencil=edge_stencil, d=1)
            ddy_utang_comp = gradient(utang, y_comp, axis=1, acc=acc, edge_stencil=edge_stencil, d=1)
            ddx_utang      = ddx_utang_comp*ddx_q1 + ddy_utang_comp*ddx_q2
            ddy_utang      = ddx_utang_comp*ddy_q1 + ddy_utang_comp*ddy_q2
        else:
            raise ValueError
        
        if ('data/ddx_utang' in self): del self['data/ddx_utang']
        self.create_dataset('data/ddx_utang', data=ddx_utang.T, chunks=None)
        if verbose: even_print('ddx[utang]','%s'%str(ddx_utang.shape))
        
        if ('data/ddy_utang' in self): del self['data/ddy_utang']
        self.create_dataset('data/ddy_utang', data=ddy_utang.T, chunks=None)
        if verbose: even_print('ddy[utang]','%s'%str(ddy_utang.shape))
    
    if ('data/unorm' in self):
        
        unorm = np.copy( self['data/unorm'][()].T )
        
        if self.rectilinear:
            ddx_unorm = gradient(unorm, self.x, axis=0, acc=acc, edge_stencil=edge_stencil, d=1)
            ddy_unorm = gradient(unorm, self.y, axis=1, acc=acc, edge_stencil=edge_stencil, d=1)
        elif self.curvilinear:
            ddx_unorm_comp = gradient(unorm, x_comp, axis=0, acc=acc, edge_stencil=edge_stencil, d=1)
            ddy_unorm_comp = gradient(unorm, y_comp, axis=1, acc=acc, edge_stencil=edge_stencil, d=1)
            ddx_unorm      = ddx_unorm_comp*ddx_q1 + ddy_unorm_comp*ddx_q2
            ddy_unorm      = ddx_unorm_comp*ddy_q1 + ddy_unorm_comp*ddy_q2
        else:
            raise ValueError
        
        if ('data/ddx_unorm' in self): del self['data/ddx_unorm']
        self.create_dataset('data/ddx_unorm', data=ddx_unorm.T, chunks=None)
        if verbose: even_print('ddx[unorm]','%s'%str(ddx_unorm.shape))
        
        if ('data/ddy_unorm' in self): del self['data/ddy_unorm']
        self.create_dataset('data/ddy_unorm', data=ddy_unorm.T, chunks=None)
        if verbose: even_print('ddy[unorm]','%s'%str(ddy_unorm.shape))
    
    # === Favre
    
    if do_favre:
        
        print(72*'-')
        
        if ('data/u_Fv' in self):
            
            u_Fv = np.copy( self['data/u_Fv'][()].T )
            
            if self.rectilinear:
                ddx_u_Fv = gradient(u_Fv, self.x, axis=0, acc=acc, edge_stencil=edge_stencil, d=1)
                ddy_u_Fv = gradient(u_Fv, self.y, axis=1, acc=acc, edge_stencil=edge_stencil, d=1)
            elif self.curvilinear:
                ddx_u_Fv_comp = gradient(u_Fv, x_comp, axis=0, acc=acc, edge_stencil=edge_stencil, d=1)
                ddy_u_Fv_comp = gradient(u_Fv, y_comp, axis=1, acc=acc, edge_stencil=edge_stencil, d=1)
                ddx_u_Fv      = ddx_u_Fv_comp*ddx_q1 + ddy_u_Fv_comp*ddx_q2
                ddy_u_Fv      = ddx_u_Fv_comp*ddy_q1 + ddy_u_Fv_comp*ddy_q2
            else:
                raise ValueError
            
            if ('data/ddx_u_Fv' in self): del self['data/ddx_u_Fv']
            self.create_dataset('data/ddx_u_Fv', data=ddx_u_Fv.T, chunks=None)
            
            if ('data/ddy_u_Fv' in self): del self['data/ddy_u_Fv']
            self.create_dataset('data/ddy_u_Fv', data=ddy_u_Fv.T, chunks=None)
            
            if verbose: even_print('ddx[u_Fv]','%s'%str(ddx_u_Fv.shape))
            if verbose: even_print('ddy[u_Fv]','%s'%str(ddy_u_Fv.shape))
        
        if ('data/v_Fv' in self):
            
            v_Fv = np.copy( self['data/v_Fv'][()].T )
            
            if self.rectilinear:
                ddx_v_Fv = gradient(v_Fv, self.x, axis=0, acc=acc, edge_stencil=edge_stencil, d=1)
                ddy_v_Fv = gradient(v_Fv, self.y, axis=1, acc=acc, edge_stencil=edge_stencil, d=1)
            elif self.curvilinear:
                ddx_v_Fv_comp = gradient(v_Fv, x_comp, axis=0, acc=acc, edge_stencil=edge_stencil, d=1)
                ddy_v_Fv_comp = gradient(v_Fv, y_comp, axis=1, acc=acc, edge_stencil=edge_stencil, d=1)
                ddx_v_Fv      = ddx_v_Fv_comp*ddx_q1 + ddy_v_Fv_comp*ddx_q2
                ddy_v_Fv      = ddx_v_Fv_comp*ddy_q1 + ddy_v_Fv_comp*ddy_q2
            else:
                raise ValueError
            
            if ('data/ddx_v_Fv' in self): del self['data/ddx_v_Fv']
            self.create_dataset('data/ddx_v_Fv', data=ddx_v_Fv.T, chunks=None)
            
            if ('data/ddy_v_Fv' in self): del self['data/ddy_v_Fv']
            self.create_dataset('data/ddy_v_Fv', data=ddy_v_Fv.T, chunks=None)
            
            if verbose: even_print('ddx[v_Fv]','%s'%str(ddx_v_Fv.shape))
            if verbose: even_print('ddy[v_Fv]','%s'%str(ddy_v_Fv.shape))
    
    self.get_header(verbose=False)
    if verbose: print(72*'-')
    if verbose: print('total time : ztmd.calc_gradients() : %s'%format_time_string((timeit.default_timer() - t_start_func)))
    if verbose: print(72*'-')
    
    return

def _calc_psvel(self, **kwargs):
    '''
    Calculate pseudovelocity, wall-normal cumulative integration of (-) z-vorticity
    '''
    
    verbose  = kwargs.get('verbose',True)
    
    if verbose: print('\n'+'ztmd.calc_psvel()'+'\n'+72*'-')
    t_start_func = timeit.default_timer()
    
    if 'data/vort_z' not in self:
        raise ValueError("'data/vort_z' not in ztmd")
    
    vort_z = np.copy( self['data/vort_z'][()].T )
    
    nx = self.nx
    ny = self.ny
    
    if self.rectilinear:
        
        x = np.copy( self['dims/x'][()] )
        y = np.copy( self['dims/y'][()] )
    
    elif self.curvilinear:
        
        ## copy dims into memory
        x = np.copy( self['dims/x'][()].T ) ## 2D
        y = np.copy( self['dims/y'][()].T ) ## 2D
        
        if ('dims/snorm' not in self):
            raise AssertionError('dims/snorm not present')
        if ('dims/stang' not in self):
            raise AssertionError('dims/stang not present')
        
        snorm = np.copy( self['dims/snorm'][()] ) ## 1D
        #stang = np.copy( self['dims/stang'][()] ) ## 1D
        
        if ('data/utang' not in self):
            raise AssertionError('data/utang not present')
        
        #utang = np.copy( self['data/utang'][()].T )
        #unorm = np.copy( self['data/unorm'][()].T )
        
        ## copy csys datasets into memory
        #vtang = np.copy( self['csys/vtang'][()] )
        #vnorm = np.copy( self['csys/vnorm'][()] )
        
        if (x.shape != (self.nx,self.ny)):
            raise ValueError('x.shape != (self.nx,self.ny)')
        if (y.shape != (self.nx,self.ny)):
            raise ValueError('y.shape != (self.nx,self.ny)')
    
    else:
        raise ValueError
    
    ## the local 1D wall-normal coordinate
    if self.rectilinear:
        y_ = np.copy(y)
    elif self.curvilinear:
        y_ = np.copy(snorm)
    else:
        raise ValueError
    
    ## pseudo-velocity is a cumulative integration of (-) z-vorticity
    psvel = np.zeros(shape=(nx,ny), dtype=np.float64)
    for i in range(nx):
        psvel_     = cumulative_trapezoid(-1*vort_z[i,:], y_, initial=0.)
        psvel[i,:] = psvel_
    
    if ('data/psvel' in self):
        del self['data/psvel']
    self.create_dataset('data/psvel', data=psvel.T, chunks=None)
    if verbose: even_print('data/psvel','%s'%str(psvel.shape))
    
    self.get_header(verbose=False)
    if verbose: print(72*'-')
    if verbose: print('total time : ztmd.calc_psvel() : %s'%format_time_string((timeit.default_timer() - t_start_func)))
    if verbose: print(72*'-')
    
    return

def _calc_wall_quantities(self, acc=6, edge_stencil='full', **kwargs):
    '''
    Get 1D wall quantities
    -----
    - [ ρ_wall, ν_wall, μ_wall, T_wall ]
    - τ_wall = μ_wall·ddn[utang] :: [kg/(m·s)]·[m/s]/[m] = [kg/(m·s²)] = [N/m²] = [Pa]
    - u_τ = (τ_wall/ρ_wall)^(1/2)
    '''
    
    verbose = kwargs.get('verbose',True)
    
    if verbose: print('\n'+'ztmd.calc_wall_quantities()'+'\n'+72*'-')
    t_start_func = timeit.default_timer()
    
    if verbose: even_print('acc','%i'%(acc,))
    if verbose: even_print('edge_stencil','%s'%(edge_stencil,))
    
    ## check
    if (self.x.ndim==1) and (self.y.ndim==1):
        if hasattr(self,'rectilinear'):
            if not self.rectilinear:
                raise AssertionError
        if hasattr(self,'curvilinear'):
            if self.curvilinear:
                raise AssertionError
    elif (self.x.ndim==2) and (self.y.ndim==2):
        if hasattr(self,'rectilinear'):
            if self.rectilinear:
                raise AssertionError
        if hasattr(self,'curvilinear'):
            if not self.curvilinear:
                raise AssertionError
    else:
        raise ValueError
    
    # ===
    
    if self.curvilinear:
        
        if self.requires_wall_norm_interp:
            
            gndata = 'data_2Dw' ## group name for 2D data (interpolated)
            #gndims = 'dims_2Dw' ## group name for 2D dims (interpolated)
            
            ## wall-normal interpolation coordinates (2D)
            #x_wn = np.copy( self[f'{gndata}/x'][()].T )
            #y_wn = np.copy( self[f'{gndata}/y'][()].T )
            s_wn = np.copy( self[f'{gndata}/wall_distance'][()].T )
        
        else:
            
            gndata = 'data' ## group name for 2D data
            #gndims = 'dims' ## group name for 2D dims
            
            #x_wn = np.copy( self['dims/x'][()].T )
            #y_wn = np.copy( self['dims/y'][()].T )
            s_wn = np.copy( self['dims/snorm'][()] )
            #s_wn = np.broadcast_to(s_wn, (self.nx,self.ny))
        
        if (f'{gndata}/utang' not in self):
            raise AssertionError(f'{gndata}/utang not present')
        
        ## wall-normal interpolated scalars (2D)
        utang_wn  = np.copy( self[f'{gndata}/utang'][()].T  )
        #T_wn      = np.copy( self[f'{gndata}/T'][()].T      )
        vort_z_wn = np.copy( self[f'{gndata}/vort_z'][()].T )
    
    # === get ρ_wall, ν_wall, μ_wall, T_wall
    
    rho = np.copy( self['data/rho'][()].T )
    rho_wall = np.copy( rho[:,0] )
    if ('data_1Dx/rho_wall' in self): del self['data_1Dx/rho_wall']
    self.create_dataset('data_1Dx/rho_wall', data=rho_wall, chunks=None)
    if verbose: even_print('data_1Dx/rho_wall','%s'%str(rho_wall.shape))
    
    nu = np.copy( self['data/nu'][()].T )
    nu_wall = np.copy( nu[:,0] )
    if ('data_1Dx/nu_wall' in self): del self['data_1Dx/nu_wall']
    self.create_dataset('data_1Dx/nu_wall', data=nu_wall, chunks=None)
    if verbose: even_print('data_1Dx/nu_wall','%s'%str(nu_wall.shape))
    
    mu = np.copy( self['data/mu'][()].T )
    mu_wall = np.copy( mu[:,0] )
    if ('data_1Dx/mu_wall' in self): del self['data_1Dx/mu_wall']
    self.create_dataset('data_1Dx/mu_wall', data=mu_wall, chunks=None)
    if verbose: even_print('data_1Dx/mu_wall','%s'%str(mu_wall.shape))
    
    T = np.copy( self['data/T'][()].T )
    T_wall = np.copy( T[:,0] )
    if ('data_1Dx/T_wall' in self): del self['data_1Dx/T_wall']
    self.create_dataset('data_1Dx/T_wall', data=T_wall, chunks=None)
    if verbose: even_print('data_1Dx/T_wall','%s'%str(T_wall.shape))
    
    # === get wall ddn[]
    
    if self.rectilinear:
        
        ddy_u = np.copy( self['data/ddy_u'][()].T )
    
    elif self.curvilinear:
        
        if True:
            
            if (s_wn.ndim==2): ## wall-normal distance (s_norm) is a 2D field
                
                ddn_utang  = np.zeros((self.nx,self.ny), dtype=np.float64) ## dimensional [m/s]/[m] = [1/s]
                ddn_vort_z = np.zeros((self.nx,self.ny), dtype=np.float64)
                
                progress_bar = tqdm(total=self.nx, ncols=100, desc='get ddn[]', leave=False, file=sys.stdout)
                for i in range(self.nx):
                    ddn_utang[i,:]  = gradient(utang_wn[i,:]  , s_wn[i,:], axis=0, acc=acc, edge_stencil=edge_stencil, d=1)
                    ddn_vort_z[i,:] = gradient(vort_z_wn[i,:] , s_wn[i,:], axis=0, acc=acc, edge_stencil=edge_stencil, d=1)
                    progress_bar.update()
                progress_bar.close()
            
            elif (s_wn.ndim==1): ## wall-normal distance (s_norm) is a 1D vector
                
                ddn_utang  = gradient(utang_wn  , s_wn, axis=1, acc=acc, edge_stencil=edge_stencil, d=1)
                ddn_vort_z = gradient(vort_z_wn , s_wn, axis=1, acc=acc, edge_stencil=edge_stencil, d=1)
            
            if (f'{gndata}/ddn_utang' in self): del self[f'{gndata}/ddn_utang']
            self.create_dataset(f'{gndata}/ddn_utang', data=ddn_utang.T, chunks=None)
            
            if (f'{gndata}/ddn_vort_z' in self): del self[f'{gndata}/ddn_vort_z']
            self.create_dataset(f'{gndata}/ddn_vort_z', data=ddn_vort_z.T, chunks=None)
            
            if ('data_1Dx/ddn_utang_wall' in self): del self['data_1Dx/ddn_utang_wall']
            self.create_dataset('data_1Dx/ddn_utang_wall', data=ddn_utang[:,0], chunks=None)
        
        else:
            
            ddn_utang  = np.copy( self[f'{gndata}/ddn_utang'][()].T  )
            ddn_vort_z = np.copy( self[f'{gndata}/ddn_vort_z'][()].T )
    
    else:
        raise ValueError
    
    # === calculate τ_wall & u_τ
    
    ## wall shear stress τ_wall
    if self.rectilinear:
        tau_wall = np.copy( mu_wall * ddy_u[:,0] )
    elif self.curvilinear:
        tau_wall = np.copy( mu_wall * ddn_utang[:,0] )
    else:
        raise ValueError
    
    ## τw
    ## [N/m²] = [kg/(m·s²)] = [Pa]
    if ('data_1Dx/tau_wall' in self): del self['data_1Dx/tau_wall']
    self.create_dataset('data_1Dx/tau_wall', data=tau_wall, chunks=None)
    if verbose: even_print('data_1Dx/tau_wall','%s'%str(tau_wall.shape))
    
    ## friction velocity u_τ [m/s]
    u_tau = np.copy( np.sqrt( tau_wall / rho_wall ) )
    
    if ('data_1Dx/u_tau' in self): del self['data_1Dx/u_tau']
    self.create_dataset('data_1Dx/u_tau', data=u_tau, chunks=None)
    if verbose: even_print('data_1Dx/u_tau','%s'%str(u_tau.shape))
    
    # === inner scales: length, velocity & time
    
    sc_u_in = np.copy( u_tau              )
    sc_l_in = np.copy( nu_wall / u_tau    )
    sc_t_in = np.copy( nu_wall / u_tau**2 )
    np.testing.assert_allclose(sc_t_in, sc_l_in/sc_u_in, rtol=1e-6, atol=1e-12)
    
    if ('data_1Dx/sc_u_in' in self): del self['data_1Dx/sc_u_in']
    self.create_dataset('data_1Dx/sc_u_in', data=sc_u_in, chunks=None)
    if verbose: even_print('data_1Dx/sc_u_in','%s'%str(sc_u_in.shape))
    
    if ('data_1Dx/sc_l_in' in self): del self['data_1Dx/sc_l_in']
    self.create_dataset('data_1Dx/sc_l_in', data=sc_l_in, chunks=None)
    if verbose: even_print('data_1Dx/sc_l_in','%s'%str(sc_l_in.shape))
    
    if ('data_1Dx/sc_t_in' in self): del self['data_1Dx/sc_t_in']
    self.create_dataset('data_1Dx/sc_t_in', data=sc_t_in, chunks=None)
    if verbose: even_print('data_1Dx/sc_t_in','%s'%str(sc_t_in.shape))
    
    self.get_header(verbose=False)
    if verbose: print(72*'-')
    if verbose: print('total time : ztmd.calc_wall_quantities() : %s'%format_time_string((timeit.default_timer() - t_start_func)))
    if verbose: print(72*'-')
    
    return

def _calc_bl_edge(self, **kwargs):
    '''
    Determine the boundary layer edge location (ZTMD wrapper)
    -----
    'method'=='u'         : 'edge' is where |du+/dy+|<ϵ
    'method'=='vorticity' : 'edge' is where |-ω+|<ϵ
    -----
    y_edge : the wall-normal edge location
    j_edge : the wall-normal edge location grid index
    '''
    
    verbose      = kwargs.get('verbose',True)
    method       = kwargs.get('method','vorticity') ## 'u','vorticity'
    epsilon      = kwargs.get('epsilon',5e-5)
    acc          = kwargs.get('acc',6)
    edge_stencil = kwargs.get('edge_stencil','full')
    interp_kind  = kwargs.get('interp_kind','cubic') ## 'linear','cubic'
    
    if verbose: print('\n'+'ztmd.calc_bl_edge()'+'\n'+72*'-')
    t_start_func = timeit.default_timer()
    
    ## Check rectilinear/curvilinear
    if (self.x.ndim==1) and (self.y.ndim==1):
        if hasattr(self,'rectilinear'):
            if not self.rectilinear:
                raise AssertionError
        if hasattr(self,'curvilinear'):
            if self.curvilinear:
                raise AssertionError
    elif (self.x.ndim==2) and (self.y.ndim==2):
        if hasattr(self,'rectilinear'):
            if self.rectilinear:
                raise AssertionError
        if hasattr(self,'curvilinear'):
            if not self.curvilinear:
                raise AssertionError
    else:
        raise ValueError
    
    ## Legacy check
    if hasattr(self,'requires_wall_norm_interp'):
        if self.requires_wall_norm_interp:
            raise NotImplementedError
    
    if not any([(method=='u'),(method=='vorticity')]):
        raise ValueError("'method' should be one of: 'u','vorticity'")
    if not any([(interp_kind=='linear'),(interp_kind=='cubic')]):
        raise ValueError("'interp_kind' should be one of: 'linear','cubic'")
    
    if verbose: even_print('method',method)
    if verbose: even_print('epsilon','%0.1e'%(epsilon,))
    if verbose: even_print('acc',f'{acc:d}')
    if verbose: even_print('edge_stencil',edge_stencil)
    if verbose: even_print('1D interp kind',interp_kind)
    
    # ===
    
    nx = self.nx
    #ny = self.ny
    
    ## copy 2D datasets into memory
    u = np.copy( self['data/u'][()].T ) ## dimensional
    
    u_tau   = np.copy( self['data_1Dx/u_tau'][()] ) ## uτ
    sc_l_in = np.copy( self['data_1Dx/sc_l_in'][()] ) ## δν = νw/uτ
    
    if self.rectilinear:
        
        x = np.copy( self['dims/x'][()] ) ## dimensional
        y = np.copy( self['dims/y'][()] )
    
    elif self.curvilinear:
        
        ## copy dims into memory
        x = np.copy( self['dims/x'][()].T ) ## 2D
        y = np.copy( self['dims/y'][()].T ) ## 2D
        
        if ('dims/snorm' not in self):
            raise AssertionError('dims/snorm not present')
        if ('dims/stang' not in self):
            raise AssertionError('dims/stang not present')
        
        snorm = np.copy( self['dims/snorm'][()] ) ## 1D
        #stang = np.copy( self['dims/stang'][()] ) ## 1D
        
        if ('data/utang' not in self):
            raise AssertionError('data/utang not present')
        
        utang = np.copy( self['data/utang'][()].T )
        #unorm = np.copy( self['data/unorm'][()].T )
        
        ## copy csys datasets into memory
        #vtang = np.copy( self['csys/vtang'][()] )
        vnorm = np.copy( self['csys/vnorm'][()] )
        
        if (x.shape != (self.nx,self.ny)):
            raise ValueError('x.shape != (self.nx,self.ny)')
        if (y.shape != (self.nx,self.ny)):
            raise ValueError('y.shape != (self.nx,self.ny)')
    
    else:
        raise ValueError
    
    # ===
    
    ## The local 1D wall-normal coordinate
    if self.rectilinear:
        y_ = np.copy(y)
    elif self.curvilinear:
        y_ = np.copy(snorm)
    else:
        raise ValueError
    
    # ===
    
    if (method=='vorticity'): ## use -ωz i.e. where |-ωz|<ϵ
        if 'data/vort_z' not in self:
            raise ValueError('data/vort_z not in ztmd')
        vort_z = np.copy( self['data/vort_z'][()].T )
    
    # ===
    
    j_edge    = np.zeros(shape=(nx,)  , dtype=np.int32   )
    y_edge    = np.zeros(shape=(nx,)  , dtype=np.float64 )
    y_edge_2d = np.zeros(shape=(nx,2) , dtype=np.float64 )
    
    if (method=='vorticity'): ## ωz is already the wall-normal derivative of pseudovelocity
        pass
    elif (method=='u'): ## pre-compute du/dy for efficiency
        if self.rectilinear:
            ddy_var = gradient(
                            u,
                            y_,
                            axis=1,
                            d=1,
                            acc=acc,
                            edge_stencil=edge_stencil,
                            )
        elif self.curvilinear:
            ddy_var = gradient(
                            utang,
                            y_,
                            axis=1,
                            d=1,
                            acc=acc,
                            edge_stencil=edge_stencil,
                            )
        else:
            raise ValueError
    else:
        raise ValueError
    
    if verbose: progress_bar = tqdm(total=nx, ncols=100, desc='y_edge', leave=False, file=sys.stdout)
    for i in range(nx):
        
        #do_debug_plot = False
        #if (i==5000):
        #    do_debug_plot = True
        
        if (method=='u'): ## |du+/dy+|<ϵ
            
            ddy_u_      = np.copy( ddy_var[i,:] ) ## du/dy
            ddy_u_plus_ = np.copy( ddy_u_ / ( u_tau[i] / sc_l_in[i] ) ) ## du+/dy+ = (du/dy)/(uτ/δν) = (du/dy)/(uτ^2/νw)
            
            y_edge_, j_edge_ = calc_profile_edge_1d(
                                y=y_,
                                ddy_u=ddy_u_plus_,
                                epsilon=epsilon,
                                )
        
        elif (method=='vorticity'): ## |-ωz+|<ϵ
            
            vort_z_      = np.copy( vort_z[i,:] ) ## ωz = (dv/dx)-(du/dy)
            vort_z_plus_ = np.copy( vort_z_ / ( u_tau[i] / sc_l_in[i] ) ) ## ωz+ = ωz/(uτ/δν) = ωz/(uτ^2/νw)
            
            y_edge_, j_edge_ = calc_profile_edge_1d(
                                y=y_,
                                ddy_u=-1*vort_z_plus_,
                                epsilon=epsilon,
                                )
        
        else:
            raise ValueError
        
        # ===
        
        y_edge[i] = y_edge_
        j_edge[i] = j_edge_
        
        ## 2D [x,y] coordinates of the 'edge line'
        if self.rectilinear:
            pt_edge_ = np.array([self.x[i],y_edge_], dtype=np.float64)
        elif self.curvilinear:
            p0_ = np.array([self.x[i,0],self.y[i,0]], dtype=np.float64)
            vnorm_ = np.copy( vnorm[i,0,:] ) ## unit normal vec @ wall at this x
            pt_edge_ = p0_ + np.dot( y_edge_ , vnorm_ )
        else:
            raise ValueError
        
        y_edge_2d[i,:] = pt_edge_
        
        progress_bar.update()
    progress_bar.close()
    
    if ('data_1Dx/y_edge' in self): del self['data_1Dx/y_edge']
    self.create_dataset('data_1Dx/y_edge', data=y_edge, chunks=None)
    if verbose: even_print('data_1Dx/y_edge','%s'%str(y_edge.shape))
    
    if ('data_1Dx/j_edge' in self): del self['data_1Dx/j_edge']
    self.create_dataset('data_1Dx/j_edge', data=j_edge, chunks=None)
    if verbose: even_print('data_1Dx/j_edge','%s'%str(j_edge.shape))
    
    if ('data_1Dx/y_edge_2d' in self): del self['data_1Dx/y_edge_2d']
    self.create_dataset('data_1Dx/y_edge_2d', data=y_edge_2d, chunks=None)
    if verbose: even_print('data_1Dx/y_edge_2d','%s'%str(y_edge_2d.shape))
    
    # ===
    
    self.get_header(verbose=False)
    if verbose: print(72*'-')
    if verbose: print('total time : ztmd.calc_bl_edge() : %s'%format_time_string((timeit.default_timer() - t_start_func)))
    if verbose: print(72*'-')
    return

def _calc_bl_edge_quantities(self, **kwargs):
    '''
    Calculate field quantity values at [y_edge]
    - Additionally, calculate cf
    '''
    
    verbose = kwargs.get('verbose',True)
    
    if verbose: print('\n'+'ztmd.calc_bl_edge_quantities()'+'\n'+72*'-')
    t_start_func = timeit.default_timer()
    
    # ===
    
    nx = self.nx
    ny = self.ny
    
    if self.rectilinear:
        
        ## copy dims into memory
        x = np.copy( self['dims/x'][()] )
        y = np.copy( self['dims/y'][()] )
    
    elif self.curvilinear:
        
        #if ('dims/snorm' not in self):
        #    raise AssertionError('dims/snorm not present')
        #if ('dims/stang' not in self):
        #    raise AssertionError('dims/stang not present')
        
        #snorm = np.copy( self['dims/snorm'][()] ) ## 1D
        #stang = np.copy( self['dims/stang'][()] ) ## 1D
        
        if ('data/utang' not in self):
            raise AssertionError('data/utang not present')
        
        ## copy dims into memory
        x = np.copy( self['dims/x'][()].T )
        y = np.copy( self['dims/y'][()].T )
        
        ## copy csys datasets into memory
        #vtang = np.copy( self['csys/vtang'][()] )
        #vnorm = np.copy( self['csys/vnorm'][()] )
        
        if (x.shape != (self.nx,self.ny)):
            raise ValueError('x.shape != (self.nx,self.ny)')
        if (y.shape != (self.nx,self.ny)):
            raise ValueError('y.shape != (self.nx,self.ny)')
    
    else:
        raise ValueError
    
    #y_edge = np.copy( self['data_1Dx/y_edge'][()]   )
    j_edge = np.copy( self['data_1Dx/j_edge'][()]   )
    
    # ## The local 1D wall-normal coordinate
    # if self.rectilinear:
    #     y_ = np.copy(y)
    # elif self.curvilinear:
    #     y_ = np.copy(snorm)
    # else:
    #     raise ValueError
    
    # === Make a numpy structured array
    
    names  = [ 'rho', 'u', 'v', 'w', 'T', 'p', 'vort_z', 'mu', 'nu', 'M' ]
    if ('data/psvel' in self):
        names += [ 'psvel' ]
    if ('data/utang' in self):
        names += [ 'utang' ]
    if ('data/unorm' in self):
        names += [ 'unorm' ]
    if ('data/umag' in self):
        names += [ 'umag' ]
    
    dtypes=[]
    for n in names:
        ds = self[f'data/{n}']
        dtypes.append( ds.dtype )
    
    names_edge = [ n+'_edge' for n in names ]
    
    data      = np.zeros(shape=(nx,ny), dtype={'names':names,      'formats':dtypes})
    data_edge = np.zeros(shape=(nx,),   dtype={'names':names_edge, 'formats':dtypes})
    
    ## populate 2D structured array with data to find edge for
    for scalar in data.dtype.names:
        data[scalar][:,:] = np.copy( self[f'data/{scalar}'][()].T )
    
    # === Interpolate edge quantity for all vars
    
    if verbose: progress_bar = tqdm(total=nx*len(names), ncols=100, desc='edge quantities', leave=False, file=sys.stdout)
    for scalar in data.dtype.names:
        for i in range(nx):
            je = j_edge[i]
            data_edge_ = data[scalar][i,je]
            data_edge[scalar+'_edge'][i] = data_edge_
            if verbose: progress_bar.update()
    if verbose: progress_bar.close()
    
    # === Write
    
    for scalar in data_edge.dtype.names:
        if (f'data_1Dx/{scalar}' in self):
            del self[f'data_1Dx/{scalar}']
        data_ = np.copy( data_edge[scalar][:] )
        dset = self.create_dataset(f'data_1Dx/{scalar}', data=data_, chunks=None)
        if verbose: even_print(f'data_1Dx/{scalar}',str(dset.shape))
    
    # ===
    
    # if False:
    #     plt.close('all')
    #     fig1 = plt.figure(figsize=(3*2,3), dpi=300)
    #     ax1 = plt.gca()
    #     ax1.plot( stang/self.lchar, data_edge['utang_edge']/self.U_inf, lw=0.5 )
    #     ax1.set_xlabel('stang')
    #     fig1.tight_layout(pad=0.25)
    #     fig1.tight_layout(pad=0.25)
    #     plt.show()
    
    # === Skin-friction coefficient cf = 2·τw/(ρe·ue^2) = 2/(ρe+·(ue+)^2)
    
    tau_wall = np.copy( self['data_1Dx/tau_wall'][()] )
    u_edge   = np.copy( data_edge['u_edge']   )
    rho_edge = np.copy( data_edge['rho_edge'] )
    
    if self.rectilinear:
        cf = np.copy( 2. * tau_wall / ( rho_edge * u_edge**2 ) )
    elif self.curvilinear:
        cf = np.copy( 2. * tau_wall / ( self.rho_inf * self.U_inf**2 ) )
    else:
        raise ValueError
    
    if ('data_1Dx/cf' in self): del self['data_1Dx/cf']
    self.create_dataset('data_1Dx/cf', data=cf, chunks=None)
    if verbose: even_print('data_1Dx/cf', '%s'%str(cf.shape))
    
    self.get_header(verbose=False)
    if verbose: print(72*'-')
    if verbose: print('total time : ztmd.calc_bl_edge_quantities() : %s'%format_time_string((timeit.default_timer() - t_start_func)))
    if verbose: print(72*'-')
    return

def _calc_d99(self, **kwargs):
    '''
    Calculate δ99 (ZTMD wrapper)
    δ = δ99 = y[ u(y) == 0.99*u_edge ]
    'u' can be pseudovelocity or streamwise velocity (set with 'method')
    '''
    
    verbose     = kwargs.get('verbose',True)
    method      = kwargs.get('method','psvel') ## 'u','psvel'
    interp_kind = kwargs.get('interp_kind','cubic') ## 'linear','cubic'
    
    if verbose: print('\n'+'ztmd.calc_d99()'+'\n'+72*'-')
    t_start_func = timeit.default_timer()
    
    if not any([(method=='u'),(method=='psvel')]):
        raise ValueError("'method' should be one of: 'u','psvel'")
    if not any([(interp_kind=='linear'),(interp_kind=='cubic')]):
        raise ValueError("'interp_kind' should be one of: 'linear','cubic'")
    
    if verbose: even_print('method',method)
    if verbose: even_print('1D interp kind',interp_kind)
    
    # ===
    
    nx = self.nx
    #ny = self.ny
    
    if self.rectilinear:
        
        ## copy dims into memory (1D)
        x = np.copy( self['dims/x'][()] )
        y = np.copy( self['dims/y'][()] )
    
    elif self.curvilinear:
        
        if ('dims/snorm' not in self):
            raise AssertionError('dims/snorm not present')
        if ('dims/stang' not in self):
            raise AssertionError('dims/stang not present')
        
        snorm = np.copy( self['dims/snorm'][()] ) ## 1D
        #stang = np.copy( self['dims/stang'][()] ) ## 1D
        
        if ('data/utang' not in self):
            raise AssertionError('data/utang not present')
        
        ## copy dims into memory (2D)
        x = np.copy( self['dims/x'][()].T )
        y = np.copy( self['dims/y'][()].T )
        
        ## copy csys datasets into memory
        #vtang = np.copy( self['csys/vtang'][()] )
        vnorm = np.copy( self['csys/vnorm'][()] )
        
        if (x.shape != (self.nx,self.ny)):
            raise ValueError('x.shape != (self.nx,self.ny)')
        if (y.shape != (self.nx,self.ny)):
            raise ValueError('y.shape != (self.nx,self.ny)')
    
    else:
        raise ValueError
    
    ## the local 1D wall-normal coordinate
    if self.rectilinear:
        y_ = np.copy(y)
    elif self.curvilinear:
        y_ = np.copy(snorm)
    else:
        raise ValueError
    
    ## The wall normal index of BL edge, as determined in e.g. ztmd.calc_bl_edge()
    j_edge = np.copy( self['data_1Dx/j_edge'][()] )
    
    ## get pseudovelocity / u / utang
    if (method=='psvel'):
        var      = np.copy( self['data/psvel'][()].T )
        var_edge = np.copy( self['data_1Dx/psvel_edge'][()].T )
    elif (method=='u'):
        if self.rectilinear:
            var      = np.copy( self['data/u'][()].T )
            var_edge = np.copy( self['data_1Dx/u_edge'][()] )
        elif self.curvilinear:
            var      = np.copy( self['data/utang'][()].T )
            var_edge = np.copy( self['data_1Dx/utang_edge'][()] )
        else:
            raise ValueError
    else:
        raise ValueError
    
    # ===
    
    d99     = np.zeros(shape=(nx,),  dtype=np.float64 )
    d99_2d  = np.zeros(shape=(nx,2), dtype=np.float64 )
    
    j99     = np.zeros(shape=(nx,),  dtype=np.int32   )
    d99g    = np.zeros(shape=(nx,),  dtype=np.float64 )
    
    if verbose: progress_bar = tqdm(total=nx, ncols=100, desc='δ', leave=False, file=sys.stdout)
    for i in range(nx):
        
        #y_edge_   = y_edge[i]
        j_edge_   = j_edge[i]
        var_      = np.copy( var[i,:] )
        var_edge_ = var_edge[i]
        
        d99_   = calc_d99_1d(y=y_, u=var_, j_edge=j_edge_, u_edge=var_edge_, interp_kind=interp_kind)
        d99[i] = d99_
        
        j99_    = np.abs( y_ - d99_ ).argmin()
        j99[i]  = j99_
        d99g[i] = y_[j99_]
        
        # ===
        
        ## Get the [x,y] coordinates of the 'd99 line' --> shape=(nx,2)
        if self.rectilinear:
            pt_99_ = np.array([self.x[i],d99_], dtype=np.float64)
        elif self.curvilinear:
            p0_ = np.array([self.x[i,0],self.y[i,0]], dtype=np.float64)
            vnorm_ = np.copy( vnorm[i,0,:] ) ## unit normal vec @ wall at this x
            pt_99_ = p0_ + np.dot( d99_ , vnorm_ )
        else:
            raise ValueError
        
        d99_2d[i,:] = pt_99_
        
        progress_bar.update()
    progress_bar.close()
    
    if ('data_1Dx/d99' in self): del self['data_1Dx/d99']
    self.create_dataset('data_1Dx/d99', data=d99, chunks=None)
    if verbose: even_print('data_1Dx/d99','%s'%str(d99.shape))
    
    if ('data_1Dx/d99_2d' in self): del self['data_1Dx/d99_2d']
    self.create_dataset('data_1Dx/d99_2d', data=d99_2d, chunks=None)
    if verbose: even_print('data_1Dx/d99_2d','%s'%str(d99_2d.shape))
    
    if ('data_1Dx/d99g' in self): del self['data_1Dx/d99g']
    self.create_dataset('data_1Dx/d99g', data=d99g, chunks=None)
    if verbose: even_print('data_1Dx/d99g','%s'%str(d99g.shape))
    
    if ('data_1Dx/j99' in self): del self['data_1Dx/j99']
    self.create_dataset('data_1Dx/j99', data=j99, chunks=None)
    if verbose: even_print('data_1Dx/j99','%s'%str(j99.shape))
    
    # ===
    
    self.get_header(verbose=False)
    if verbose: print(72*'-')
    if verbose: print('total time : ztmd.calc_d99() : %s'%format_time_string((timeit.default_timer() - t_start_func)))
    if verbose: print(72*'-')
    return

def _calc_d99_quantities(self, **kwargs):
    '''
    Calculate interpolated field quantity values at y=δ99
    '''
    
    verbose     = kwargs.get('verbose',True)
    interp_kind = kwargs.get('interp_kind','cubic') ## 'linear','cubic'
    
    if verbose: print('\n'+'ztmd.calc_d99_quantities()'+'\n'+72*'-')
    t_start_func = timeit.default_timer()
    
    if not any([(interp_kind=='linear'),(interp_kind=='cubic')]):
        raise ValueError("'interp_kind' should be one of: 'linear','cubic'")
    
    if verbose: even_print('1D interp kind',interp_kind)
    
    nx = self.nx
    ny = self.ny
    
    if self.rectilinear:
        
        ## copy dims into memory
        x = np.copy( self['dims/x'][()] )
        y = np.copy( self['dims/y'][()] )
    
    elif self.curvilinear:
        
        if ('dims/snorm' not in self):
            raise AssertionError('dims/snorm not present')
        if ('dims/stang' not in self):
            raise AssertionError('dims/stang not present')
        
        snorm = np.copy( self['dims/snorm'][()] ) ## 1D
        #stang = np.copy( self['dims/stang'][()] ) ## 1D
        
        if ('data/utang' not in self):
            raise AssertionError('data/utang not present')
        
        ## copy dims into memory
        x = np.copy( self['dims/x'][()].T )
        y = np.copy( self['dims/y'][()].T )
        
        ## copy csys datasets into memory
        #vtang = np.copy( self['csys/vtang'][()] )
        #vnorm = np.copy( self['csys/vnorm'][()] )
        
        if (x.shape != (self.nx,self.ny)):
            raise ValueError('x.shape != (self.nx,self.ny)')
        if (y.shape != (self.nx,self.ny)):
            raise ValueError('y.shape != (self.nx,self.ny)')
    
    else:
        raise ValueError
    
    d99 = np.copy( self['data_1Dx/d99'][()] )
    
    ## Local 1D wall-normal coordinate
    if self.rectilinear:
        y_ = np.copy(y)
    elif self.curvilinear:
        y_ = np.copy(snorm)
    else:
        raise ValueError
    
    # === Make a structured array
    
    names  = [ 'rho', 'u', 'v', 'w', 'T', 'p', 'vort_z', 'mu', 'nu', 'M' ]
    if ('data/psvel' in self):
        names += [ 'psvel' ]
    if ('data/utang' in self):
        names += [ 'utang' ]
    if ('data/unorm' in self):
        names += [ 'unorm' ]
    if ('data/umag' in self):
        names += [ 'umag' ]
    
    dtypes=[]
    for n in names:
        ds = self[f'data/{n}']
        dtypes.append( ds.dtype )
    
    #names_99 = [ n+'99' for n in names ]
    names_99 = [ n+'_99' if ('_' in n) else n+'99' for n in names ]
    
    data    = np.zeros(shape=(nx,ny), dtype={'names':names,    'formats':dtypes})
    data_99 = np.zeros(shape=(nx,),   dtype={'names':names_99, 'formats':dtypes})
    
    # === populate structured array
    
    for scalar in data.dtype.names:
        data[scalar][:,:] = np.copy( self[f'data/{scalar}'][()].T )
    
    ## Main loop: interpolate @ δ99 for all vars
    if verbose: progress_bar = tqdm(total=nx*len(names), ncols=100, desc='δ99 quantities', leave=False, file=sys.stdout)
    for ni,scalar in enumerate(data.dtype.names):
        for i in range(nx):
            
            data_y_    = np.copy( data[scalar][i,:] )
            intrp_func = interp1d(y_, data_y_, kind=interp_kind, bounds_error=True)
            
            d99_    = d99[i]
            data_99_ = intrp_func(d99_)
            
            data_99[names_99[ni]][i] = data_99_
            
            if verbose: progress_bar.update()
    if verbose: progress_bar.close()
    
    ## Write
    for scalar in data_99.dtype.names:
        if (f'data_1Dx/{scalar}' in self):
            del self[f'data_1Dx/{scalar}']
        data_ = np.copy( data_99[scalar][:] )
        dset = self.create_dataset(f'data_1Dx/{scalar}', data=data_, chunks=None)
        if verbose: even_print(f'data_1Dx/{scalar}',str(dset.shape))
    
    ## Outer (here 99) scales: length, velocity & time
    sc_l_out = np.copy(d99)
    if self.rectilinear:
        sc_u_out = np.copy( data_99['u99'] )
        sc_t_out = np.copy( d99/data_99['u99'] )
    elif self.curvilinear:
        sc_u_out = np.copy( data_99['utang99'] )
        sc_t_out = np.copy( d99/data_99['utang99'] )
    else:
        raise ValueError
    
    np.testing.assert_allclose(sc_t_out, sc_l_out/sc_u_out, rtol=1e-12, atol=1e-12)
    
    u_tau = np.copy( self['data_1Dx/u_tau'][()] )
    sc_t_eddy = np.copy( d99/u_tau )
    
    if ('data_1Dx/sc_u_out' in self): del self['data_1Dx/sc_u_out']
    self.create_dataset('data_1Dx/sc_u_out', data=sc_u_out, chunks=None)
    if verbose: even_print('data_1Dx/sc_u_out', '%s'%str(sc_u_out.shape))
    
    if ('data_1Dx/sc_l_out' in self): del self['data_1Dx/sc_l_out']
    self.create_dataset('data_1Dx/sc_l_out', data=sc_l_out, chunks=None)
    if verbose: even_print('data_1Dx/sc_l_out', '%s'%str(sc_l_out.shape))
    
    if ('data_1Dx/sc_t_out' in self): del self['data_1Dx/sc_t_out']
    self.create_dataset('data_1Dx/sc_t_out', data=sc_t_out, chunks=None)
    if verbose: even_print('data_1Dx/sc_t_out', '%s'%str(sc_t_out.shape))
    
    if ('data_1Dx/sc_t_eddy' in self): del self['data_1Dx/sc_t_eddy']
    self.create_dataset('data_1Dx/sc_t_eddy', data=sc_t_eddy, chunks=None)
    if verbose: even_print('data_1Dx/sc_t_eddy', '%s'%str(sc_t_eddy.shape))
    
    self.get_header(verbose=False)
    if verbose: print(72*'-')
    if verbose: print('total time : ztmd.calc_d99_quantities() : %s'%format_time_string((timeit.default_timer() - t_start_func)))
    if verbose: print(72*'-')
    return

def _calc_bl_integral_quantities(self, **kwargs):
    '''
    Calculate boundary layer integral quantities (ZTMD wrapper)
    δ*=δ1, θ=δ2, Reθ, Reδ2, H12, H32, etc.
    -----
    - Also: Reδ2, Reδ99 out of convenience
    '''
    verbose     = kwargs.get('verbose', True)
    interp_kind = kwargs.get('interp_kind', 'cubic')
    
    if interp_kind not in ('linear', 'cubic'):
        raise ValueError("'interp_kind' should be one of: 'linear','cubic'")
    
    if verbose:
        print('\n' + 'ztmd.calc_bl_integral_quantities()' + '\n' + 72*'-')
    t_start_func = timeit.default_timer()
    
    nx = self.nx
    #ny = self.ny
    
    ## Geometry: Flat-plate vs Curved
    if self.rectilinear:
        y  = np.copy(self['dims/y'][()])
        y_ = y
    elif self.curvilinear:
        y_ = np.copy(self['dims/snorm'][()])
    else:
        raise ValueError
    
    ## 1D [x] profiles
    u_tau    = np.copy(self['data_1Dx/u_tau'][()])
    rho_wall = np.copy(self['data_1Dx/rho_wall'][()])
    nu_wall  = np.copy(self['data_1Dx/nu_wall'][()])
    mu_wall  = np.copy(self['data_1Dx/mu_wall'][()])
    
    #y_edge   = np.copy(self['data_1Dx/y_edge'][()])
    j_edge   = np.copy(self['data_1Dx/j_edge'][()])
    d99      = np.copy(self['data_1Dx/d99'][()])
    rho_edge = np.copy(self['data_1Dx/rho_edge'][()])
    mu_edge  = np.copy(self['data_1Dx/mu_edge'][()])
    nu_edge  = np.copy(self['data_1Dx/nu_edge'][()])
    
    if self.rectilinear:
        u_edge    = np.copy( self['data_1Dx/u_edge'][()])
        #u_Fv_edge = np.copy( self['data_1Dx/u_Fv_edge'][()] )
    else:
        u_edge = np.copy(self['data_1Dx/utang_edge'][()]) ## !! reading 'utang' as local 'u' !!
        #u_Fv_edge = np.copy( self['data_1Dx/utang_Fv_edge'][()] ) ## never tested
    
    ## 2D data
    u   = np.copy(self['data/u'][()].T)
    rho = np.copy(self['data/rho'][()].T)
    
    if self.curvilinear:
        u = np.copy(self['data/utang'][()].T)
    
    ## Output arrays
    d1    = np.full((nx,), np.nan, dtype=np.float64)
    d1_k  = np.full((nx,), np.nan, dtype=np.float64)
    d2    = np.full((nx,), np.nan, dtype=np.float64)
    d2_k  = np.full((nx,), np.nan, dtype=np.float64)
    d3    = np.full((nx,), np.nan, dtype=np.float64)
    d3_k  = np.full((nx,), np.nan, dtype=np.float64)
    dRC   = np.full((nx,), np.nan, dtype=np.float64)
    dRC_k = np.full((nx,), np.nan, dtype=np.float64)
    
    I2   = np.full((nx,), np.nan, dtype=np.float64)
    I2_k = np.full((nx,), np.nan, dtype=np.float64)
    I3   = np.full((nx,), np.nan, dtype=np.float64)
    I3_k = np.full((nx,), np.nan, dtype=np.float64)
    
    if verbose:
        progress_bar = tqdm(total=nx, ncols=100, desc='BL integrals', leave=False)
    
    # Main loop
    # ==================================================================
    
    for i in range(nx):
        
        u_        = u[i,:]
        rho_      = rho[i,:]
        #y_edge_   = y_edge[i]
        j_edge_   = j_edge[i]
        u_edge_   = u_edge[i]
        u_tau_    = u_tau[i]
        rho_edge_ = rho_edge[i]
        rho_wall_ = rho_wall[i]
        
        ## Compressible integrals
        
        #u_edge_ = u_Fv_edge[i]
        
        d1[i] = calc_d1(
            y_, u_,
            rho=rho_,
            j_edge=j_edge_,
            u_edge=u_edge_,
            rho_edge=rho_edge_,
            )
        
        d2[i] = calc_d2(
            y_, u_,
            rho=rho_,
            j_edge=j_edge_,
            u_edge=u_edge_,
            rho_edge=rho_edge_,
            )
        
        d3[i] = calc_d3(
            y_, u_,
            rho=rho_,
            j_edge=j_edge_,
            u_edge=u_edge_,
            rho_edge=rho_edge_,
            )
        
        dRC[i] = calc_dRC(
            y_, u_,
            u_tau=u_tau_,
            rho=rho_,
            j_edge=j_edge_,
            u_edge=u_edge_,
            rho_edge=rho_edge_,
            rho_wall=rho_wall_,
            )
        
        I2[i] = calc_I2(
            y_, u_,
            u_tau=u_tau_,
            rho=rho_,
            j_edge=j_edge_,
            u_edge=u_edge_,
            rho_edge=rho_edge_,
            rho_wall=rho_wall_,
            )
        
        I3[i] = calc_I3(
            y_, u_,
            u_tau=u_tau_,
            rho=rho_,
            j_edge=j_edge_,
            u_edge=u_edge_,
            rho_edge=rho_edge_,
            rho_wall=rho_wall_,
            )
        
        ## Kinetic (u-only) integrals
        
        #u_edge_ = u_Fv_edge[i]
        u_edge_ = u_edge[i]
        
        d1_k[i] = calc_d1(
            y_, u_,
            rho=None,
            j_edge=j_edge_,
            u_edge=u_edge_,
            rho_edge=None,
            )
        
        d2_k[i] = calc_d2(
            y_, u_,
            rho=None,
            j_edge=j_edge_,
            u_edge=u_edge_,
            rho_edge=None,
            )
        
        d3_k[i] = calc_d3(
            y_, u_,
            rho=None,
            j_edge=j_edge_,
            u_edge=u_edge_,
            rho_edge=None,
            )
        
        dRC_k[i] = calc_dRC(
            y_, u_,
            u_tau=u_tau_,
            rho=None,
            j_edge=j_edge_,
            u_edge=u_edge_,
            rho_edge=None,
            rho_wall=None,
            )
        
        I2_k[i] = calc_I2(
            y_, u_,
            u_tau=u_tau_,
            rho=None,
            j_edge=j_edge_,
            u_edge=u_edge_,
            rho_edge=None,
            rho_wall=None,
            )
        
        I3_k[i] = calc_I3(
            y_, u_,
            u_tau=u_tau_,
            rho=None,
            j_edge=j_edge_,
            u_edge=u_edge_,
            rho_edge=None,
            rho_wall=None,
            )
        
        if verbose:
            progress_bar.update()
    
    if verbose:
        progress_bar.close()
    
    # ===
    
    ## alias
    dstar   = np.copy( d1   ) ## δ* = δ1
    dstar_k = np.copy( d1_k )
    
    ## alias
    theta   = np.copy( d2   ) ## θ = δ2
    theta_k = np.copy( d2_k )
    
    H12   = np.copy( d1   / d2   ) ## H12 = δ*/θ
    H12_k = np.copy( d1_k / d2_k )
    H32   = np.copy( d3   / d2   ) ## H32 = δ3/δ2
    H32_k = np.copy( d3_k / d2_k )
    
    ## νw = μw / ρw
    np.testing.assert_allclose(
        nu_wall,
        mu_wall / rho_wall,
        rtol=1e-6,
        )
    
    ## νe = μe / ρe
    np.testing.assert_allclose(
        nu_edge,
        mu_edge / rho_edge,
        rtol=1e-6,
        )
    
    ## Reynolds numbers
    Re_tau     = np.copy( d99     * u_tau  * rho_wall / mu_wall ) ## Reτ = δ99·uτ·ρw / μw
    Re_theta   = np.copy( theta   * u_edge * rho_edge / mu_edge ) ## Reθ = θ·ue·ρe / μe
    Re_dstar   = np.copy( dstar   * u_edge * rho_edge / mu_edge ) ## Reδ* = δ*·ue·ρe / μe
    Re_d2      = np.copy( theta   * u_edge * rho_edge / mu_wall ) ## Reδ2 = θ·ue·ρe / μw
    Re_d99     = np.copy( d99     * u_edge * rho_edge / mu_edge ) ## Reδ99 = δ99·ue·ρe / μe
    Re_theta_k = np.copy( theta_k * u_edge * rho_edge / mu_edge ) ## Reθk = θk·ue·ρe / μe
    Re_dstar_k = np.copy( dstar_k * u_edge * rho_edge / mu_edge ) ## Reδ*k = δ*k·ue·ρe / μe
    
    ## Reδ2 = Reθk = (μe/μw)·Reθ ≈ (μ∞/μw)·Reθ
    np.testing.assert_allclose(
        Re_d2,
        (mu_edge / mu_wall) * Re_theta,
        rtol=1e-6,
        )
    
    ## H12 = δ*/θ = Reδ*/Reθ
    np.testing.assert_allclose(
        Re_dstar / Re_theta,
        H12,
        rtol=1e-6,
        )
    
    ## H12k = δ*k/θk = Reδ*k/Reθk
    np.testing.assert_allclose(
        Re_dstar_k / Re_theta_k,
        H12_k,
        rtol=1e-6,
        )
    
    uplus_edge   = np.copy( u_edge   / u_tau    )
    rhoplus_edge = np.copy( rho_edge / rho_wall )
    muplus_edge  = np.copy( mu_edge  / mu_wall  )
    
    ## Reδ*/Reτ = (δ*/δ99)·(ue/uτ)·(ρe/ρw)·(μw/μe)
    ##          = (δ*/δ99)·(ue+·ρe+/μe+)
    np.testing.assert_allclose(
        Re_dstar / Re_tau,
        ( dstar / d99 ) * uplus_edge * rhoplus_edge / muplus_edge,
        rtol=1e-6,
        )
    
    ## Reθ/Reτ = (θ/δ99)·(ue/uτ)·(ρe/ρw)·(μw/μe)
    ##         = (θ/δ99)·(ue+·ρe+/μe+)
    np.testing.assert_allclose(
        Re_theta / Re_tau,
        ( theta / d99 ) * uplus_edge * rhoplus_edge / muplus_edge,
        rtol=1e-6,
        )
    
    ## Helper for writing datasets
    def _write(name, arr):
        if name in self: ## Delete if exists
            del self[name]
        self.create_dataset(name, data=arr, chunks=None) ## Write
        if verbose:
            even_print(name, str(arr.shape))
    
    ## Write datasets to ZTMD HDF5
    _write('data_1Dx/d1'      , d1      )
    _write('data_1Dx/d1_k'    , d1_k    )
    _write('data_1Dx/dstar'   , dstar   )
    _write('data_1Dx/dstar_k' , dstar_k )
    
    _write('data_1Dx/d2'      , d2      )
    _write('data_1Dx/d2_k'    , d2_k    )
    _write('data_1Dx/theta'   , theta   )
    _write('data_1Dx/theta_k' , theta_k )
    
    _write('data_1Dx/d3'    , d3   )
    _write('data_1Dx/d3_k'  , d3_k )
    
    _write('data_1Dx/dRC'   , dRC   )
    _write('data_1Dx/dRC_k' , dRC_k )
    
    _write('data_1Dx/H12'   , H12   )
    _write('data_1Dx/H12_k' , H12_k )
    _write('data_1Dx/H32'   , H32   )
    _write('data_1Dx/H32_k' , H32_k )
    
    _write('data_1Dx/I2'   , I2   )
    _write('data_1Dx/I2_k' , I2_k )
    _write('data_1Dx/I3'   , I3   )
    _write('data_1Dx/I3_k' , I3_k )
    
    _write('data_1Dx/Re_tau'     , Re_tau     )
    _write('data_1Dx/Re_theta'   , Re_theta   )
    _write('data_1Dx/Re_theta_k' , Re_theta_k )
    _write('data_1Dx/Re_d99'     , Re_d99     )
    _write('data_1Dx/Re_d2'      , Re_d2      )
    _write('data_1Dx/Re_dstar'   , Re_dstar   )
    _write('data_1Dx/Re_dstar_k' , Re_dstar_k )
    
    ## Update header
    self.get_header(verbose=False)
    
    if verbose:
        print(72*'-')
        print(
            'total time : ztmd.calc_bl_integral_quantities() : %s'
            % format_time_string(timeit.default_timer() - t_start_func)
            )
        print(72*'-')
    
    return

# ======================================================================

def _calc_wake_parameter(self, **kwargs):
    '''
    Calculate the Coles wake parameter Π (ZTMD wrapper)
    '''
    
    verbose = kwargs.get('verbose',True)
    
    ## Von Kármán constant (κ)
    k = kwargs.get('k',0.384)
    
    ## Log-law intercept (B) : u+ = (1/κ)·ln(y+) + B
    ## see Nagib et al. (2007)
    B = kwargs.get('B',4.173)
    
    if verbose: print('\n'+'ztmd.calc_wake_parameter()'+'\n'+72*'-')
    t_start_func = timeit.default_timer()
    
    ## Check
    # ...
    
    if verbose: even_print('κ',f'{k:0.5f}')
    if verbose: even_print('B',f'{B:0.5f}')
    
    if self.curvilinear:
        raise NotImplementedError('ztmd.calc_wake_parameter() has not been implemented for curved cases')
    
    ## Read data
    u_tau   = np.copy( self['data_1Dx/u_tau'][()]   ) ## uτ
    sc_l_in = np.copy( self['data_1Dx/sc_l_in'][()] ) ## δν = νw/uτ
    d99     = np.copy( self['data_1Dx/d99'][()]     ) ## δ99
    u99     = np.copy( self['data_1Dx/u99'][()]     ) ## u(δ99)
    u       = np.copy( self['data/u'][()].T         )
    
    doVD   = False
    doTL   = False
    doVIPL = False
    doGFM  = False
    
    ## Output array
    wake_parameter = np.full((self.nx,),np.nan,dtype=np.float64)
    
    if 'data/u_VD' in self: ## van-Driest
        doVD   = True
        u_VD   = np.copy( self['data/u_VD'][()].T      )
        u99_VD = np.copy( self['data_1Dx/u_99_VD'][()] )
        d99_VD = np.copy( self['data_1Dx/d99_VD'][()]  )
        wake_parameter_VD = np.full((self.nx,),np.nan,dtype=np.float64)
    
    if 'data/u_TL' in self: ## Trettel & Larsson
        doTL   = True
        u_TL   = np.copy( self['data/u_TL'][()].T      )
        y_TL   = np.copy( self['data/y_TL'][()].T      )
        u99_TL = np.copy( self['data_1Dx/u_99_TL'][()] )
        d99_TL = np.copy( self['data_1Dx/d99_TL'][()]  )
        wake_parameter_TL = np.full((self.nx,),np.nan,dtype=np.float64)
    
    if 'data/u_VIPL' in self: ## Volpiani et al.
        doVIPL   = True
        u_VIPL   = np.copy( self['data/u_VIPL'][()].T      )
        y_VIPL   = np.copy( self['data/y_VIPL'][()].T      )
        u99_VIPL = np.copy( self['data_1Dx/u_99_VIPL'][()] )
        d99_VIPL = np.copy( self['data_1Dx/d99_VIPL'][()]  )
        wake_parameter_VIPL = np.full((self.nx,),np.nan,dtype=np.float64)
    
    if 'data/u_GFM' in self: ## Griffin,Fu & Moin
        doGFM   = True
        u_GFM   = np.copy( self['data/u_GFM'][()].T      )
        y_GFM   = np.copy( self['data/y_GFM'][()].T      )
        u99_GFM = np.copy( self['data_1Dx/u_99_GFM'][()] )
        d99_GFM = np.copy( self['data_1Dx/d99_GFM'][()]  )
        wake_parameter_GFM = np.full((self.nx,),np.nan,dtype=np.float64)
    
    if verbose:
        progress_bar = tqdm(
                        total=self.nx,
                        ncols=100,
                        desc='wake parameter',
                        leave=False,
                        file=sys.stdout,
                        )
    for i in range(self.nx):
        
        ## Untransformed
        yplus   = self.y / sc_l_in[i]
        uplus   = u[i,:] / u_tau[i]
        d99plus = d99[i] / sc_l_in[i] ## δ99+
        u99plus = u99[i] / u_tau[i]   ## u+(δ99) for check
        wake_parameter[i] = calc_wake_parameter_1d(yplus=yplus, uplus=uplus, dplus=d99plus, uplus_delta=u99plus, k=k, B=B)
        
        if doVD:
            yplus   = self.y    / sc_l_in[i]
            uplus   = u_VD[i,:] / u_tau[i]
            d99plus = d99_VD[i] / sc_l_in[i]
            u99plus = u99_VD[i] / u_tau[i]
            wake_parameter_VD[i] = calc_wake_parameter_1d(yplus=yplus, uplus=uplus, dplus=d99plus, uplus_delta=u99plus, k=k, B=B)
        
        if doTL:
            yplus   = y_TL[i,:] / sc_l_in[i]
            uplus   = u_TL[i,:] / u_tau[i]
            d99plus = d99_TL[i] / sc_l_in[i]
            u99plus = u99_TL[i] / u_tau[i]
            wake_parameter_TL[i] = calc_wake_parameter_1d(yplus=yplus, uplus=uplus, dplus=d99plus, uplus_delta=u99plus, k=k, B=B)
        
        if doVIPL:
            yplus   = y_VIPL[i,:] / sc_l_in[i]
            uplus   = u_VIPL[i,:] / u_tau[i]
            d99plus = d99_VIPL[i] / sc_l_in[i]
            u99plus = u99_VIPL[i] / u_tau[i]
            wake_parameter_VIPL[i] = calc_wake_parameter_1d(yplus=yplus, uplus=uplus, dplus=d99plus, uplus_delta=u99plus, k=k, B=B)
        
        if doGFM:
            yplus   = y_GFM[i,:] / sc_l_in[i]
            uplus   = u_GFM[i,:] / u_tau[i]
            d99plus = d99_GFM[i] / sc_l_in[i]
            u99plus = u99_GFM[i] / u_tau[i]
            wake_parameter_GFM[i] = calc_wake_parameter_1d(yplus=yplus, uplus=uplus, dplus=d99plus, uplus_delta=u99plus, k=k, B=B)
        
        progress_bar.update()
    progress_bar.close()
    
    ## Helper for writing 1D datasets to data_1Dx/
    def _write_1D(name, arr):
        if name in self: ## Delete if exists
            del self[name]
        self.create_dataset(f'data_1Dx/{name}', data=arr, chunks=None) ## Write
        if verbose:
            even_print(f'data_1Dx/{name}', str(arr.shape))
    
    _write_1D('wake_parameter' , wake_parameter)
    
    if doVD:   _write_1D('wake_parameter_VD'   , wake_parameter_VD   )
    if doTL:   _write_1D('wake_parameter_TL'   , wake_parameter_TL   )
    if doVIPL: _write_1D('wake_parameter_VIPL' , wake_parameter_VIPL )
    if doGFM:  _write_1D('wake_parameter_GFM'  , wake_parameter_GFM  )
    
    self.get_header(verbose=False)
    if verbose: print(72*'-')
    if verbose: print('total time : ztmd.calc_wake_parameter() : %s'%format_time_string((timeit.default_timer() - t_start_func)))
    if verbose: print(72*'-')

def _calc_peak_tauI(self, **kwargs):
    '''
    Calculate peak τ′xx, τ′xy, τ′yy
    '''
    
    verbose = kwargs.get('verbose',True)
    
    if verbose: print('\n'+'ztmd.calc_peak_tauI()'+'\n'+72*'-')
    t_start_func = timeit.default_timer()
    
    ## check
    if self.rectilinear:
        pass
    elif self.curvilinear:
        #raise NotImplementedError('ztmd.calc_peak_tauI() has not been implemented for curved cases')
        print('>>> ztmd.calc_peak_tauI() has not been implemented for curved cases')
        return
    else:
        raise ValueError
    
    ## Check data availability
    if 'data_1Dx/sc_l_in' not in self:
        raise ValueError('data_1Dx/sc_l_in not found')
    if 'data/r_uII_uII' not in self:
        raise ValueError('data/r_uII_uII not found')
    if 'data/r_uII_vII' not in self:
        raise ValueError('data/r_uII_vII not found')
    if 'data/r_vII_vII' not in self:
        raise ValueError('data/r_vII_vII not found')
    
    r_uII_uII = np.copy( self['data/r_uII_uII'][()].T )
    r_uII_vII = np.copy( self['data/r_uII_vII'][()].T )
    r_vII_vII = np.copy( self['data/r_vII_vII'][()].T )
    
    y        = np.copy( self['dims/y'][()]            )
    tau_wall = np.copy( self['data_1Dx/tau_wall'][()] )
    sc_l_in  = np.copy( self['data_1Dx/sc_l_in'][()]  )
    sc_l_out = np.copy( self['data_1Dx/sc_l_out'][()] )
    nu_wall  = np.copy( self['data_1Dx/nu_wall'][()]  )
    u_tau    = np.copy( self['data_1Dx/u_tau'][()]    )
    d99      = np.copy( self['data_1Dx/d99'][()]      )
    
    np.testing.assert_allclose(sc_l_in  , nu_wall/u_tau , rtol=1e-12, atol=1e-12)
    np.testing.assert_allclose(sc_l_out , d99           , rtol=1e-12, atol=1e-12)
    
    r_uII_uII_plus = np.copy( r_uII_uII / tau_wall[:,np.newaxis] )
    r_uII_vII_plus = np.copy( r_uII_vII / tau_wall[:,np.newaxis] )
    r_vII_vII_plus = np.copy( r_vII_vII / tau_wall[:,np.newaxis] )
    
    tau_xx_I_peak   = np.zeros((self.nx,), dtype=np.float64)
    tau_xx_I_peak_y = np.zeros((self.nx,), dtype=np.float64)
    
    tau_xy_I_peak   = np.zeros((self.nx,), dtype=np.float64)
    tau_xy_I_peak_y = np.zeros((self.nx,), dtype=np.float64)
    
    tau_yy_I_peak   = np.zeros((self.nx,), dtype=np.float64)
    tau_yy_I_peak_y = np.zeros((self.nx,), dtype=np.float64)
    
    # ===
    
    def __opt_find_peak(y_plus_pk,func):
        root = func(y_plus_pk,1)
        return root
    
    if verbose: progress_bar = tqdm(total=self.nx, ncols=100, desc='peak τ′', leave=False, file=sys.stdout)
    #for i in [5000,10000,15000]:
    for i in range(self.nx):
        
        y_plus_  = np.copy( y / sc_l_in[i]  )
        #yovd_    = np.copy( y / sc_l_out[i] )
        
        r_uII_uII_plus_ = np.copy( r_uII_uII_plus[i,:] )
        r_uII_vII_plus_ = np.copy( r_uII_vII_plus[i,:] )
        r_vII_vII_plus_ = np.copy( r_vII_vII_plus[i,:] )
        
        # === τ′xx
        
        i_naive = np.argmax( r_uII_uII_plus_ )
        #tau_xx_I_peak_naive_ = r_uII_uII_plus_[i_naive]
        
        func_tauIxx = CubicSpline( y_plus_ , r_uII_uII_plus_ , bc_type='natural', extrapolate=False )
        
        bounds_ = ( max(y_plus_[i_naive]*0.9,y_plus_.min()) , min(y_plus_[i_naive]*1.1,y_plus_.max()) )
        
        sol = least_squares(
                fun=__opt_find_peak,
                args=(func_tauIxx,),
                x0=y_plus_[i_naive],
                xtol=1e-15,
                ftol=1e-15,
                gtol=1e-15,
                method='dogbox',
                bounds=bounds_,
                )
        if not sol.success:
            raise ValueError
        
        y_plus_pk_ = float(sol.x[0])
        tau_xx_I_peak[i]   = func_tauIxx(y_plus_pk_) * tau_wall[i] ## re-dimensionalizing
        tau_xx_I_peak_y[i] = y_plus_pk_              * sc_l_in[i]  ## re-dimensionalizing
        
        # ===
        
        # ## debug plot for τ′xx
        # #if (i==5000) or (i==10000) or (i==15000):
        # if 0:
        #     
        #     plt.close('all')
        #     fig1 = plt.figure(figsize=(3,2), dpi=400)
        #     ax1 = plt.gca()
        #     
        #     ax1.tick_params(axis='x', which='both', direction='in')
        #     ax1.tick_params(axis='y', which='both', direction='in')
        #     #ax1.xaxis.set_ticks_position('both')
        #     #ax1.yaxis.set_ticks_position('both')
        #     ax1.set_xscale('log',base=10)
        #     #ax1.set_yscale('log',base=10)
        #     
        #     #ax1.set_xlim(100,3000)
        #     #ax1.xaxis.set_major_locator(mpl.ticker.LogLocator(subs=(1,)))
        #     #ax1.xaxis.set_minor_locator(mpl.ticker.LogLocator(subs=np.linspace(1,9,9)))
        #     #ax1.xaxis.set_minor_formatter(mpl.ticker.NullFormatter())
        #     
        #     ax1.plot(
        #     y_plus_,
        #     r_uII_uII_plus_,
        #     c='k',
        #     zorder=19,
        #     lw=0.8,
        #     marker='o',
        #     ms=1.5,
        #     ls='none',
        #     )
        #     
        #     y_plus_dummy_          = np.logspace(np.log10(1),np.log10(1000),1000)
        #     r_uII_uII_plus_spline_ = func_tauIxx(y_plus_dummy_)
        #     
        #     ax1.plot(
        #     y_plus_dummy_,
        #     r_uII_uII_plus_spline_,
        #     c='blue',
        #     zorder=19,
        #     lw=0.8,
        #     #marker='o',
        #     #ms=1.5,
        #     #ls='none',
        #     )
        #     
        #     ax1.axvline(x=y_plus_pk_       , linestyle='solid', c='gray', zorder=1, lw=0.5)
        #     ax1.axhline(y=func_tauIxx(y_plus_pk_) , linestyle='solid', c='gray', zorder=1, lw=0.5)
        #     
        #     plt.show()
        
        # === τ′xy
        
        i_naive = np.argmin( r_uII_vII_plus_ ) ## ACHTUNG argmin(), NOT argmax() !!
        #tau_xy_I_peak_naive_ = r_uII_vII_plus_[i_naive]
        
        func_tauIxy = CubicSpline( y_plus_ , r_uII_vII_plus_ , bc_type='natural', extrapolate=False )
        
        bounds_ = ( max(y_plus_[i_naive]*0.9,y_plus_.min()) , min(y_plus_[i_naive]*1.1,y_plus_.max()) )
        
        sol = least_squares(
                fun=__opt_find_peak,
                args=(func_tauIxy,),
                x0=y_plus_[i_naive],
                xtol=1e-15,
                ftol=1e-15,
                gtol=1e-15,
                method='dogbox',
                bounds=bounds_,
                )
        if not sol.success:
            raise ValueError
        
        y_plus_pk_ = float(sol.x[0])
        tau_xy_I_peak[i]   = func_tauIxy(y_plus_pk_) * tau_wall[i] ## re-dimensionalizing
        tau_xy_I_peak_y[i] = y_plus_pk_              * sc_l_in[i]  ## re-dimensionalizing
        
        # ===
        
        # ## debug plot for τ′xy
        # #if (i==5000) or (i==10000) or (i==15000):
        # if 0:
        #     
        #     plt.close('all')
        #     fig1 = plt.figure(figsize=(3,2), dpi=400)
        #     ax1 = plt.gca()
        #     
        #     ax1.tick_params(axis='x', which='both', direction='in')
        #     ax1.tick_params(axis='y', which='both', direction='in')
        #     #ax1.xaxis.set_ticks_position('both')
        #     #ax1.yaxis.set_ticks_position('both')
        #     ax1.set_xscale('log',base=10)
        #     #ax1.set_yscale('log',base=10)
        #     
        #     #ax1.set_xlim(100,3000)
        #     #ax1.xaxis.set_major_locator(mpl.ticker.LogLocator(subs=(1,)))
        #     #ax1.xaxis.set_minor_locator(mpl.ticker.LogLocator(subs=np.linspace(1,9,9)))
        #     #ax1.xaxis.set_minor_formatter(mpl.ticker.NullFormatter())
        #     
        #     ax1.plot(
        #     y_plus_,
        #     r_uII_vII_plus_,
        #     c='k',
        #     zorder=19,
        #     lw=0.8,
        #     marker='o',
        #     ms=1.5,
        #     ls='none',
        #     )
        #     
        #     y_plus_dummy_          = np.logspace(np.log10(1),np.log10(1000),1000)
        #     r_uII_vII_plus_spline_ = func_tauIxy(y_plus_dummy_)
        #     
        #     ax1.plot(
        #     y_plus_dummy_,
        #     r_uII_vII_plus_spline_,
        #     c='blue',
        #     zorder=19,
        #     lw=0.8,
        #     #marker='o',
        #     #ms=1.5,
        #     #ls='none',
        #     )
        #     
        #     ax1.axvline(x=y_plus_pk_       , linestyle='solid', c='gray', zorder=1, lw=0.5)
        #     ax1.axhline(y=func_tauIxy(y_plus_pk_) , linestyle='solid', c='gray', zorder=1, lw=0.5)
        #     
        #     plt.show()
        
        # === τ′yy
        
        i_naive = np.argmax( r_vII_vII_plus_ )
        #tau_yy_I_peak_naive_ = r_vII_vII_plus_[i_naive]
        
        func_tauIyy = CubicSpline( y_plus_ , r_vII_vII_plus_ , bc_type='natural', extrapolate=False )
        
        bounds_ = ( max(y_plus_[i_naive]*0.9,y_plus_.min()) , min(y_plus_[i_naive]*1.1,y_plus_.max()) )
        
        sol = least_squares(
                fun=__opt_find_peak,
                args=(func_tauIyy,),
                x0=y_plus_[i_naive],
                xtol=1e-15,
                ftol=1e-15,
                gtol=1e-15,
                method='dogbox',
                bounds=bounds_,
                )
        if not sol.success:
            raise ValueError
        
        y_plus_pk_ = float(sol.x[0])
        tau_yy_I_peak[i]   = func_tauIyy(y_plus_pk_) * tau_wall[i] ## re-dimensionalizing
        tau_yy_I_peak_y[i] = y_plus_pk_              * sc_l_in[i]  ## re-dimensionalizing
        
        # ===
        
        # ## debug plot for τ′yy
        # #if (i==5000) or (i==10000) or (i==15000):
        # if 0:
        #     
        #     plt.close('all')
        #     fig1 = plt.figure(figsize=(3,2), dpi=400)
        #     ax1 = plt.gca()
        #     
        #     ax1.tick_params(axis='x', which='both', direction='in')
        #     ax1.tick_params(axis='y', which='both', direction='in')
        #     #ax1.xaxis.set_ticks_position('both')
        #     #ax1.yaxis.set_ticks_position('both')
        #     ax1.set_xscale('log',base=10)
        #     #ax1.set_yscale('log',base=10)
        #     
        #     #ax1.set_xlim(100,3000)
        #     #ax1.xaxis.set_major_locator(mpl.ticker.LogLocator(subs=(1,)))
        #     #ax1.xaxis.set_minor_locator(mpl.ticker.LogLocator(subs=np.linspace(1,9,9)))
        #     #ax1.xaxis.set_minor_formatter(mpl.ticker.NullFormatter())
        #     
        #     ax1.plot(
        #     y_plus_,
        #     r_vII_vII_plus_,
        #     c='k',
        #     zorder=19,
        #     lw=0.8,
        #     marker='o',
        #     ms=1.5,
        #     ls='none',
        #     )
        #     
        #     y_plus_dummy_          = np.logspace(np.log10(1),np.log10(1000),1000)
        #     r_vII_vII_plus_spline_ = func_tauIyy(y_plus_dummy_)
        #     
        #     ax1.plot(
        #     y_plus_dummy_,
        #     r_vII_vII_plus_spline_,
        #     c='blue',
        #     zorder=19,
        #     lw=0.8,
        #     #marker='o',
        #     #ms=1.5,
        #     #ls='none',
        #     )
        #     
        #     ax1.axvline(x=y_plus_pk_              , linestyle='solid', c='gray', zorder=1, lw=0.5)
        #     ax1.axhline(y=func_tauIyy(y_plus_pk_) , linestyle='solid', c='gray', zorder=1, lw=0.5)
        #     
        #     plt.show()
        
        # ===
        
        progress_bar.update()
    progress_bar.close()
    
    
    if ('data_1Dx/tau_xx_I_peak' in self): del self['data_1Dx/tau_xx_I_peak']
    self.create_dataset('data_1Dx/tau_xx_I_peak', data=tau_xx_I_peak, chunks=None)
    if verbose: even_print('data_1Dx/tau_xx_I_peak','%s'%str(tau_xx_I_peak.shape))
    
    if ('data_1Dx/tau_xy_I_peak' in self): del self['data_1Dx/tau_xy_I_peak']
    self.create_dataset('data_1Dx/tau_xy_I_peak', data=tau_xy_I_peak, chunks=None)
    if verbose: even_print('data_1Dx/tau_xy_I_peak','%s'%str(tau_xy_I_peak.shape))
    
    if ('data_1Dx/tau_yy_I_peak' in self): del self['data_1Dx/tau_yy_I_peak']
    self.create_dataset('data_1Dx/tau_yy_I_peak', data=tau_yy_I_peak, chunks=None)
    if verbose: even_print('data_1Dx/tau_yy_I_peak','%s'%str(tau_yy_I_peak.shape))
    
    # ## old
    # if ('data_1Dx/tau_xx_I_peak_y_plus' in self):
    #     del self['data_1Dx/tau_xx_I_peak_y_plus']
    # if ('data_1Dx/tau_xy_I_peak_y_plus' in self):
    #     del self['data_1Dx/tau_xy_I_peak_y_plus']
    # if ('data_1Dx/tau_yy_I_peak_y_plus' in self):
    #     del self['data_1Dx/tau_yy_I_peak_y_plus']
    
    if ('data_1Dx/tau_xx_I_peak_y' in self): del self['data_1Dx/tau_xx_I_peak_y']
    self.create_dataset('data_1Dx/tau_xx_I_peak_y', data=tau_xx_I_peak_y, chunks=None)
    if verbose: even_print('data_1Dx/tau_xx_I_peak_y','%s'%str(tau_xx_I_peak_y.shape))
    
    if ('data_1Dx/tau_xy_I_peak_y' in self): del self['data_1Dx/tau_xy_I_peak_y']
    self.create_dataset('data_1Dx/tau_xy_I_peak_y', data=tau_xy_I_peak_y, chunks=None)
    if verbose: even_print('data_1Dx/tau_xy_I_peak_y','%s'%str(tau_xy_I_peak_y.shape))
    
    if ('data_1Dx/tau_yy_I_peak_y' in self): del self['data_1Dx/tau_yy_I_peak_y']
    self.create_dataset('data_1Dx/tau_yy_I_peak_y', data=tau_yy_I_peak_y, chunks=None)
    if verbose: even_print('data_1Dx/tau_yy_I_peak_y','%s'%str(tau_yy_I_peak_y.shape))
    
    
    self.get_header(verbose=False)
    if verbose: print(72*'-')
    if verbose: print('total time : ztmd.calc_peak_tauI() : %s'%format_time_string((timeit.default_timer() - t_start_func)))
    if verbose: print(72*'-')
    return
