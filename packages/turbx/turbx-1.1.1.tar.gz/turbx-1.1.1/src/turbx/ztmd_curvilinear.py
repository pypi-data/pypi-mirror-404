import os
import pickle
import timeit

import numpy as np

from .utils import even_print, format_time_string

'''
========================================================================
ZTMD functions unique to curved-grid cases
========================================================================
'''

# ======================================================================

def _calc_s_wall(self,**kwargs):
    '''
    calculate wall/top path length 's' (numerically integrated, not continuous!)
    '''
    
    verbose = kwargs.get('verbose',True)
    
    if verbose: print('\n'+'ztmd.calc_s_wall()'+'\n'+72*'-')
    t_start_func = timeit.default_timer()
    
    if self.rectilinear:
        
        s_wall = np.copy( self.x - self.x.min() )
        s_top  = np.copy( self.x - self.x.min() )
    
    else: ## curvilinear
        
        ds_wall = np.sqrt( np.diff(self.x[:,0])**2 + np.diff(self.y[:,0])**2 )
        s_wall  = np.cumsum(np.concatenate([[0.],ds_wall]))
        
        ds_top = np.sqrt( np.diff(self.x[:,-1])**2 + np.diff(self.y[:,-1])**2 )
        s_top  = np.cumsum(np.concatenate([[0.],ds_top]))
    
    if verbose: even_print( 's_wall/lchar max' , '%0.8f'%(s_wall.max()/self.lchar) )
    if verbose: even_print( 's_top/lchar max'  , '%0.8f'%(s_top.max()/self.lchar)  )
    
    if ('dims/s_wall' in self):
        del self['dims/s_wall']
    dset = self.create_dataset('dims/s_wall', data=s_wall, chunks=None)
    if verbose: even_print( 'dims/s_wall', str(dset.shape) )
    
    if ('dims/s_top' in self):
        del self['dims/s_top']
    dset = self.create_dataset('dims/s_top', data=s_top, chunks=None)
    if verbose: even_print( 'dims/s_top', str(dset.shape) )
    
    self.get_header(verbose=False)
    if verbose: print(72*'-')
    if verbose: print('total time : ztmd.calc_s_wall() : %s'%format_time_string((timeit.default_timer() - t_start_func)))
    if verbose: print(72*'-')
    
    return

def _add_geom_data(self, fn_dat=None, **kwargs):
    '''
    add geom data (from pickled .dat, usually from tgg)
    - dims/stang : (nx,)
    - dims/snorm : (ny,)
    - dims/crv_R : (nx,)
    '''
    
    verbose = kwargs.get('verbose',True)
    
    if verbose: print('\n'+'ztmd.add_geom_data()'+'\n'+72*'-')
    t_start_func = timeit.default_timer()
    
    if not os.path.isfile(fn_dat):
        raise FileNotFoundError('file does not exist: %s'%str(fn_dat))
    
    ## open data file from tgg
    with open(fn_dat,'rb') as f:
        dd = pickle.load(f)
    
    if ('xy2d' not in dd.keys()):
        raise ValueError(f'file {fn_dat} does not contain xy2d')
    
    ## check if consistent with [xy] grid in ref file
    xy2d = np.copy( dd['xy2d'] )
    
    if (self.x.ndim==2) and (self.y.ndim==2):
        np.testing.assert_allclose(xy2d[:,:,0], self.x/self.lchar, rtol=1e-14, atol=1e-14)
        np.testing.assert_allclose(xy2d[:,:,1], self.y/self.lchar, rtol=1e-14, atol=1e-14)
    elif (self.x.ndim==1) and (self.y.ndim==1):
        np.testing.assert_allclose(xy2d[:,0,0], self.x/self.lchar, rtol=1e-14, atol=1e-14)
        np.testing.assert_allclose(xy2d[0,:,1], self.y/self.lchar, rtol=1e-14, atol=1e-14)
    else:
        raise ValueError
    
    if verbose: even_print('check passed', 'x grid')
    if verbose: even_print('check passed', 'y grid')
    
    ## key names for 'dims' group
    kn_dims = ['stang', 'snorm', 'crv_R'] 
    for k in kn_dims:
        if (k in dd.keys()):
            dsn = f'dims/{k}'
            if (dd[k] is None):
                continue
            data = np.copy(dd[k])
            data *= self.lchar ## re-dimensionalize (ztmd is dimensional)
            if (dsn in self): del self[dsn]
            ds = self.create_dataset(dsn, data=data, chunks=None)
            if verbose: even_print(dsn,'%s'%str(ds.shape))
    
    kn_dims = ['z', 's', 's_top', 's_wall', 'R_min', 'path_len', 'W', 'H'] 
    for k in kn_dims:
        if (k in dd.keys()):
            dsn = f'dims/{k}'
            if (dd[k] is None):
                continue
            if isinstance(dd[k], np.ndarray):
                data = np.copy(dd[k])
                data *= self.lchar ## re-dimensionalize (ztmd is dimensional)
            if isinstance(dd[k], (int,float)):
                data = float(dd[k])
                data *= self.lchar ## re-dimensionalize (ztmd is dimensional)
            if (dsn in self): del self[dsn]
            ds = self.create_dataset(dsn, data=data, chunks=None)
            if verbose: even_print(dsn,'%s'%str(ds.shape))
    
    kn_dims = ['curve_arc_angle']
    for k in kn_dims:
        if (k in dd.keys()):
            dsn = f'dims/{k}'
            if (dd[k] is None):
                continue
            if (dsn in self): del self[dsn]
            ds = self.create_dataset(dsn, data=dd[k], chunks=None)
            if verbose: even_print(dsn,'%s'%str(ds.shape))
    
    ## check
    if self.rectilinear:
        
        stang_ = self['dims/stang'][()]
        x_ = self['dims/x'][()]
        np.testing.assert_allclose(stang_, x_-x_.min(), rtol=1e-14, atol=1e-14)
        
        snorm_ = self['dims/snorm'][()]
        y_ = self['dims/y'][()]
        np.testing.assert_allclose(snorm_, y_-y_.min(), rtol=1e-14, atol=1e-14)
    
    self.get_header(verbose=False)
    if verbose: print(72*'-')
    if verbose: print('total time : ztmd.add_geom_data() : %s'%format_time_string((timeit.default_timer() - t_start_func)))
    if verbose: print(72*'-')
    
    return

def _add_csys_vecs_xy(self, fn_dat=None, **kwargs):
    '''
    add csys data (from pickled .dat, usually from tgg)
    - csys/vtang : (nx,ny,2)
    - csys/vnorm : (nx,ny,2)
    '''
    
    verbose = kwargs.get('verbose',True)
    
    if verbose: print('\n'+'ztmd.add_csys_vecs_xy()'+'\n'+72*'-')
    t_start_func = timeit.default_timer()
    
    if not os.path.isfile(fn_dat):
        raise FileNotFoundError('file does not exist: %s'%str(fn_dat))
    
    ## open data file from tgg
    with open(fn_dat,'rb') as f:
        dd = pickle.load(f)
    
    if ('xy2d' not in dd.keys()):
        raise ValueError(f'file {fn_dat} does not contain xy2d')
    if ('vtang' not in dd.keys()):
        raise ValueError(f'file {fn_dat} does not contain vtang')
    if ('vnorm' not in dd.keys()):
        raise ValueError(f'file {fn_dat} does not contain vnorm')
    
    xy2d  = dd['xy2d']
    vtang = dd['vtang']
    vnorm = dd['vnorm']
    
    #wall_distance = dd['wall_distance']
    #s_wall_2d     = dd['s_wall_2d'] ## curve path length of point on wall (nx,ny)
    #p_wall_2d     = dd['p_wall_2d'] ## projection point on wall (nx,ny,2)
    
    if (self.x.ndim==2) and (self.y.ndim==2):
        np.testing.assert_allclose(xy2d[:,:,0], self.x/self.lchar, rtol=1e-14, atol=1e-14)
        np.testing.assert_allclose(xy2d[:,:,1], self.y/self.lchar, rtol=1e-14, atol=1e-14)
    elif (self.x.ndim==1) and (self.y.ndim==1):
        np.testing.assert_allclose(xy2d[:,0,0], self.x/self.lchar, rtol=1e-14, atol=1e-14)
        np.testing.assert_allclose(xy2d[0,:,1], self.y/self.lchar, rtol=1e-14, atol=1e-14)
    else:
        raise ValueError
    
    if verbose: even_print('check passed', 'x grid')
    if verbose: even_print('check passed', 'y grid')
    
    dd = None; del dd
    xy2d = None; del xy2d
    
    ## re-dimensionalize
    #wall_distance *= self.lchar
    
    #if not (wall_distance.shape == (self.nx,self.ny)):
    #    raise ValueError('wall_distance.shape != (self.nx,self.ny)')
    if not (vtang.shape == (self.nx,self.ny,2)):
        raise ValueError('vtang.shape != (self.nx,self.ny,2)')
    if not (vnorm.shape == (self.nx,self.ny,2)):
        raise ValueError('vnorm.shape != (self.nx,self.ny,2)')
    
    ## write wall distance scalar (nx,ny)
    #if ('data/wall_distance' in self): del self['data/wall_distance']
    #self.create_dataset('data/wall_distance', data=wall_distance.T, chunks=None)
    
    ## write wall normal / tangent basis vectors
    if ('csys/vtang' in self): del self['csys/vtang']
    dset = self.create_dataset('csys/vtang', data=vtang, chunks=None)
    if verbose: even_print('csys/vtang',str(dset.shape))
    
    if ('csys/vnorm' in self): del self['csys/vnorm']
    dset = self.create_dataset('csys/vnorm', data=vnorm, chunks=None)
    if verbose: even_print('csys/vnorm',str(dset.shape))
    
    ## write continuous wall point coordinate & wall path length
    #if ('csys/s_wall_2d' in self): del self['csys/s_wall_2d']
    #self.create_dataset('csys/s_wall_2d', data=s_wall_2d, chunks=None)
    #if ('csys/p_wall_2d' in self): del self['csys/p_wall_2d']
    #self.create_dataset('csys/p_wall_2d', data=p_wall_2d, chunks=None)
    
    ## check
    if self.rectilinear:
        
        vtang_        = np.zeros((self.nx,self.ny,2),dtype=np.float64)
        vtang_[:,:,:] = np.array([1,0],dtype=np.float64)
        np.testing.assert_allclose(vtang_, vtang, rtol=1e-14, atol=1e-14)
        
        vnorm_        = np.zeros((self.nx,self.ny,2),dtype=np.float64)
        vnorm_[:,:,:] = np.array([0,1],dtype=np.float64)
        np.testing.assert_allclose(vnorm_, vnorm, rtol=1e-14, atol=1e-14)
    
    self.get_header(verbose=False)
    if verbose: print(72*'-')
    if verbose: print('total time : ztmd.add_csys_vecs_xy() : %s'%format_time_string((timeit.default_timer() - t_start_func)))
    if verbose: print(72*'-')
    
    return

def _calc_vel_tangnorm(self, **kwargs):
    '''
    add tangent & normal velocity [utang,unorm] to file
    '''
    
    verbose = kwargs.get('verbose',True)
    
    if verbose: print('\n'+'ztmd.calc_vel_tangnorm()'+'\n'+72*'-')
    t_start_func = timeit.default_timer()
    
    if 'data/u' not in self:
        raise ValueError('data/u not in hdf5')
    if 'data/v' not in self:
        raise ValueError('data/v not in hdf5')
    if 'csys/vtang' not in self:
        raise ValueError('csys/vtang not in hdf5')
    if 'csys/vnorm' not in self:
        raise ValueError('csys/vnorm not in hdf5')
    if not (self.open_mode=='a') or (self.open_mode=='w'):
        raise ValueError('not able to write to hdf5 file')
    
    ## read unit vectors (wall tangent, wall norm) from HDF5
    vtang = np.copy( self['csys/vtang'][()] )
    vnorm = np.copy( self['csys/vnorm'][()] )
    
    # === Reynolds
    
    if ('data/u' in self) and ('data/v' in self):
        
        ## read 2D velocities
        u  = np.copy( self['data/u'][()].T )
        v  = np.copy( self['data/v'][()].T )
        uv = np.stack((u,v), axis=-1)
        
        umag1 = np.copy( np.sqrt( u**2 + v**2 ) )
        
        ## inner product of velocity vector and basis vector (csys transform)
        utang = np.einsum('xyi,xyi->xy', vtang, uv)
        unorm = np.einsum('xyi,xyi->xy', vnorm, uv)
        
        umag2 = np.copy( np.sqrt( utang**2 + unorm**2 ) )
        
        if (umag1.dtype==np.dtype(np.float32)):
            np.testing.assert_allclose(umag1, umag2, rtol=1e-6) ## single precision
        elif (umag2.dtype==np.dtype(np.float64)):
            np.testing.assert_allclose(umag1, umag2, rtol=1e-12) ## double precision
        else:
            raise ValueError
        
        # if self.get('data/u').attrs['dimensional']:
        #     raise AssertionError('u is dimensional')
        # if self.get('data/v').attrs['dimensional']:
        #     raise AssertionError('v is dimensional')
        
        if ('data/utang' in self): del self['data/utang']
        self.create_dataset('data/utang', data=utang.T, chunks=None)
        #dset.attrs['dimensional'] = False
        if verbose: even_print('utang','%s'%str(utang.shape))
        
        if ('data/unorm' in self): del self['data/unorm']
        self.create_dataset('data/unorm', data=unorm.T, chunks=None)
        #dset.attrs['dimensional'] = False
        if verbose: even_print('unorm','%s'%str(unorm.shape))
        
        ## assert that in rectilinear case that u==utang & v==unorm
        if self.rectilinear:
            np.testing.assert_allclose(u, utang, rtol=1e-14, atol=1e-14)
            np.testing.assert_allclose(v, unorm, rtol=1e-14, atol=1e-14)
    
    # === Favre
    
    if ('data/u_Fv' in self) and ('data/v_Fv' in self):
        
        ## read 2D velocities
        u_Fv     = np.copy( self['data/u_Fv'][()].T )
        v_Fv     = np.copy( self['data/v_Fv'][()].T )
        uv_Fv    = np.stack((u_Fv,v_Fv), axis=-1)
        umag1_Fv = np.copy( np.sqrt( u_Fv**2 + v_Fv**2 ) )
        
        ## inner product of velocity vector and basis vector (csys transform)
        utang_Fv = np.einsum('xyi,xyi->xy', vtang, uv_Fv)
        unorm_Fv = np.einsum('xyi,xyi->xy', vnorm, uv_Fv)
        
        umag2_Fv = np.copy( np.sqrt( utang_Fv**2 + unorm_Fv**2 ) )
        
        if (umag1_Fv.dtype==np.dtype(np.float32)):
            np.testing.assert_allclose(umag1_Fv, umag2_Fv, rtol=1e-6) ## single precision
        elif (umag2_Fv.dtype==np.dtype(np.float64)):
            np.testing.assert_allclose(umag1_Fv, umag2_Fv, rtol=1e-12) ## double precision
        else:
            raise ValueError
        
        if ('data/utang_Fv' in self): del self['data/utang_Fv']
        self.create_dataset('data/utang_Fv', data=utang_Fv.T, chunks=None)
        if verbose: even_print('utang_Fv','%s'%str(utang_Fv.shape))
        
        if ('data/unorm_Fv' in self): del self['data/unorm_Fv']
        self.create_dataset('data/unorm_Fv', data=unorm_Fv.T, chunks=None)
        if verbose: even_print('unorm_Fv','%s'%str(unorm_Fv.shape))
        
        ## assert that in rectilinear case that u==utang & v==unorm
        if self.rectilinear:
            np.testing.assert_allclose(u_Fv, utang_Fv, rtol=1e-14, atol=1e-14)
            np.testing.assert_allclose(v_Fv, unorm_Fv, rtol=1e-14, atol=1e-14)
    
    self.get_header(verbose=False)
    if verbose: print(72*'-')
    if verbose: print('total time : ztmd.calc_vel_tangnorm() : %s'%format_time_string((timeit.default_timer() - t_start_func)))
    if verbose: print(72*'-')
    
    return

def _calc_vel_tangnorm_mean_removed(self, **kwargs):
    '''
    calculate utangI_utangI, unormI_unormI
    '''
    
    verbose = kwargs.get('verbose',True)
    
    if verbose: print('\n'+'ztmd.calc_vel_tangnorm_mean_removed()'+'\n'+72*'-')
    t_start_func = timeit.default_timer()
    
    #if not ('data/wall_distance' in self):
    #    raise ValueError('data/wall_distance not in hdf5')
    if 'dims/snorm' not in self:
        raise ValueError('dims/snorm not in hdf5')
    if 'data/uI_uI' not in self:
        raise ValueError('data/uI_uI not in hdf5')
    if 'data/vI_vI' not in self:
        raise ValueError('data/vI_vI not in hdf5')
    if 'csys/vtang' not in self:
        raise ValueError('csys/vtang not in hdf5')
    if 'csys/vnorm' not in self:
        raise ValueError('csys/vnorm not in hdf5')
    if not (self.open_mode=='a') or (self.open_mode=='w'):
        raise ValueError('not able to write to hdf5 file')
    
    ## read unit vectors (wall tangent, wall norm) from HDF5
    vtang = np.copy( self['csys/vtang'][()] )
    vnorm = np.copy( self['csys/vnorm'][()] )
    trafo = np.stack((vtang,vnorm),axis=-1)
    
    ## transpose [2,2] matrix at every [x,y]
    #trafoT = np.transpose(trafo,(0,1,3,2))
    
    # === Reynolds
    
    if ('data/uI_uI' in self) and ('data/uI_vI' in self) and ('data/vI_vI' in self):
        
        uI_uI = np.copy( self['data/uI_uI'][()].T )
        vI_vI = np.copy( self['data/vI_vI'][()].T )
        uI_vI = np.copy( self['data/uI_vI'][()].T )
        vI_uI = np.copy( uI_vI )
        
        ## construct 2D tensor --> (nx,ny,2,2)
        uIuI_ij = np.stack( (np.stack( [uI_uI, uI_vI], axis=-1 ),
                             np.stack( [vI_uI, vI_vI], axis=-1 )), axis=-1 )
        
        #uIuI_ij = np.transpose(uIuI_ij, (0,1,3,2))
        
        uI_uI_rms = np.copy( self['data/uI_uI_rms'][()].T )
        vI_vI_rms = np.copy( self['data/vI_vI_rms'][()].T )
        uI_vI_rms = np.copy( self['data/uI_vI_rms'][()].T )
        vI_uI_rms = np.copy( uI_vI_rms )
        
        ## construct 2D tensor --> (nx,ny,2,2)
        uIuI_rms_ij = np.stack( (np.stack( [uI_uI_rms, uI_vI_rms], axis=-1 ),
                                 np.stack( [vI_uI_rms, vI_vI_rms], axis=-1 )), axis=-1 )
        
        #uIuI_rms_ij = np.transpose(uIuI_rms_ij, (0,1,3,2))
        
        ## check
        np.testing.assert_allclose(uI_uI, uI_uI_rms**2, rtol=1e-6, atol=1e-6)
        np.testing.assert_allclose(vI_vI, vI_vI_rms**2, rtol=1e-6, atol=1e-6)
        
        ## these three ops are the same
        #uIuI_ij_tn_A = np.einsum('xyij,xyjk,xykl->xyil', trafoT, uIuI_ij, trafo)
        #uIuI_ij_tn_B = np.einsum('xyji,xyjk,xykl->xyil', trafo,  uIuI_ij, trafo)
        #uIuI_ij_tn_C = np.matmul(np.matmul(trafoT, uIuI_ij), trafo)
        #np.testing.assert_allclose(uIuI_ij_tn_A, uIuI_ij_tn_B, atol=1e-14, rtol=1e-14)
        #np.testing.assert_allclose(uIuI_ij_tn_B, uIuI_ij_tn_C, atol=1e-14, rtol=1e-14)
        
        uIuI_ij_tn     = np.einsum('xyji,xyjk,xykl->xyil', trafo, uIuI_ij,     trafo)
        uIuI_rms_ij_tn = np.einsum('xyji,xyjk,xykl->xyil', trafo, uIuI_rms_ij, trafo)
        
        utI_utI = np.copy(uIuI_ij_tn[:,:,0,0])
        unI_unI = np.copy(uIuI_ij_tn[:,:,1,1])
        utI_unI = np.copy(uIuI_ij_tn[:,:,0,1])
        unI_utI = np.copy(uIuI_ij_tn[:,:,1,0])
        
        np.testing.assert_allclose( utI_unI, unI_utI, rtol=1e-14, atol=1e-14 )
        
        #utI_utI_rms = np.copy(uIuI_rms_ij_tn[:,:,0,0])
        #unI_unI_rms = np.copy(uIuI_rms_ij_tn[:,:,1,1])
        utI_unI_rms = np.copy(uIuI_rms_ij_tn[:,:,0,1])
        unI_utI_rms = np.copy(uIuI_rms_ij_tn[:,:,1,0])
        
        np.testing.assert_allclose( utI_unI_rms, unI_utI_rms, rtol=1e-14, atol=1e-14 )
        
        ## fails
        #np.testing.assert_allclose( utI_utI, utI_utI_rms**2, rtol=1e-6, atol=1e-6 )
        #np.testing.assert_allclose( unI_unI, unI_unI_rms**2, rtol=1e-6, atol=1e-6 )
        
        ## only write full covariances, not RMSes
        
        if ('data/utI_utI' in self): del self['data/utI_utI']
        self.create_dataset('data/utI_utI', data=utI_utI.T, chunks=None)
        if verbose: even_print('utI_utI','%s'%str(utI_utI.shape))
        
        if ('data/unI_unI' in self): del self['data/unI_unI']
        self.create_dataset('data/unI_unI', data=unI_unI.T, chunks=None)
        if verbose: even_print('unI_unI','%s'%str(unI_unI.shape))
        
        if ('data/utI_unI' in self): del self['data/utI_unI']
        self.create_dataset('data/utI_unI', data=utI_unI.T, chunks=None)
        if verbose: even_print('utI_unI','%s'%str(utI_unI.shape))
        
        ## check
        if self.rectilinear:
            np.testing.assert_allclose(utI_utI, uI_uI, rtol=1e-14, atol=1e-14)
            np.testing.assert_allclose(unI_unI, vI_vI, rtol=1e-14, atol=1e-14)
            np.testing.assert_allclose(utI_unI, uI_vI, rtol=1e-14, atol=1e-14)
    
    # === Favre
    
    if ('data/r_uII_uII' in self) and ('data/r_uII_vII' in self) and ('data/r_vII_vII' in self):
        
        r_uII_uII = np.copy( self['data/r_uII_uII'][()].T )
        r_vII_vII = np.copy( self['data/r_vII_vII'][()].T )
        r_uII_vII = np.copy( self['data/r_uII_vII'][()].T )
        r_vII_uII = np.copy( r_uII_vII )
        
        ## construct 2D tensor --> (nx,ny,2,2)
        r_uIIuII_ij = np.stack( (np.stack( [r_uII_uII, r_uII_vII], axis=-1 ),
                                 np.stack( [r_vII_uII, r_vII_vII], axis=-1 )), axis=-1 )
        
        r_uII_uII_rms = np.copy( self['data/r_uII_uII_rms'][()].T )
        r_vII_vII_rms = np.copy( self['data/r_vII_vII_rms'][()].T )
        #r_uII_vII_rms = np.copy( self['data/r_uII_vII_rms'][()].T )
        #r_vII_uII_rms = np.copy( r_uII_vII_rms )
        
        ## construct 2D tensor --> (nx,ny,2,2)
        #r_uIIuII_rms_ij = np.stack( (np.stack( [r_uII_uII_rms, r_uII_vII_rms], axis=-1 ),
        #                             np.stack( [r_vII_uII_rms, r_vII_vII_rms], axis=-1 )), axis=-1 )
        
        ## check
        np.testing.assert_allclose(r_uII_uII, r_uII_uII_rms**2, rtol=1e-6, atol=1e-6)
        np.testing.assert_allclose(r_vII_vII, r_vII_vII_rms**2, rtol=1e-6, atol=1e-6)
        
        r_uIIuII_ij_tn     = np.einsum('xyji,xyjk,xykl->xyil', trafo, r_uIIuII_ij,     trafo)
        #r_uIIuII_rms_ij_tn = np.einsum('xyji,xyjk,xykl->xyil', trafo, r_uIIuII_rms_ij, trafo)
        
        r_utII_utII = np.copy(r_uIIuII_ij_tn[:,:,0,0])
        r_unII_unII = np.copy(r_uIIuII_ij_tn[:,:,1,1])
        r_utII_unII = np.copy(r_uIIuII_ij_tn[:,:,0,1])
        r_unII_utII = np.copy(r_uIIuII_ij_tn[:,:,1,0])
        
        np.testing.assert_allclose( r_utII_unII, r_unII_utII, rtol=1e-14, atol=1e-14 )
        
        #r_utII_utII_rms = np.copy(uIuI_rms_ij_tn[:,:,0,0])
        #r_unII_unII_rms = np.copy(uIuI_rms_ij_tn[:,:,1,1])
        r_utII_unII_rms = np.copy(uIuI_rms_ij_tn[:,:,0,1])
        r_unII_utII_rms = np.copy(uIuI_rms_ij_tn[:,:,1,0])
        
        np.testing.assert_allclose( r_utII_unII_rms, r_unII_utII_rms, rtol=1e-14, atol=1e-14 )
        
        ## fails!
        #np.testing.assert_allclose( r_utII_utII, r_utII_utII_rms**2, rtol=1e-6, atol=1e-6 )
        #np.testing.assert_allclose( r_unII_unII, r_unII_unII_rms**2, rtol=1e-6, atol=1e-6 )
        
        ## only write full covariances, not RMSes
        
        if ('data/r_utII_utII' in self): del self['data/r_utII_utII']
        self.create_dataset('data/r_utII_utII', data=r_utII_utII.T, chunks=None)
        if verbose: even_print('r_utII_utII','%s'%str(r_utII_utII.shape))
        
        if ('data/r_unII_unII' in self): del self['data/r_unII_unII']
        self.create_dataset('data/r_unII_unII', data=r_unII_unII.T, chunks=None)
        if verbose: even_print('r_unII_unII','%s'%str(r_unII_unII.shape))
        
        if ('data/r_utII_unII' in self): del self['data/r_utII_unII']
        self.create_dataset('data/r_utII_unII', data=r_utII_unII.T, chunks=None)
        if verbose: even_print('r_utII_unII','%s'%str(r_utII_unII.shape))
        
        ## check
        if self.rectilinear:
            np.testing.assert_allclose(r_utII_utII, r_uII_uII, rtol=1e-14, atol=1e-14)
            np.testing.assert_allclose(r_unII_unII, r_vII_vII, rtol=1e-14, atol=1e-14)
            np.testing.assert_allclose(r_utII_unII, r_uII_vII, rtol=1e-14, atol=1e-14)
    
    self.get_header(verbose=False)
    if verbose: print(72*'-')
    if verbose: print('total time : ztmd.calc_vel_tangnorm_mean_removed() : %s'%format_time_string((timeit.default_timer() - t_start_func)))
    if verbose: print(72*'-')
    
    return
