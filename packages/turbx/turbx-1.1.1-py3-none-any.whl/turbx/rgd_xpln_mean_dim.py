import os
import timeit

import numpy as np
import scipy as sp

from .bl import calc_bl_integral_quantities_1d, calc_d99_1d, calc_profile_edge_1d
from .gradient import gradient
from .utils import even_print, format_time_string

# ======================================================================

def _add_mean_dimensional_data_xpln(self, **kwargs):
    '''
    Get dimensionalized mean data for [x] plane
    --> save to existing RGD file with fsubtype=mean
    - assumes volume which is thin in [x] direction
    - an RGD which is the output of rgd.get_mean() should be opened here
    - NOT parallel!!
    '''
    
    verbose      = kwargs.get('verbose',True)
    epsilon      = kwargs.get('epsilon',5e-5)
    acc          = kwargs.get('acc',6)
    edge_stencil = kwargs.get('edge_stencil','full')
    
    if (self.rank==0):
        verbose = True
    else:
        verbose = False
    
    if verbose: print('\n'+'rgd.add_mean_dimensional_data_xpln()'+'\n'+72*'-')
    t_start_func = timeit.default_timer()
    
    ## This func is not parallel!
    if self.usingmpi:
        raise NotImplementedError('rgd.add_mean_dimensional_data_xpln() is not a parallel function')
    
    ## 'r' and 'w' open modes are not allowed
    if not (self.open_mode=='a') or (self.open_mode=='r+'):
        raise ValueError(f'open mode is {self.open_mode}')
    
    ## Assert that this is a mean flow file ( i.e. output from rgd.get_mean() )
    if (self.fsubtype!='mean'):
        print(self.fsubtype)
        raise ValueError
    
    ## Get size of infile
    fsize = os.path.getsize(self.fname)/1024**3
    if verbose: even_print(os.path.basename(self.fname),'%0.1f [GB]'%fsize)
    if verbose: even_print('nx','%i'%self.nx)
    if verbose: even_print('ny','%i'%self.ny)
    if verbose: even_print('nz','%i'%self.nz)
    if verbose: even_print('nt','%i'%self.nt)
    if verbose: even_print('ngp','%0.1f [M]'%(self.ngp/1e6,))
    if verbose: print(72*'-')
    
    ## Read in 1D coordinate arrays, then dimensionalize [m]
    x = np.copy( self['dims/x'][()] * self.lchar )
    y = np.copy( self['dims/y'][()] * self.lchar )
    z = np.copy( self['dims/z'][()] * self.lchar )
    
    if (x.ndim!=1):
        raise ValueError
    if (y.ndim!=1):
        raise ValueError
    if (z.ndim!=1):
        raise ValueError
    
    ## Check if constant Δz (calculate Δz+ later)
    dz0 = np.diff(z)[0]
    if not np.all(np.isclose(np.diff(z), dz0, rtol=1e-7)):
        raise NotImplementedError
    
    ## Check if mean rgd has attr 'dt'
    if ('dt' in self.attrs.keys()):
        dt = self.attrs['dt']
        if (dt is not None):
            dt *= self.tchar
    else:
        raise ValueError
    
    if verbose: even_print('Δt/tchar','%0.8f'%(dt/self.tchar))
    if verbose: even_print('Δt','%0.3e [s]'%(dt,))
    if verbose: even_print('duration/tchar','%0.1f'%(self.duration_avg,))
    if verbose: even_print('duration','%0.3e [s]'%(self.duration_avg*self.tchar,))
    if verbose: print(72*'-')
    
    ## Re-dimensionalize
    u   =  np.copy( self.U_inf                     *  self['data/u'][()].T   )
    v   =  np.copy( self.U_inf                     *  self['data/v'][()].T   )
    w   =  np.copy( self.U_inf                     *  self['data/w'][()].T   )
    rho =  np.copy( self.rho_inf                   *  self['data/rho'][()].T )
    p   =  np.copy( (self.rho_inf * self.U_inf**2) *  self['data/p'][()].T   )
    T   =  np.copy( self.T_inf                     *  self['data/T'][()].T   )
    
    # mu1 = np.copy( self.C_Suth * T**(3/2) / (T + self.S_Suth) )
    # mu2 = np.copy( self.mu_Suth_ref * ( T / self.T_Suth_ref )**(3/2) * ((self.T_Suth_ref+self.S_Suth)/(T+self.S_Suth)) )
    # np.testing.assert_allclose(mu1, mu2, rtol=2e-7, atol=2e-7)
    # mu = np.copy(mu2)
    
    mu = np.copy( self.C_Suth * T**(3/2) / (T + self.S_Suth) )
    nu = np.copy( mu / rho )
    
    # === Average in [x,z] --> leave 1D [y]
    
    u   = np.squeeze( np.mean( u   , axis=(0,2), dtype=np.float64) )
    v   = np.squeeze( np.mean( v   , axis=(0,2), dtype=np.float64) )
    w   = np.squeeze( np.mean( w   , axis=(0,2), dtype=np.float64) )
    rho = np.squeeze( np.mean( rho , axis=(0,2), dtype=np.float64) )
    p   = np.squeeze( np.mean( p   , axis=(0,2), dtype=np.float64) )
    T   = np.squeeze( np.mean( T   , axis=(0,2), dtype=np.float64) )
    mu  = np.squeeze( np.mean( mu  , axis=(0,2), dtype=np.float64) )
    nu  = np.squeeze( np.mean( nu  , axis=(0,2), dtype=np.float64) )
    
    # ## determine finite difference order / size of central stencil based on [nx]
    # if (nx<3):
    #     raise ValueError('dx[] not possible because nx<3')
    # elif (nx>=3) and (nx<5):
    #     acc = 2
    # elif (nx>=5) and (nx<7):
    #     acc = 4
    # elif (nx>=7):
    #     acc = 6
    # else:
    #     raise ValueError('this should never happen')
    
    if verbose: even_print('acc','%i'%acc)
    if verbose: even_print('edge_stencil',edge_stencil)
    if verbose: print(72*'-')
    
    ## Get [y] gradients --> size [y]
    ddy_u   = gradient(u   , y, axis=0, acc=acc, edge_stencil=edge_stencil, d=1)
    ddy_v   = gradient(v   , y, axis=0, acc=acc, edge_stencil=edge_stencil, d=1)
    ddy_T   = gradient(T   , y, axis=0, acc=acc, edge_stencil=edge_stencil, d=1)
    ddy_p   = gradient(p   , y, axis=0, acc=acc, edge_stencil=edge_stencil, d=1)
    ddy_rho = gradient(rho , y, axis=0, acc=acc, edge_stencil=edge_stencil, d=1)
    
    ## Wall quantities
    ddy_u_wall  = float( ddy_u[0] )
    ddy_T_wall  = float( ddy_T[0] )
    rho_wall    = float( rho[0]   )
    nu_wall     = float( nu[0]    )
    mu_wall     = float( mu[0]    )
    T_wall      = float( T[0]     )
    tau_wall    = mu_wall * ddy_u_wall
    
    u_tau   = np.sqrt( tau_wall / rho_wall ) ## uτ
    sc_u_in = u_tau
    sc_l_in = nu_wall / u_tau     ## δν
    sc_t_in = nu_wall / u_tau**2  ## tν
    np.testing.assert_allclose(sc_t_in, sc_l_in/sc_u_in, rtol=1e-14, atol=1e-14)
    
    if verbose: even_print('ρw',f'{rho_wall:0.5f} [kg/m³]')
    if verbose: even_print('Tw',f'{T_wall:0.2f} [K]')
    if verbose: even_print('μw',f'{mu_wall:0.5E} [kg/(m·s)]')
    if verbose: even_print('νw',f'{nu_wall:0.5E} [m²/s]')
    if verbose: even_print('uτ',f'{u_tau:0.5E} [m/s]')
    if verbose: even_print('τw',f'{tau_wall:0.5E} [Pa]')
    if verbose: even_print('δν',f'{sc_l_in:0.5E} [m]')
    if verbose: even_print('tν',f'{sc_t_in:0.5E} [s]')
    if verbose: even_print('(du/dy)_w',f'{ddy_u_wall:0.3E} [1/s]')
    if verbose: even_print('(dT/dy)_w',f'{ddy_T_wall:0.3E} [K/m]')
    if verbose: print(72*'-')
    
    ddy_u_plus = np.copy( ddy_u / (u_tau/sc_l_in) ) ## du+/dy+ = (du/dy)/(uτ/δν) = (du/dy)/(uτ^2/νw)
    
    ## Get edge --> where |du+/dy+|<ϵ
    y_edge,j_edge = calc_profile_edge_1d(
                        y=y, ## dimensional
                        ddy_u=ddy_u_plus,
                        epsilon=epsilon,
                        )
    
    if verbose: even_print('ϵ',f'{epsilon:0.5E}')
    if verbose: even_print('j_edge',f'{j_edge:d}')
    if verbose: even_print('(du+/dy+)_edge',f'{ddy_u_plus[j_edge]:0.5E}')
    if verbose: even_print('y_edge',f'{y_edge:0.5E} [m]')
    if verbose: even_print('y+_edge',f'{y_edge/sc_l_in:0.3f}')
    
    aa = (y_edge-y.min())/(y.max()-y.min())
    if verbose: even_print('(y_edge-ymin)/(ymax-ymin)',f'{aa:0.3f}')
    
    # ===
    
    u_edge   =   u[j_edge]
    #v_edge   =   v[j_edge]
    #w_edge   =   w[j_edge]
    T_edge   =   T[j_edge]
    rho_edge = rho[j_edge]
    mu_edge  =  mu[j_edge]
    nu_edge  =  nu[j_edge]
    
    ## δ99
    d99 = calc_d99_1d(
            y=y,
            u=u,
            j_edge=j_edge,
            u_edge=u_edge,
            rtol=1e-3,
            interp_kind='cubic',
            )
    
    u99 = float( sp.interpolate.interp1d(y, u, kind='cubic', bounds_error=True)(d99) )
    
    ## Outer scales
    sc_l_out = d99
    sc_u_out = u99
    sc_t_out = d99/u99
    np.testing.assert_allclose(sc_t_out, sc_l_out/sc_u_out, rtol=1e-14, atol=1e-14)
    
    t_meas = self.duration_avg * (self.lchar / self.U_inf)
    t_eddy = t_meas / ( d99 / u_tau )
    
    ## Get BL integral quantities
    dd = calc_bl_integral_quantities_1d(
            y=y,
            u=u,
            rho=rho,
            d99=d99,
            u_tau=u_tau, rho_wall=rho_wall, mu_wall=mu_wall,
            u_edge=u_edge, rho_edge=rho_edge, mu_edge=mu_edge,
            j_edge=j_edge,
            )
    
    # === Add to file
    
    gn = 'data_dim'
    
    ## if group already exists in file, delete it entirely
    if (gn in self):
        del self[gn]
    
    ## 1D
    
    self.create_dataset(f'{gn}/u'     , data=u     , chunks=None)
    self.create_dataset(f'{gn}/rho'   , data=rho   , chunks=None)
    
    self.create_dataset(f'{gn}/ddy_u'   , data=ddy_u   , chunks=None)
    self.create_dataset(f'{gn}/ddy_v'   , data=ddy_v   , chunks=None)
    self.create_dataset(f'{gn}/ddy_T'   , data=ddy_T   , chunks=None)
    self.create_dataset(f'{gn}/ddy_p'   , data=ddy_p   , chunks=None)
    self.create_dataset(f'{gn}/ddy_rho' , data=ddy_rho , chunks=None)
    
    self.create_dataset(f'{gn}/z1d' , data=z , chunks=None)
    self.create_dataset(f'{gn}/z'   , data=z , chunks=None)
    
    ## 0D
    
    self.create_dataset(f'{gn}/dz0'        , data=dz0 , chunks=None)
    self.create_dataset(f'{gn}/dt'         , data=dt  , chunks=None)
    
    self.create_dataset(f'{gn}/y_edge'     , data=y_edge    , chunks=None)
    self.create_dataset(f'{gn}/d99'        , data=d99       , chunks=None)
    self.create_dataset(f'{gn}/u99'       , data=u99      , chunks=None)
    
    self.create_dataset(f'{gn}/u_edge'     , data=u_edge     , chunks=None)
    self.create_dataset(f'{gn}/rho_edge'   , data=rho_edge   , chunks=None)
    self.create_dataset(f'{gn}/mu_edge'    , data=mu_edge    , chunks=None)
    self.create_dataset(f'{gn}/nu_edge'    , data=nu_edge    , chunks=None)
    self.create_dataset(f'{gn}/T_edge'     , data=T_edge     , chunks=None)
    
    self.create_dataset(f'{gn}/u_tau'      , data=u_tau      , chunks=None)
    
    self.create_dataset(f'{gn}/ddy_u_wall' , data=ddy_u_wall , chunks=None )
    self.create_dataset(f'{gn}/ddy_T_wall' , data=ddy_T_wall , chunks=None )
    self.create_dataset(f'{gn}/rho_wall'   , data=rho_wall   , chunks=None )
    self.create_dataset(f'{gn}/nu_wall'    , data=nu_wall    , chunks=None )
    self.create_dataset(f'{gn}/mu_wall'    , data=mu_wall    , chunks=None )
    self.create_dataset(f'{gn}/T_wall'     , data=T_wall     , chunks=None )
    self.create_dataset(f'{gn}/tau_wall'   , data=tau_wall   , chunks=None )
    #self.create_dataset(f'{gn}/q_wall'     , data=q_wall     , chunks=None )
    
    self.create_dataset(f'{gn}/sc_u_in'    , data=sc_u_in    , chunks=None)
    self.create_dataset(f'{gn}/sc_l_in'    , data=sc_l_in    , chunks=None)
    self.create_dataset(f'{gn}/sc_t_in'    , data=sc_t_in    , chunks=None)
    self.create_dataset(f'{gn}/sc_u_out'   , data=sc_u_out   , chunks=None)
    self.create_dataset(f'{gn}/sc_l_out'   , data=sc_l_out   , chunks=None)
    self.create_dataset(f'{gn}/sc_t_out'   , data=sc_t_out   , chunks=None)
    
    ## Add integrated quantities (all 0D)
    for key,val in dd.items():
        self.create_dataset(f'{gn}/{key}', data=val, chunks=None)
    
    ## Report -- currently does not report everything returned
    if verbose:
        print(72*'-')
        even_print('Reτ'    , '%0.1f'%dd['Re_tau']      )
        even_print('Reθ'    , '%0.1f'%dd['Re_theta']    )
        even_print('Reδ*'   , '%0.1f'%dd['Re_dstar']    )
        even_print('Reδ2'   , '%0.1f'%dd['Re_d2']       )
        even_print('θ'      , '%0.5E [m]'%dd['theta']   )
        even_print('δ*'     , '%0.5E [m]'%dd['dstar']   )
        even_print('Δ'      , '%0.5E [m]'%dd['dRC']     )
        even_print('H12'    , '%0.5f'%dd['H12']         )
        even_print('H32'    , '%0.5f'%dd['H32']         )
        even_print('δ99'    , '%0.5E [m]'%d99           )
        even_print('θ/δ99'  , '%0.5f'%(dd['theta']/d99) )
        even_print('δ*/δ99' , '%0.5f'%(dd['dstar']/d99) )
        
        even_print('uτ'     , f'{u_tau:0.5E} [m/s]'        )
        even_print('νw'     , f'{nu_wall:0.5E} [m²/s]'     )
        even_print('μw'     , f'{mu_wall:0.5E} [kg/(m·s)]' )
        even_print('τw'     , f'{tau_wall:0.5E} [Pa]'      )
        
        even_print('τw/q_inf'                 , '%0.5E'%(tau_wall/(self.rho_inf*self.U_inf**2)) )
        even_print('cf = 2·τw/(ρe·ue²)'       , '%0.5E'%(2*tau_wall/(rho_edge*u_edge**2)) )
        even_print('t_meas'                   , '%0.5E [s]'%t_meas            )
        even_print('t_meas/tchar'             , '%0.1f'%(t_meas/self.tchar)   )
        even_print('t_eddy = t_meas/(δ99/uτ)' , '%0.2f'%t_eddy                )
        even_print('t_meas/(δ99/u99)'         , '%0.2f'%(t_meas/(d99/u99))    )
        even_print('t_meas/(20·δ99/u99)'      , '%0.2f'%(t_meas/(20*d99/u99)) )
        print(72*'-')
        even_print('uτ'           , '%0.5E [m/s]'%(sc_u_in,)  )
        even_print('δν = νw/uτ'   , '%0.5E [m]'%(sc_l_in,)    )
        even_print('tν = νw/uτ²'  , '%0.5E [s]'%(sc_t_in,)    )
        even_print('u99'          , '%0.5E [m/s]'%(sc_u_out,) )
        even_print('δ99'          , '%0.5E [m]'%(sc_l_out,)   )
        even_print('δ99/u99'      , '%0.5E [s]'%(sc_t_out,)   )
    
    if verbose: print(72*'-')
    if verbose: print('total time : rgd.add_mean_dimensional_data_xpln() : %s'%format_time_string((timeit.default_timer() - t_start_func)))
    if verbose: print(72*'-')
    return
