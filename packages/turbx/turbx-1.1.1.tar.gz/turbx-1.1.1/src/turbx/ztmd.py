import io
import os
import re
import shutil
import struct
import subprocess
import sys
import textwrap
import time
import timeit
import types
from pathlib import Path

import h5py
import numpy as np
from tqdm import tqdm

from .eas3 import eas3
from .eas4 import eas4
from .utils import even_print, format_time_string
from .ztmd_analysis import (
    _calc_bl_edge,
    _calc_bl_edge_quantities,
    _calc_bl_integral_quantities,
    _calc_d99,
    _calc_d99_quantities,
    _calc_gradients,
    _calc_peak_tauI,
    _calc_psvel,
    _calc_wake_parameter,
    _calc_wall_quantities,
)
from .ztmd_comp_trafo import (
    _calc_comp_trafo,
    _calc_VDII,
)
from .ztmd_curvilinear import (
    _add_csys_vecs_xy,
    _add_geom_data,
    _calc_s_wall,
    _calc_vel_tangnorm,
    _calc_vel_tangnorm_mean_removed,
)

# ======================================================================

class ztmd(h5py.File):
    '''
    Span (z) & temporal (t) mean data (md)
    -----
    - mean_flow_mpi.eas
    - favre_mean_flow_mpi.eas
    - ext_rms_fluctuation_mpi.eas
    - ext_favre_fluctuation_mpi.eas
    - turbulent_budget_mpi.eas
    -----
    '''
    
    def __init__(self, *args, **kwargs):
        
        self.fname, self.open_mode = args
        
        self.fname_path = os.path.dirname(self.fname)
        self.fname_base = os.path.basename(self.fname)
        self.fname_root, self.fname_ext = os.path.splitext(self.fname_base)
        
        ## default to libver='latest' if none provided
        if ('libver' not in kwargs):
            kwargs['libver'] = 'latest'
        
        ## catch possible user error --> could prevent accidental EAS overwrites
        if (self.fname_ext=='.eas'):
            raise ValueError('EAS4 files should not be opened with turbx.ztmd()')
        
        ## mpio driver for ZTMD currently not supported
        if ('driver' in kwargs) and (kwargs['driver']=='mpio'):
            raise ValueError('ZTMD class is currently not set up to be used with MPI')
        
        ## determine if using mpi
        if ('driver' in kwargs) and (kwargs['driver']=='mpio'):
            self.usingmpi = True
        else:
            self.usingmpi = False
        
        ## determine communicator & rank info
        if self.usingmpi:
            self.comm    = kwargs['comm']
            self.n_ranks = self.comm.Get_size()
            self.rank    = self.comm.Get_rank()
        else:
            self.comm    = None
            self.n_ranks = 1
            self.rank    = 0
        
        ## ztmd() unique kwargs (not h5py.File kwargs) --> pop() rather than get()
        stripe_count   = kwargs.pop('stripe_count'   , 16    )
        stripe_size_mb = kwargs.pop('stripe_size_mb' , 8     )
        perms          = kwargs.pop('perms'          , '640' )
        
        if not isinstance(stripe_count, int):
            raise ValueError
        if not isinstance(stripe_size_mb, int):
            raise ValueError
        if not isinstance(perms, str):
            raise ValueError
        if not len(perms)==3:
            raise ValueError
        if not re.fullmatch(r'\d{3}',perms):
            raise ValueError
        
        ## if not using MPI, remove 'driver' and 'comm' from kwargs
        if ( not self.usingmpi ) and ('driver' in kwargs):
            kwargs.pop('driver')
        if ( not self.usingmpi ) and ('comm' in kwargs):
            kwargs.pop('comm')
        
        ## ztmd() unique kwargs (not h5py.File kwargs) --> pop() rather than get()
        verbose = kwargs.pop( 'verbose' , False )
        force   = kwargs.pop( 'force'   , False )
        
        if not isinstance(verbose, bool):
            raise ValueError
        if not isinstance(force, bool):
            raise ValueError
        
        # === initialize file on FS
        
        ## if file open mode is 'w', the file exists, and force is False
        ## --> raise error
        if (self.open_mode == 'w') and (force is False) and os.path.isfile(self.fname):
            if (self.rank==0):
                print('\n'+72*'-')
                print(self.fname+' already exists! opening with \'w\' would overwrite.\n')
                openModeInfoStr = '''
                                  r       --> Read only, file must exist
                                  r+      --> Read/write, file must exist
                                  w       --> Create file, truncate if exists
                                  w- or x --> Create file, fail if exists
                                  a       --> Read/write if exists, create otherwise
                                  
                                  or use force=True arg:
                                  
                                  >>> with ztmd(<<fname>>,'w',force=True) as f:
                                  >>>     ...
                                  '''
                print(textwrap.indent(textwrap.dedent(openModeInfoStr), 2*' ').strip('\n'))
                print(72*'-'+'\n')
                sys.stdout.flush()
            
            if (self.comm is not None):
                self.comm.Barrier()
            raise FileExistsError()
        
        ## if file open mode is 'w'
        ## --> <delete>, touch, chmod, stripe
        if (self.open_mode == 'w'):
            if (self.rank==0):
                if os.path.isfile(self.fname): ## if the file exists, delete it
                    os.remove(self.fname)
                    time.sleep(0.5)
                Path(self.fname).touch() ## touch a new file
                os.chmod(self.fname, int(perms, base=8)) ## change permissions
                if shutil.which('lfs') is not None: ## set stripe if on Lustre
                    cmd_str_lfs_migrate = f'lfs migrate --stripe-count {stripe_count:d} --stripe-size {stripe_size_mb:d}M {self.fname} > /dev/null 2>&1'
                    return_code = subprocess.call(cmd_str_lfs_migrate, shell=True)
                    if (return_code != 0):
                        raise ValueError('lfs migrate failed')
                    time.sleep(1.)
        
        if (self.comm is not None):
            self.comm.Barrier()
        
        ## call actual h5py.File.__init__()
        super(ztmd, self).__init__(*args, **kwargs)
        self.get_header(verbose=verbose)
        return
    
    def get_header(self,**kwargs):
        '''
        Helper for __init__
        Read attributes of ZTMD class instance & attach
        '''
        
        verbose = kwargs.get('verbose',True)
        
        if (self.rank!=0):
            verbose=False
        
        # === udef
        
        ## Base
        header_attr_keys = [
            'Ma','Re','Pr',
            'kappa','R',
            'p_inf','T_inf',
            'S_Suth','mu_Suth_ref','T_Suth_ref',
            ]
        
        ## Derived
        header_attr_keys_derived = [
            'C_Suth','mu_inf','rho_inf','nu_inf',
            'a_inf','U_inf',
            'cp','cv',
            'recov_fac','Taw',
            'lchar','tchar',
            'uchar','M_inf',
            'p_tot_inf', 'T_tot_inf', 'rho_tot_inf',
            ]
        
        ## Read,attach -- base attributes
        for key in header_attr_keys:
            if key in self.attrs:
                setattr(self, key, self.attrs[key]) ## Attach to ztmd() instance
        
        ## Read,attach -- derived attributes
        for key in header_attr_keys_derived:
            if key in self.attrs:
                setattr(self, key, self.attrs[key]) ## Attach to ztmd() instance
        
        ## Check derived
        if all([ hasattr(self,key) for key in header_attr_keys ]): ## Has all base attrs
            
            cc = types.SimpleNamespace() ## Temporary obj
            
            ## Re-calculate derived attrs
            cc.C_Suth      = self.mu_Suth_ref/(self.T_Suth_ref**(3/2))*(self.T_Suth_ref + self.S_Suth) ## [kg/(m·s·√K)]
            cc.mu_inf      = self.mu_Suth_ref*(self.T_inf/self.T_Suth_ref)**(3/2) * ((self.T_Suth_ref+self.S_Suth)/(self.T_inf+self.S_Suth))
            cc.rho_inf     = self.p_inf/(self.R*self.T_inf)
            #cc.nu_inf      = self.mu_inf/self.rho_inf ## no!
            cc.nu_inf      = cc.mu_inf/cc.rho_inf
            cc.a_inf       = np.sqrt(self.kappa*self.R*self.T_inf)
            cc.U_inf       = self.Ma*self.a_inf
            cc.cp          = self.R*self.kappa/(self.kappa-1.)
            cc.cv          = self.cp/self.kappa
            cc.recov_fac   = self.Pr**(1/3) ## for turbulent boundary layer
            cc.Taw         = self.T_inf + self.recov_fac*self.U_inf**2/(2*self.cp)
            cc.lchar       = self.Re*self.nu_inf/self.U_inf
            cc.tchar       = self.lchar / self.U_inf
            cc.uchar       = self.U_inf
            cc.p_tot_inf   = self.p_inf   * (1 + (self.kappa-1)/2 * self.M_inf**2)**(self.kappa/(self.kappa-1))
            cc.T_tot_inf   = self.T_inf   * (1 + (self.kappa-1)/2 * self.M_inf**2)
            cc.rho_tot_inf = self.rho_inf * (1 + (self.kappa-1)/2 * self.M_inf**2)**(1/(self.kappa-1))
            
            ## Assert that re-calculated derived attrs are equal to HDF5 top-level attrs of same name
            for key in header_attr_keys_derived:
                if hasattr(self,key) and hasattr(cc,key):
                    np.testing.assert_allclose(getattr(self,key), getattr(cc,key), rtol=1e-8, atol=1e-8)
            
            ## Report
            if verbose: print(72*'-')
            if verbose: even_print('Ma'          , '%0.2f [-]'           % self.Ma          )
            if verbose: even_print('Re'          , '%0.1f [-]'           % self.Re          )
            if verbose: even_print('Pr'          , '%0.3f [-]'           % self.Pr          )
            if verbose: even_print('T_inf'       , '%0.3f [K]'           % self.T_inf       )
            if verbose: even_print('p_inf'       , '%0.1f [Pa]'          % self.p_inf       )
            if verbose: even_print('kappa'       , '%0.3f [-]'           % self.kappa       )
            if verbose: even_print('R'           , '%0.3f [J/(kg·K)]'    % self.R           )
            if verbose: even_print('mu_Suth_ref' , '%0.6E [kg/(m·s)]'    % self.mu_Suth_ref )
            if verbose: even_print('T_Suth_ref'  , '%0.2f [K]'           % self.T_Suth_ref  )
            if verbose: even_print('S_Suth'      , '%0.2f [K]'           % self.S_Suth      )
            if verbose: even_print('C_Suth'      , '%0.5e [kg/(m·s·√K)]' % self.C_Suth      )
            
            if verbose: print(72*'-')
            if verbose: even_print('rho_inf'         , '%0.3f [kg/m³]'    % self.rho_inf   )
            if verbose: even_print('mu_inf'          , '%0.6E [kg/(m·s)]' % self.mu_inf    )
            if verbose: even_print('nu_inf'          , '%0.6E [m²/s]'     % self.nu_inf    )
            if verbose: even_print('a_inf'           , '%0.6f [m/s]'      % self.a_inf     )
            if verbose: even_print('U_inf'           , '%0.6f [m/s]'      % self.U_inf     )
            if verbose: even_print('cp'              , '%0.3f [J/(kg·K)]' % self.cp        )
            if verbose: even_print('cv'              , '%0.3f [J/(kg·K)]' % self.cv        )
            #if verbose: even_print('recovery factor' , '%0.6f [-]'        % self.recov_fac )
            if verbose: even_print('Taw'             , '%0.3f [K]'        % self.Taw       )
            if verbose: even_print('lchar'           , '%0.6E [m]'        % self.lchar     )
            if verbose: even_print('tchar'           , '%0.6E [s]'        % self.tchar     )
            #if verbose: print(72*'-'+'\n')
            
            ## Pack & attach a udef dict as attr for convenience
            self.udef = {
                'Ma':self.Ma,
                'Re':self.Re,
                'Pr':self.Pr,
                'kappa':self.kappa,
                'R':self.R,
                'p_inf':self.p_inf,
                'T_inf':self.T_inf,
                'S_Suth':self.S_Suth,
                'mu_Suth_ref':self.mu_Suth_ref,
                'T_Suth_ref':self.T_Suth_ref,
                
                'C_Suth':self.C_Suth,
                'mu_inf':self.mu_inf,
                'rho_inf':self.rho_inf,
                'nu_inf':self.nu_inf,
                'a_inf':self.a_inf,
                'U_inf':self.U_inf,
                'cp':self.cp,
                'cv':self.cv,
                'recov_fac':self.recov_fac,
                'Taw':self.Taw,
                'lchar':self.lchar,
                'tchar':self.tchar,
                
                'uchar':self.uchar,
                'M_inf':self.M_inf,
                
                'p_tot_inf':self.p_tot_inf,
                'T_tot_inf':self.T_tot_inf,
                'rho_tot_inf':self.rho_tot_inf,
                }
        
        # ===
        
        if 'duration_avg' in self.attrs:
            self.duration_avg = self.attrs['duration_avg']
        if 'nx' in self.attrs:
            self.nx = self.attrs['nx']
        if 'ny' in self.attrs:
            self.ny = self.attrs['ny']
        
        if ('dims/x' in self):
            self.x = np.copy( self['dims/x'][()] ) ## dont transpose yet
        if ('dims/y' in self):
            self.y = np.copy( self['dims/y'][()] ) ## dont transpose yet
        if ('dims/t' in self):
            self.t = np.copy( self['dims/t'][()] )
        
        if hasattr(self,'x') and hasattr(self,'y'):
            if (self.x.ndim==1) and (self.y.ndim==1):
                self.xx, self.yy = np.meshgrid( self.x, self.y, indexing='ij' )
            elif (self.x.ndim==2) and (self.y.ndim==2):
                self.x  = np.copy( self.x.T )
                self.y  = np.copy( self.y.T )
                self.xx = np.copy( self.x   )
                self.yy = np.copy( self.y   )
            else:
                raise ValueError
        
        if 'dz' in self.attrs:
            self.dz = self.attrs['dz']
        
        if ('dims/stang' in self):
            self.stang = np.copy( self['dims/stang'][()] )
        if ('dims/snorm' in self):
            self.snorm = np.copy( self['dims/snorm'][()] )
        
        if ('csys/vtang' in self):
            self.vtang = np.copy( self['csys/vtang'][()] )
        if ('csys/vnorm' in self):
            self.vnorm = np.copy( self['csys/vnorm'][()] )
        
        if ('dims/crv_R' in self):
            self.crv_R = np.copy( self['dims/crv_R'][()] )
        if ('dims/R_min' in self):
            self.R_min = self['dims/R_min'][()]
        
        if verbose: print(72*'-')
        if verbose and hasattr(self,'duration_avg'): even_print('duration_avg', '%0.5f'%self.duration_avg)
        if verbose: even_print('nx', '%i'%self.nx)
        if verbose: even_print('ny', '%i'%self.ny)
        #if verbose: print(72*'-')
        
        # ===
        
        if 'rectilinear' in self.attrs:
            self.rectilinear = self.attrs['rectilinear']
        
        if 'curvilinear' in self.attrs:
            self.curvilinear = self.attrs['curvilinear']
        
        ## Check
        if hasattr(self,'rectilinear') and not hasattr(self,'curvilinear'):
            raise ValueError
        if hasattr(self,'curvilinear') and not hasattr(self,'rectilinear'):
            raise ValueError
        if hasattr(self,'rectilinear') or hasattr(self,'curvilinear'):
            if self.rectilinear and self.curvilinear:
                raise ValueError
            if not self.rectilinear and not self.curvilinear:
                raise ValueError
        
        ## Legacy flag for curved cases
        if 'requires_wall_norm_interp' in self.attrs:
            self.requires_wall_norm_interp = self.attrs['requires_wall_norm_interp']
        else:
            self.requires_wall_norm_interp = False
        
        ## ts group names & scalars
        if ('data' in self):
            self.scalars = list(self['data'].keys())
            self.n_scalars = len(self.scalars)
            self.scalars_dtypes = []
            for scalar in self.scalars:
                self.scalars_dtypes.append(self['data/%s'%scalar].dtype)
            self.scalars_dtypes_dict = dict(zip(self.scalars, self.scalars_dtypes)) ## dict {<<scalar>>: <<dtype>>}
        else:
            self.scalars = []
            self.n_scalars = 0
            self.scalars_dtypes = []
            self.scalars_dtypes_dict = dict(zip(self.scalars, self.scalars_dtypes))
        
        return
    
    def import_data_eas4(self, path, **kwargs):
        '''
        Copy data from 2D EAS4 containers (output from NS3D) to a ZTMD container
        -----
        
        The 'path' directory should contain one or more of the following files:
        
        --> mean_flow_mpi.eas
        --> favre_mean_flow_mpi.eas
        --> ext_rms_fluctuation_mpi.eas
        --> ext_favre_fluctuation_mpi.eas
        --> turbulent_budget_mpi.eas
        
        /dims : 2D dimension datasets (x,y,..) and possibly 1D dimension datasets (s_wall,..)
        /data : 2D datasets (u,uIuI,..)
        
        Datasets are dimensionalized to SI units upon import!
        
        /dimless : copy the dimless datasets as a reference
        
        Curvilinear cases may have the following additional HDF5 groups
        
        /data_1Dx : 1D datsets in streamwise (x/s1) direction (μ_wall,ρ_wall,u_τ,..)
        /csys     : coordinate system transformation arrays (projection vectors, transform tensors, etc.)
        -----
        /dims_2Dw : alternate grid (e.g. wall-normal projected/interpolation grid)
        /data_2Dw : data interpolated onto alternate grid
        '''
        
        verbose   = kwargs.get( 'verbose', True)
        recalc_mu = kwargs.get( 'recalc_mu', False)
        
        if verbose: print('\n'+'turbx.ztmd.import_data_eas4()'+'\n'+72*'-')
        t_start_func = timeit.default_timer()
        
        even_print('ztmd',str(self.fname))
        
        ## dz,dt should be input as DIMLESS (freestream) i.e. Δz/lchar, Δt/tchar
        ## --> dz & dt get re-dimensionalized during this func!
        dz = kwargs.get('dz',None)
        nz = kwargs.get('nz',None)
        dt = kwargs.get('dt',None)
        
        path_ztmean = Path(path)
        if not path_ztmean.is_dir():
            raise FileNotFoundError('%s does not exist.'%str(path_ztmean))
        fn_Re_mean     = Path(path_ztmean, 'mean_flow_mpi.eas')
        fn_Fv_mean     = Path(path_ztmean, 'favre_mean_flow_mpi.eas')
        fn_Re_fluct    = Path(path_ztmean, 'ext_rms_fluctuation_mpi.eas')
        fn_Fv_fluct    = Path(path_ztmean, 'ext_favre_fluctuation_mpi.eas')
        fn_turb_budget = Path(path_ztmean, 'turbulent_budget_mpi.eas')
        
        self.attrs['fn_Re_mean']     = str( fn_Re_mean.relative_to(Path())     )
        self.attrs['fn_Fv_mean']     = str( fn_Fv_mean.relative_to(Path())     )
        self.attrs['fn_Re_fluct']    = str( fn_Re_fluct.relative_to(Path())    )
        self.attrs['fn_Fv_fluct']    = str( fn_Fv_fluct.relative_to(Path())    )
        self.attrs['fn_turb_budget'] = str( fn_turb_budget.relative_to(Path()) )
        
        ## the simulation timestep dt is not known from the averaged files
        if (dt is not None):
            self.attrs['dt'] = dt
        if (nz is not None):
            self.attrs['nz'] = nz
        if (dz is not None):
            self.attrs['dz'] = dz
        
        if verbose:
            if (nz is not None):
                even_print('nz' , '%i'%nz )
            if (dz is not None):
                even_print('dz' , '%0.6e'%dz )
            if (dt is not None):
                even_print('dt' , '%0.6e'%dt )
            print(72*'-')
        
        # ===
        
        ## File (1/5) : mean_flow_mpi.eas
        if fn_Re_mean.exists():
            even_print('eas4 Re mean',str(fn_Re_mean.relative_to(Path())))
            with eas4(str(fn_Re_mean),'r',verbose=False) as f1:
                
                ## The EAS4 data is still organized by rank in [z], so perform average across ranks
                data_mean = f1.get_mean()
                
                ## assert mean data shape
                for i, key in enumerate(data_mean.dtype.names):
                    if (data_mean[key].shape[0]!=f1.nx):
                        raise AssertionError('mean data dim1 shape != nx')
                    if (data_mean[key].shape[1]!=f1.ny):
                        raise AssertionError('mean data dim2 shape != ny')
                    if (data_mean[key].ndim!=2):
                        raise AssertionError('mean data ndim != 2')
                
                nx = f1.nx ; self.attrs['nx'] = nx
                ny = f1.ny ; self.attrs['ny'] = ny
                
                ## Primary
                Ma          = f1.Ma          ; self.attrs['Ma']          = Ma
                Re          = f1.Re          ; self.attrs['Re']          = Re
                Pr          = f1.Pr          ; self.attrs['Pr']          = Pr
                T_inf       = f1.T_inf       ; self.attrs['T_inf']       = T_inf
                p_inf       = f1.p_inf       ; self.attrs['p_inf']       = p_inf
                kappa       = f1.kappa       ; self.attrs['kappa']       = kappa
                R           = f1.R           ; self.attrs['R']           = R
                mu_Suth_ref = f1.mu_Suth_ref ; self.attrs['mu_Suth_ref'] = mu_Suth_ref
                T_Suth_ref  = f1.T_Suth_ref  ; self.attrs['T_Suth_ref']  = T_Suth_ref
                C_Suth      = f1.C_Suth      ; self.attrs['C_Suth']      = C_Suth
                S_Suth      = f1.S_Suth      ; self.attrs['S_Suth']      = S_Suth
                
                ## Derived
                rho_inf   = f1.rho_inf    ; self.attrs['rho_inf']   = rho_inf
                mu_inf    = f1.mu_inf     ; self.attrs['mu_inf']    = mu_inf
                nu_inf    = f1.nu_inf     ; self.attrs['nu_inf']    = nu_inf
                a_inf     = f1.a_inf      ; self.attrs['a_inf']     = a_inf
                U_inf     = f1.U_inf      ; self.attrs['U_inf']     = U_inf
                cp        = f1.cp         ; self.attrs['cp']        = cp
                cv        = f1.cv         ; self.attrs['cv']        = cv
                recov_fac = f1.recov_fac  ; self.attrs['recov_fac'] = recov_fac
                Taw       = f1.Taw        ; self.attrs['Taw']       = Taw
                lchar     = f1.lchar      ; self.attrs['lchar']     = lchar
                
                tchar = f1.tchar ; self.attrs['tchar'] = tchar
                uchar = f1.U_inf ; self.attrs['uchar'] = uchar
                M_inf = f1.Ma    ; self.attrs['M_inf'] = M_inf
                
                p_tot_inf   = f1.p_tot_inf   ; self.attrs['p_tot_inf']   = p_tot_inf
                T_tot_inf   = f1.T_tot_inf   ; self.attrs['T_tot_inf']   = T_tot_inf
                rho_tot_inf = f1.rho_tot_inf ; self.attrs['rho_tot_inf'] = rho_tot_inf
                
                ## Duration over which avg was performed, iteration count and the sampling period of the avg
                Re_mean_total_avg_time       = f1.total_avg_time * tchar
                Re_mean_total_avg_iter_count = f1.total_avg_iter_count
                Re_mean_dt                   = Re_mean_total_avg_time / Re_mean_total_avg_iter_count
                
                self.attrs['Re_mean_total_avg_time'] = Re_mean_total_avg_time
                self.attrs['Re_mean_total_avg_iter_count'] = Re_mean_total_avg_iter_count
                self.attrs['Re_mean_dt'] = Re_mean_dt
                
                t_meas = f1.total_avg_time * (f1.lchar/f1.U_inf) ## dimensional [s]
                #t_meas = f1.total_avg_time ## dimless (char)
                self.attrs['t_meas'] = t_meas
                self.create_dataset('dims/t', data=np.array([t_meas],dtype=np.float64), chunks=None)
                
                # ===
                
                ## From EAS4, dimless (char)
                x = np.copy(f1.x)
                y = np.copy(f1.y)
                
                if (f1.x.ndim==1) and (f1.y.ndim==1): ## Rectilinear in [x,y]
                    
                    self.attrs['rectilinear'] = True
                    self.attrs['curvilinear'] = False
                    
                    ## Dimensionalize & write
                    x  *= lchar
                    y  *= lchar
                    dz *= lchar
                    dt *= tchar
                    self.create_dataset('dims/x', data=x, chunks=None, dtype=np.float64)
                    self.create_dataset('dims/y', data=y, chunks=None, dtype=np.float64)
                    self.attrs['dz'] = dz
                    self.attrs['dt'] = dt
                    
                    self.attrs['nx'] = nx
                    self.attrs['ny'] = ny
                    #self.attrs['nz'] = 1 ## NO
                    if verbose:
                        even_print('nx' , '%i'%nx )
                        even_print('ny' , '%i'%ny )
                
                elif (f1.x.ndim==3) and (f1.y.ndim==3): ## Curvilinear in [x,y]
                    
                    self.attrs['rectilinear'] = False
                    self.attrs['curvilinear'] = True
                    
                    ## 3D coords: confirm that x,y coords are same in [z] direction
                    np.testing.assert_allclose( x[-1,-1,:] , x[-1,-1,0] , rtol=1e-10 , atol=1e-10 )
                    np.testing.assert_allclose( y[-1,-1,:] , y[-1,-1,0] , rtol=1e-10 , atol=1e-10 )
                    
                    ## 3D coords: take only 1 layer in [z]
                    x = np.squeeze( np.copy( x[:,:,0] ) ) ## dimless (char)
                    y = np.squeeze( np.copy( y[:,:,0] ) )
                    
                    # if True: ## check against tgg data wall distance file (if it exists)
                    #     fn_dat = '../tgg/wall_distance.dat'
                    #     if os.path.isfile(fn_dat):
                    #         with open(fn_dat,'rb') as f:
                    #             d_ = pickle.load(f)
                    #             xy2d_tmp = d_['xy2d']
                    #             np.testing.assert_allclose(xy2d_tmp[:,:,0], x[:,:,0], rtol=1e-10, atol=1e-10)
                    #             np.testing.assert_allclose(xy2d_tmp[:,:,1], y[:,:,0], rtol=1e-10, atol=1e-10)
                    #             if verbose: even_print('check passed' , 'x grid' )
                    #             if verbose: even_print('check passed' , 'y grid' )
                    #             d_ = None; del d_
                    #             xy2d_tmp = None; del xy2d_tmp
                    
                    # ## backup non-dimensional coordinate arrays
                    # self.create_dataset('/dimless/dims/x', data=x.T, chunks=None)
                    # self.create_dataset('/dimless/dims/y', data=y.T, chunks=None)
                    
                    ## dimensionalize & write
                    x  *= lchar
                    y  *= lchar
                    dz *= lchar
                    dt *= tchar
                    
                    self.create_dataset('dims/x', data=x.T, chunks=None, dtype=np.float64)
                    self.create_dataset('dims/y', data=y.T, chunks=None, dtype=np.float64)
                    self.attrs['dz'] = dz
                    self.attrs['dt'] = dt
                    
                    self.attrs['nx'] = nx
                    self.attrs['ny'] = ny
                    #self.attrs['nz'] = 1 ## NO
                    if verbose:
                        even_print('nx' , '%i'%nx )
                        even_print('ny' , '%i'%ny )
                
                else:
                    raise ValueError('case x.ndim=%i , y.ndim=%i not yet accounted for'%(f1.x.ndim,f1.y.ndim))
                
                # === Redimensionalize quantities (by sim characteristic quantities)
                
                u   = np.copy( data_mean['u']   ) * U_inf 
                v   = np.copy( data_mean['v']   ) * U_inf
                w   = np.copy( data_mean['w']   ) * U_inf
                rho = np.copy( data_mean['rho'] ) * rho_inf
                p   = np.copy( data_mean['p']   ) * (rho_inf * U_inf**2)
                T   = np.copy( data_mean['T']   ) * T_inf
                mu  = np.copy( data_mean['mu']  ) * mu_inf
                
                # === Check μ
                #
                # the O(1%) discrepancies are due to [z,t] averaging
                # μ=f(T) BUT this no longer holds exactly once averaged
                # the user should decide if <μ> should be re-calculated from <T>
                
                T_NS3D = np.copy( data_mean['T'] ) ## dimless
                
                ## Non-dimensional Suth Temp 'Ts' 
                ## 'equations.F90', subroutines calc_viscosity() & initialize_viscosity()
                Ts = S_Suth/T_inf
                mu_NS3D = np.copy( T_NS3D**1.5 * ( 1 + Ts ) / ( T_NS3D + Ts ) ) ## dimless
                np.testing.assert_allclose(mu/mu_inf, mu_NS3D, rtol=0.003)
                
                mu_A = np.copy( mu_Suth_ref*(T/T_Suth_ref)**(3/2) * ((T_Suth_ref+S_Suth)/(T+S_Suth)) )
                mu_B = np.copy( C_Suth * T**(3/2) / (T + S_Suth) )
                np.testing.assert_allclose(mu_A, mu_B, rtol=1e-6) ## single precision
                
                np.testing.assert_allclose(mu, mu_A, rtol=0.003)
                np.testing.assert_allclose(mu, mu_B, rtol=0.003)
                
                ## !!! Recalculate and replace <μ> !!!
                if recalc_mu:
                    mu = np.copy( C_Suth * T**(3/2) / (T + S_Suth) )
                
                ## Clear structured array from memory
                data_mean = None; del data_mean
                
                ## Derived 2D fields from
                a     = np.copy( np.sqrt( kappa * R * T )      )
                nu    = np.copy( mu / rho                      )
                umag  = np.copy( np.sqrt( u**2 + v**2 + w**2 ) )
                M     = np.copy( umag / np.sqrt(kappa * R * T) )
                
                T_tot   = np.copy( T   * (1 + (kappa-1)/2 * M**2)                    )
                p_tot   = np.copy( p   * (1 + (kappa-1)/2 * M**2)**(kappa/(kappa-1)) )
                rho_tot = np.copy( rho * (1 + (kappa-1)/2 * M**2)**(1/(kappa-1))     )
                
                ## Base 2D scalars [ρ,u,v,w,T,p]
                self.create_dataset('data/rho' , data=rho.T , chunks=None)
                self.create_dataset('data/u'   , data=u.T   , chunks=None)
                self.create_dataset('data/v'   , data=v.T   , chunks=None)
                self.create_dataset('data/w'   , data=w.T   , chunks=None)
                self.create_dataset('data/T'   , data=T.T   , chunks=None)
                self.create_dataset('data/p'   , data=p.T   , chunks=None)
                
                ## Derived 2D fields
                self.create_dataset('data/a'       , data=a.T       , chunks=None) ## Speed of sound
                self.create_dataset('data/mu'      , data=mu.T      , chunks=None)
                self.create_dataset('data/nu'      , data=nu.T      , chunks=None)
                self.create_dataset('data/umag'    , data=umag.T    , chunks=None)
                self.create_dataset('data/M'       , data=M.T       , chunks=None)
                self.create_dataset('data/T_tot'   , data=T_tot.T   , chunks=None)
                self.create_dataset('data/p_tot'   , data=p_tot.T   , chunks=None)
                self.create_dataset('data/rho_tot' , data=rho_tot.T , chunks=None)
        
        ## File (2/5) : favre_mean_flow_mpi.eas
        if fn_Re_fluct.exists():
            even_print('eas4 Re fluct',str(fn_Re_fluct.relative_to(Path())))
            with eas4(str(fn_Re_fluct),'r',verbose=False) as f1:
                
                data_mean = f1.get_mean()
                
                ## assert mean data shape
                for i, key in enumerate(data_mean.dtype.names):
                    if (data_mean[key].shape[0]!=f1.nx):
                        raise AssertionError('mean data dim1 shape != nx')
                    if (data_mean[key].shape[1]!=f1.ny):
                        raise AssertionError('mean data dim2 shape != ny')
                    if (data_mean[key].ndim!=2):
                        raise AssertionError('mean data ndim != 2')
                
                Re_fluct_total_avg_time       = f1.total_avg_time
                Re_fluct_total_avg_iter_count = f1.total_avg_iter_count
                Re_fluct_dt                   = Re_fluct_total_avg_time/Re_fluct_total_avg_iter_count
                
                self.attrs['Re_fluct_total_avg_time'] = Re_fluct_total_avg_time
                self.attrs['Re_fluct_total_avg_iter_count'] = Re_fluct_total_avg_iter_count
                self.attrs['Re_fluct_dt'] = Re_fluct_dt
                
                uI_uI = data_mean["u'u'"] * U_inf**2
                vI_vI = data_mean["v'v'"] * U_inf**2
                wI_wI = data_mean["w'w'"] * U_inf**2
                uI_vI = data_mean["u'v'"] * U_inf**2
                uI_wI = data_mean["u'w'"] * U_inf**2
                vI_wI = data_mean["v'w'"] * U_inf**2
                
                self.create_dataset('data/uI_uI', data=uI_uI.T, chunks=None)
                self.create_dataset('data/vI_vI', data=vI_vI.T, chunks=None)
                self.create_dataset('data/wI_wI', data=wI_wI.T, chunks=None)
                self.create_dataset('data/uI_vI', data=uI_vI.T, chunks=None)
                self.create_dataset('data/uI_wI', data=uI_wI.T, chunks=None)
                self.create_dataset('data/vI_wI', data=vI_wI.T, chunks=None)
                
                uI_TI = data_mean["u'T'"] * (U_inf*T_inf)
                vI_TI = data_mean["v'T'"] * (U_inf*T_inf)
                wI_TI = data_mean["w'T'"] * (U_inf*T_inf)
                
                self.create_dataset('data/uI_TI', data=uI_TI.T, chunks=None)
                self.create_dataset('data/vI_TI', data=vI_TI.T, chunks=None)
                self.create_dataset('data/wI_TI', data=wI_TI.T, chunks=None)
                
                TI_TI = data_mean["T'T'"] * T_inf**2
                pI_pI = data_mean["p'p'"] * (rho_inf * U_inf**2)**2
                rI_rI = data_mean["r'r'"] * rho_inf**2
                muI_muI = data_mean["mu'mu'"] * mu_inf**2
                
                self.create_dataset('data/TI_TI',   data=TI_TI.T,   chunks=None)
                self.create_dataset('data/pI_pI',   data=pI_pI.T,   chunks=None)
                self.create_dataset('data/rI_rI',   data=rI_rI.T,   chunks=None)
                self.create_dataset('data/muI_muI', data=muI_muI.T, chunks=None)
                
                tauI_xx = data_mean["tau'_xx"] * mu_inf * U_inf / lchar
                tauI_yy = data_mean["tau'_yy"] * mu_inf * U_inf / lchar
                tauI_zz = data_mean["tau'_zz"] * mu_inf * U_inf / lchar
                tauI_xy = data_mean["tau'_xy"] * mu_inf * U_inf / lchar
                tauI_xz = data_mean["tau'_xz"] * mu_inf * U_inf / lchar
                tauI_yz = data_mean["tau'_yz"] * mu_inf * U_inf / lchar
                
                self.create_dataset('data/tauI_xx', data=tauI_xx.T, chunks=None)
                self.create_dataset('data/tauI_yy', data=tauI_yy.T, chunks=None)
                self.create_dataset('data/tauI_zz', data=tauI_zz.T, chunks=None)
                self.create_dataset('data/tauI_xy', data=tauI_xy.T, chunks=None)
                self.create_dataset('data/tauI_xz', data=tauI_xz.T, chunks=None)
                self.create_dataset('data/tauI_yz', data=tauI_yz.T, chunks=None)
                
                # === RMS values
                
                if True: ## dimensional
                    
                    uI_uI_rms = np.sqrt(       data_mean["u'u'"]  * U_inf**2 )
                    vI_vI_rms = np.sqrt(       data_mean["v'v'"]  * U_inf**2 )
                    wI_wI_rms = np.sqrt(       data_mean["w'w'"]  * U_inf**2 )
                    uI_vI_rms = np.sqrt(np.abs(data_mean["u'v'"]) * U_inf**2 ) * np.sign(data_mean["u'v'"]) 
                    uI_wI_rms = np.sqrt(np.abs(data_mean["u'w'"]) * U_inf**2 ) * np.sign(data_mean["u'w'"])
                    vI_wI_rms = np.sqrt(np.abs(data_mean["v'w'"]) * U_inf**2 ) * np.sign(data_mean["v'w'"])
                    
                    uI_TI_rms = np.sqrt(np.abs(data_mean["u'T'"]) * U_inf*T_inf) * np.sign(data_mean["u'T'"])
                    vI_TI_rms = np.sqrt(np.abs(data_mean["v'T'"]) * U_inf*T_inf) * np.sign(data_mean["v'T'"])
                    wI_TI_rms = np.sqrt(np.abs(data_mean["w'T'"]) * U_inf*T_inf) * np.sign(data_mean["w'T'"])
                    
                    rI_rI_rms   = np.sqrt( data_mean["r'r'"]   * rho_inf**2              )
                    TI_TI_rms   = np.sqrt( data_mean["T'T'"]   * T_inf**2                )
                    pI_pI_rms   = np.sqrt( data_mean["p'p'"]   * (rho_inf * U_inf**2)**2 )
                    muI_muI_rms = np.sqrt( data_mean["mu'mu'"] * mu_inf**2               )
                    
                    M_rms = uI_uI_rms / np.sqrt(kappa * R * T)
                
                # if False: ## dimless
                #     
                #     uI_uI_rms = np.sqrt(        data_mean["u'u'"]  )
                #     vI_vI_rms = np.sqrt(        data_mean["v'v'"]  )
                #     wI_wI_rms = np.sqrt(        data_mean["w'w'"]  )
                #     uI_vI_rms = np.sqrt( np.abs(data_mean["u'v'"]) ) * np.sign(data_mean["u'v'"]) 
                #     uI_wI_rms = np.sqrt( np.abs(data_mean["u'w'"]) ) * np.sign(data_mean["u'w'"])
                #     vI_wI_rms = np.sqrt( np.abs(data_mean["v'w'"]) ) * np.sign(data_mean["v'w'"])
                #     
                #     uI_TI_rms = np.sqrt( np.abs(data_mean["u'T'"]) ) * np.sign(data_mean["u'T'"])
                #     vI_TI_rms = np.sqrt( np.abs(data_mean["v'T'"]) ) * np.sign(data_mean["v'T'"])
                #     wI_TI_rms = np.sqrt( np.abs(data_mean["w'T'"]) ) * np.sign(data_mean["w'T'"])
                #     
                #     rI_rI_rms   = np.sqrt( data_mean["r'r'"]   )
                #     TI_TI_rms   = np.sqrt( data_mean["T'T'"]   )
                #     pI_pI_rms   = np.sqrt( data_mean["p'p'"]   )
                #     muI_muI_rms = np.sqrt( data_mean["mu'mu'"] )
                #     
                #     # ...
                #     M_rms = np.sqrt( data_mean["u'u'"] * U_inf**2 ) / np.sqrt(kappa * R * (T*T_inf) )
                
                # ===
                
                self.create_dataset( 'data/uI_uI_rms' , data=uI_uI_rms.T , chunks=None )
                self.create_dataset( 'data/vI_vI_rms' , data=vI_vI_rms.T , chunks=None )
                self.create_dataset( 'data/wI_wI_rms' , data=wI_wI_rms.T , chunks=None )
                self.create_dataset( 'data/uI_vI_rms' , data=uI_vI_rms.T , chunks=None )
                self.create_dataset( 'data/uI_wI_rms' , data=uI_wI_rms.T , chunks=None )
                self.create_dataset( 'data/vI_wI_rms' , data=vI_wI_rms.T , chunks=None )
                
                self.create_dataset( 'data/uI_TI_rms' , data=uI_TI_rms.T , chunks=None )
                self.create_dataset( 'data/vI_TI_rms' , data=vI_TI_rms.T , chunks=None )
                self.create_dataset( 'data/wI_TI_rms' , data=wI_TI_rms.T , chunks=None )
                
                self.create_dataset( 'data/rI_rI_rms'   , data=rI_rI_rms.T   , chunks=None )
                self.create_dataset( 'data/TI_TI_rms'   , data=TI_TI_rms.T   , chunks=None )
                self.create_dataset( 'data/pI_pI_rms'   , data=pI_pI_rms.T   , chunks=None )
                self.create_dataset( 'data/muI_muI_rms' , data=muI_muI_rms.T , chunks=None )
                
                self.create_dataset( 'data/M_rms' , data=M_rms.T , chunks=None )
        
        ## File (3/5) : ext_rms_fluctuation_mpi.eas
        if fn_Fv_mean.exists():
            #print('--r-> %s'%fn_Fv_mean.relative_to(Path()) )
            even_print('eas4 Fv mean',str(fn_Fv_mean.relative_to(Path())))
            with eas4(str(fn_Fv_mean),'r',verbose=False) as f1:
                
                ## the EAS4 data is still organized by rank in [z], so perform average across ranks
                data_mean = f1.get_mean()
                
                ## assert mean data shape
                for i, key in enumerate(data_mean.dtype.names):
                    if (data_mean[key].shape[0]!=f1.nx):
                        raise AssertionError('mean data dim1 shape != nx')
                    if (data_mean[key].shape[1]!=f1.ny):
                        raise AssertionError('mean data dim2 shape != ny')
                    if (data_mean[key].ndim!=2):
                        raise AssertionError('mean data ndim != 2')
                
                ## duration over which avg was performed, iteration count and the sampling period of the avg
                Fv_mean_total_avg_time       = f1.total_avg_time * tchar
                Fv_mean_total_avg_iter_count = f1.total_avg_iter_count
                Fv_mean_dt                   = Fv_mean_total_avg_time / Fv_mean_total_avg_iter_count
                
                self.attrs['Fv_mean_total_avg_time'] = Fv_mean_total_avg_time
                self.attrs['Fv_mean_total_avg_iter_count'] = Fv_mean_total_avg_iter_count
                self.attrs['Fv_mean_dt'] = Fv_mean_dt
                
                u_Fv   = np.copy( data_mean['u']   ) * U_inf 
                v_Fv   = np.copy( data_mean['v']   ) * U_inf
                w_Fv   = np.copy( data_mean['w']   ) * U_inf
                rho_Fv = np.copy( data_mean['rho'] ) * rho_inf
                p_Fv   = np.copy( data_mean['p']   ) * (rho_inf * U_inf**2)
                T_Fv   = np.copy( data_mean['T']   ) * T_inf
                mu_Fv  = np.copy( data_mean['mu']  ) * mu_inf
                
                uu_Fv  = np.copy( data_mean['uu'] ) * U_inf**2
                uv_Fv  = np.copy( data_mean['uv'] ) * U_inf**2
                
                data_mean = None; del data_mean
                
                self.create_dataset('data/u_Fv'   , data=u_Fv.T   , chunks=None)
                self.create_dataset('data/v_Fv'   , data=v_Fv.T   , chunks=None)
                self.create_dataset('data/w_Fv'   , data=w_Fv.T   , chunks=None)
                self.create_dataset('data/rho_Fv' , data=rho_Fv.T , chunks=None)
                self.create_dataset('data/p_Fv'   , data=p_Fv.T   , chunks=None)
                self.create_dataset('data/T_Fv'   , data=T_Fv.T   , chunks=None)
                self.create_dataset('data/mu_Fv'  , data=mu_Fv.T  , chunks=None)
                
                self.create_dataset('data/uu_Fv' , data=uu_Fv.T   , chunks=None)
                self.create_dataset('data/uv_Fv' , data=uv_Fv.T   , chunks=None)
        
        ## File (4/5) : ext_favre_fluctuation_mpi.eas
        if fn_Fv_fluct.exists():
            #print('--r-> %s'%fn_Fv_fluct.relative_to(Path()) )
            even_print('eas4 Fv fluct',str(fn_Fv_fluct.relative_to(Path())))
            with eas4(str(fn_Fv_fluct),'r',verbose=False) as f1:
                
                data_mean = f1.get_mean()
                
                ## assert mean data shape
                for i, key in enumerate(data_mean.dtype.names):
                    if (data_mean[key].shape[0]!=f1.nx):
                        raise AssertionError('mean data dim1 shape != nx')
                    if (data_mean[key].shape[1]!=f1.ny):
                        raise AssertionError('mean data dim2 shape != ny')
                    if (data_mean[key].ndim!=2):
                        raise AssertionError('mean data ndim != 2')
                
                Fv_fluct_total_avg_time       = f1.total_avg_time
                Fv_fluct_total_avg_iter_count = f1.total_avg_iter_count
                Fv_fluct_dt                   = Fv_fluct_total_avg_time/Fv_fluct_total_avg_iter_count
                
                self.attrs['Fv_fluct_total_avg_time'] = Fv_fluct_total_avg_time
                self.attrs['Fv_fluct_total_avg_iter_count'] = Fv_fluct_total_avg_iter_count
                self.attrs['Fv_fluct_dt'] = Fv_fluct_dt
                
                r_uII_uII = data_mean["r u''u''"]  * rho_inf * U_inf**2
                r_vII_vII = data_mean["r v''v''"]  * rho_inf * U_inf**2
                r_wII_wII = data_mean["r w''_w''"] * rho_inf * U_inf**2
                r_uII_vII = data_mean["r u''v''"]  * rho_inf * U_inf**2
                r_uII_wII = data_mean["r u''w''"]  * rho_inf * U_inf**2
                r_vII_wII = data_mean["r w''v''"]  * rho_inf * U_inf**2
                
                self.create_dataset('data/r_uII_uII', data=r_uII_uII.T, chunks=None)
                self.create_dataset('data/r_vII_vII', data=r_vII_vII.T, chunks=None)
                self.create_dataset('data/r_wII_wII', data=r_wII_wII.T, chunks=None)
                self.create_dataset('data/r_uII_vII', data=r_uII_vII.T, chunks=None)
                self.create_dataset('data/r_uII_wII', data=r_uII_wII.T, chunks=None)
                self.create_dataset('data/r_vII_wII', data=r_vII_wII.T, chunks=None)
                
                r_uII_TII = data_mean["r u''T''"] * rho_inf * U_inf * T_inf
                r_vII_TII = data_mean["r v''T''"] * rho_inf * U_inf * T_inf
                r_wII_TII = data_mean["r w''T''"] * rho_inf * U_inf * T_inf
                
                self.create_dataset('data/r_uII_TII', data=r_uII_TII.T, chunks=None)
                self.create_dataset('data/r_vII_TII', data=r_vII_TII.T, chunks=None)
                self.create_dataset('data/r_wII_TII', data=r_wII_TII.T, chunks=None)
                
                r_TII_TII   = data_mean["r T''T''"]   * rho_inf * T_inf**2
                r_pII_pII   = data_mean["r p''p''"]   * rho_inf * (rho_inf * U_inf**2)**2
                r_rII_rII   = data_mean["r r''r''"]   * rho_inf * rho_inf**2
                r_muII_muII = data_mean["r mu''mu''"] * rho_inf * mu_inf**2
                
                self.create_dataset('data/r_TII_TII',   data=r_TII_TII.T,   chunks=None)
                self.create_dataset('data/r_pII_pII',   data=r_pII_pII.T,   chunks=None)
                self.create_dataset('data/r_rII_rII',   data=r_rII_rII.T,   chunks=None)
                self.create_dataset('data/r_muII_muII', data=r_muII_muII.T, chunks=None)
                
                # === RMS
                
                if True:
                    
                    r_uII_uII_rms = np.sqrt(       data_mean["r u''u''"]  * rho_inf * U_inf**2 )
                    r_vII_vII_rms = np.sqrt(       data_mean["r v''v''"]  * rho_inf * U_inf**2 )
                    r_wII_wII_rms = np.sqrt(       data_mean["r w''_w''"] * rho_inf * U_inf**2 )
                    r_uII_vII_rms = np.sqrt(np.abs(data_mean["r u''v''"]) * rho_inf * U_inf**2 ) * np.sign(data_mean["r u''v''"]) 
                    r_uII_wII_rms = np.sqrt(np.abs(data_mean["r u''w''"]) * rho_inf * U_inf**2 ) * np.sign(data_mean["r u''w''"])
                    r_vII_wII_rms = np.sqrt(np.abs(data_mean["r w''v''"]) * rho_inf * U_inf**2 ) * np.sign(data_mean["r w''v''"])
                    ## ... ρ·u″T″
                    
                    self.create_dataset( 'data/r_uII_uII_rms' , data=r_uII_uII_rms.T , chunks=None )
                    self.create_dataset( 'data/r_vII_vII_rms' , data=r_vII_vII_rms.T , chunks=None )
                    self.create_dataset( 'data/r_wII_wII_rms' , data=r_wII_wII_rms.T , chunks=None )
                    self.create_dataset( 'data/r_uII_vII_rms' , data=r_uII_vII_rms.T , chunks=None )
                    self.create_dataset( 'data/r_uII_wII_rms' , data=r_uII_wII_rms.T , chunks=None )
                    self.create_dataset( 'data/r_vII_wII_rms' , data=r_vII_wII_rms.T , chunks=None )
                    ## ... ρ·u″T″
        
        ## File (5/5) : turbulent_budget_mpi.eas
        if fn_turb_budget.exists():
            #print('--r-> %s'%fn_turb_budget.relative_to(Path()) )
            even_print('eas4 turb budget',str(fn_turb_budget.relative_to(Path())))
            with eas4(str(fn_turb_budget),'r',verbose=False) as f1:
                
                data_mean = f1.get_mean() ## numpy structured array
                
                ## assert mean data shape
                for i, key in enumerate(data_mean.dtype.names):
                    if (data_mean[key].shape[0]!=f1.nx):
                        raise AssertionError('mean data dim1 shape != nx')
                    if (data_mean[key].shape[1]!=f1.ny):
                        raise AssertionError('mean data dim2 shape != ny')
                    if (data_mean[key].ndim!=2):
                        raise AssertionError('mean data ndim != 2')
                
                turb_budget_total_avg_time       = f1.total_avg_time
                turb_budget_total_avg_iter_count = f1.total_avg_iter_count
                turb_budget_dt                   = turb_budget_total_avg_time/turb_budget_total_avg_iter_count
                
                self.attrs['turb_budget_total_avg_time'] = turb_budget_total_avg_time
                self.attrs['turb_budget_total_avg_iter_count'] = turb_budget_total_avg_iter_count
                self.attrs['turb_budget_dt'] = turb_budget_dt
                
                production     = data_mean['prod.']     * U_inf**3 * rho_inf / lchar
                dissipation    = data_mean['dis.']      * U_inf**2 * mu_inf  / lchar**2
                turb_transport = data_mean['t-transp.'] * U_inf**3 * rho_inf / lchar
                visc_diffusion = data_mean['v-diff.']   * U_inf**2 * mu_inf  / lchar**2
                p_diffusion    = data_mean['p-diff.']   * U_inf**3 * rho_inf / lchar
                p_dilatation   = data_mean['p-dilat.']  * U_inf**3 * rho_inf / lchar
                rho_terms      = data_mean['rho-terms'] * U_inf**3 * rho_inf / lchar
                
                self.create_dataset('data/production'     , data=production.T     , chunks=None)
                self.create_dataset('data/dissipation'    , data=dissipation.T    , chunks=None)
                self.create_dataset('data/turb_transport' , data=turb_transport.T , chunks=None)
                self.create_dataset('data/visc_diffusion' , data=visc_diffusion.T , chunks=None)
                self.create_dataset('data/p_diffusion'    , data=p_diffusion.T    , chunks=None)
                self.create_dataset('data/p_dilatation'   , data=p_dilatation.T   , chunks=None)
                self.create_dataset('data/rho_terms'      , data=rho_terms.T      , chunks=None)
                
                Kolm_len = (nu**3 / np.abs(dissipation))**(1/4)
                self.create_dataset('data/Kolm_len', data=Kolm_len.T, chunks=None)
        
        # ===
        
        self.get_header(verbose=True)
        if verbose: print(72*'-')
        if verbose: print('total time : turbx.ztmd.import_data_eas4() : %s'%format_time_string((timeit.default_timer() - t_start_func)))
        if verbose: print(72*'-')
        
        return
    
    def import_data_eas3(self, path, **kwargs):
        '''
        Copy data from legacy EAS3 containers (output from NS3D) to a ZTMD container
        -----
        
        The 'path' directory should contain one or more of the following files:
        
        --> mean_flow_all_mittel-z.eas
        --> favre_mean_flow_all_mittel-z.eas
        --> ext_rms_fluctuation_all_mittel-z.eas
        --> ext_favre_fluctuation_all_mittel-z.eas
        --> turbulent_budget_all_mittel-z.eas
        
        /dims : 2D dimension datasets (x,y,..)
        /data : 2D datasets (u,uIuI,..)
        
        Datasets are dimensionalized to SI units upon import!
        '''
        
        verbose   = kwargs.get('verbose',True)
        recalc_mu = kwargs.get( 'recalc_mu', False)
        
        if verbose: print('\n'+'turbx.ztmd.import_data_eas3()'+'\n'+72*'-')
        t_start_func = timeit.default_timer()
        
        even_print('ztmd',str(self.fname))
        
        ## dz,dt should be input as dimless (characteristic/inlet) (output from tgg)
        ## --> dz & dt get re-dimensionalized during this func!
        dz = kwargs.get('dz',None)
        nz = kwargs.get('nz',None)
        dt = kwargs.get('dt',None)
        
        path_ztmean = Path(path)
        if not path_ztmean.is_dir():
            raise FileNotFoundError('%s does not exist.'%str(path_ztmean))
        fn_Re_mean     = Path(path_ztmean, 'mean_flow_all_mittel-z.eas')
        fn_Fv_mean     = Path(path_ztmean, 'favre_mean_flow_all_mittel-z.eas')
        fn_Re_fluct    = Path(path_ztmean, 'ext_rms_fluctuation_all_mittel-z.eas')
        fn_Fv_fluct    = Path(path_ztmean, 'ext_favre_fluctuation_all_mittel-z.eas')
        fn_turb_budget = Path(path_ztmean, 'turbulent_budget_all_mittel-z.eas')
        
        self.attrs['fn_Re_mean']     = str( fn_Re_mean.relative_to(Path())     )
        self.attrs['fn_Fv_mean']     = str( fn_Fv_mean.relative_to(Path())     )
        self.attrs['fn_Re_fluct']    = str( fn_Re_fluct.relative_to(Path())    )
        self.attrs['fn_Fv_fluct']    = str( fn_Fv_fluct.relative_to(Path())    )
        self.attrs['fn_turb_budget'] = str( fn_turb_budget.relative_to(Path()) )
        
        ## the simulation timestep dt is not known from the averaged files
        if (dt is not None):
            self.attrs['dt'] = dt
            setattr(self,'dt',dt)
        if (nz is not None):
            self.attrs['nz'] = nz
            setattr(self,'nz',nz)
        if (dz is not None):
            self.attrs['dz'] = dz
            setattr(self,'dz',dz)
        
        if verbose:
            if (nz is not None):
                even_print('nz' , '%i'%nz )
            if (dz is not None):
                even_print('dz' , '%0.6e'%dz )
            if (dt is not None):
                even_print('dt' , '%0.6e'%dt )
            print(72*'-')
        
        # ===
        
        ## this function currently requires that the Reynolds mean file exists
        if not fn_Re_mean.exists():
            raise FileNotFoundError(str(fn_Re_mean))
        
        if fn_Re_mean.exists(): ## Reynolds mean (must exist!)
            even_print('eas3 Re mean',str(fn_Re_mean.relative_to(Path())))
            with eas3(fname=str(fn_Re_mean),verbose=False) as f1:
                
                nx = f1.nx ; self.attrs['nx'] = nx
                ny = f1.ny ; self.attrs['ny'] = ny
                
                Ma          = f1.Ma          ; self.attrs['Ma']          = Ma
                Re          = f1.Re          ; self.attrs['Re']          = Re
                Pr          = f1.Pr          ; self.attrs['Pr']          = Pr
                T_inf       = f1.T_inf       ; self.attrs['T_inf']       = T_inf
                p_inf       = f1.p_inf       ; self.attrs['p_inf']       = p_inf
                kappa       = f1.kappa       ; self.attrs['kappa']       = kappa
                R           = f1.R           ; self.attrs['R']           = R
                mu_Suth_ref = f1.mu_Suth_ref ; self.attrs['mu_Suth_ref'] = mu_Suth_ref
                T_Suth_ref  = f1.T_Suth_ref  ; self.attrs['T_Suth_ref']  = T_Suth_ref
                C_Suth      = f1.C_Suth      ; self.attrs['C_Suth']      = C_Suth
                S_Suth      = f1.S_Suth      ; self.attrs['S_Suth']      = S_Suth
                
                rho_inf   = f1.rho_inf   # ; self.attrs['rho_inf']   = rho_inf
                mu_inf    = f1.mu_inf    # ; self.attrs['mu_inf']    = mu_inf
                #nu_inf    = f1.nu_inf    # ; self.attrs['nu_inf']    = nu_inf
                #a_inf     = f1.a_inf     # ; self.attrs['a_inf']     = a_inf
                U_inf     = f1.U_inf     # ; self.attrs['U_inf']     = U_inf
                #cp        = f1.cp        # ; self.attrs['cp']        = cp
                #cv        = f1.cv        # ; self.attrs['cv']        = cv
                #recov_fac = f1.recov_fac # ; self.attrs['recov_fac'] = recov_fac
                #Taw       = f1.Taw       # ; self.attrs['Taw']       = Taw
                lchar     = f1.lchar     # ; self.attrs['lchar']     = lchar
                
                tchar = f1.lchar/f1.U_inf # ; self.attrs['tchar'] = tchar
                
                setattr(self,'lchar',lchar)
                setattr(self,'tchar',tchar)
                setattr(self,'U_inf',U_inf)
                
                # ===
                
                if (f1.t.shape[0]==1):
                    f1.total_avg_time = float(f1.t[0])
                else:
                    raise NotImplementedError
                
                ## duration over which avg was performed, iteration count and the sampling period of the avg
                Re_mean_total_avg_time       = f1.total_avg_time * tchar
                Re_mean_total_avg_iter_count = f1.total_avg_iter_count
                Re_mean_dt                   = Re_mean_total_avg_time / Re_mean_total_avg_iter_count
                
                self.attrs['Re_mean_total_avg_time'] = Re_mean_total_avg_time
                self.attrs['Re_mean_total_avg_iter_count'] = Re_mean_total_avg_iter_count
                self.attrs['Re_mean_dt'] = Re_mean_dt
                
                t_meas = f1.total_avg_time * (f1.lchar/f1.U_inf) ## dimensional [s]
                #t_meas = f1.total_avg_time ## dimless (char)
                self.attrs['t_meas'] = t_meas
                self.create_dataset('dims/t', data=np.array([t_meas,],dtype=np.float64), chunks=None)
                
                # ===
                
                ## from EAS3, dimless (char)
                x = np.copy(f1.x)
                y = np.copy(f1.y)
                
                if (f1.x.ndim==1) and (f1.y.ndim==1): ## rectilinear in [x,y]
                    
                    self.attrs['rectilinear'] = True
                    self.attrs['curvilinear'] = False
                    
                    ## dimensionalize
                    x  *= lchar
                    y  *= lchar
                    dz *= lchar
                    dt *= tchar
                    
                    ## write
                    self.create_dataset('dims/x', data=x, chunks=None, dtype=np.float64)
                    self.create_dataset('dims/y', data=y, chunks=None, dtype=np.float64)
                    self.attrs['dz'] = dz
                    self.attrs['dt'] = dt
                    self.attrs['nx'] = nx
                    self.attrs['ny'] = ny
                    #self.attrs['nz'] = 1 ## NO
                    
                    if verbose:
                        even_print('nx' , '%i'%nx )
                        even_print('ny' , '%i'%ny )
                    
                    setattr(self,'x',x)
                    setattr(self,'y',y)
                    
                    setattr(self,'dz',dz)
                    setattr(self,'dt',dt)
                    setattr(self,'nx',nx)
                    setattr(self,'ny',ny)
                
                else:
                    raise NotImplementedError
                
                # ===
                
                if (f1.scalars != f1.attr_param):
                    raise AssertionError
                if (f1.ndim3!=1):
                    raise AssertionError
                
                if (f1.accuracy == f1.IEEES):
                    dtypes = [ np.float32 for _ in f1.scalars ]
                if (f1.accuracy == f1.IEEED):
                    dtypes = [ np.float64 for _ in f1.scalars ]
                else:
                    raise ValueError
                
                ## numpy structured array
                data = np.zeros( shape=(nx,ny), dtype={'names':f1.scalars,'formats':dtypes} )
                
                ## populate structured array from EAS3 binary data file
                progress_bar = tqdm(total=f1.nt*f1.npar, ncols=100, desc='import eas3 Re mean', leave=False)
                for scalar in f1.attr_param:
                    tqdm.write(even_print(scalar,f'({nx},{ny})',s=True))
                    for jj in range(f1.ndim2):
                        if f1.accuracy == f1.IEEES:
                            packet = struct.unpack('!'+str(f1.ndim1)+'f',f1.f.read(4*f1.ndim1))[:]
                        else:
                            packet = struct.unpack('!'+str(f1.ndim1)+'d',f1.f.read(8*f1.ndim1))[:]
                        data[scalar][:,jj] = packet
                    progress_bar.update()
                progress_bar.close()
                
                ## re-dimensionalize by characteristic freestream quantities
                for scalar in data.dtype.names:
                    if scalar in ['u','v','w', 'uI','vI','wI', 'uII','vII','wII',]:
                        data[scalar] *= U_inf
                    elif scalar in ['r_uII','r_vII','r_wII']:
                        data[scalar] *= (U_inf*rho_inf)
                    elif scalar in ['T','TI','TII']:
                        data[scalar] *= T_inf
                    elif scalar in ['r_TII']:
                        data[scalar] *= (T_inf*rho_inf)
                    elif scalar in ['rho','rhoI']:
                        data[scalar] *= rho_inf
                    elif scalar in ['p','pI','pII']:
                        data[scalar] *= (rho_inf * U_inf**2)
                    elif scalar in ['mu']:
                        data[scalar] *= mu_inf
                    else:
                        raise ValueError(f"condition needed for redimensionalizing '{scalar}'")
                
                ## write structured array to ZTMD
                for scalar in data.dtype.names:
                    self.create_dataset(f'data/{scalar}', data=data[scalar].T, chunks=None)
                
                ## already made dimensional
                u   = np.copy( data['u']   )
                v   = np.copy( data['v']   )
                w   = np.copy( data['w']   )
                rho = np.copy( data['rho'] )
                p   = np.copy( data['p']   )
                T   = np.copy( data['T']   )
                mu  = np.copy( data['mu']  )
                
                # === check μ
                #
                # the O(1%) discrepancies are due to [z,t] averaging
                # μ=f(T) BUT this no longer holds exactly once averaged
                # the user should decide if <μ> should be re-calculated from <T>
                
                T_NS3D = np.copy( data['T']/T_inf ) ## dimless
                
                ## Non-dimensional Suth Temp 'Ts'
                ## 'equations.F90', subroutine initialize_viscosity()
                Ts = S_Suth/T_inf
                mu_NS3D = np.copy( T_NS3D**1.5 * ( 1 + Ts ) / ( T_NS3D + Ts ) ) ## dimless
                np.testing.assert_allclose(mu/mu_inf, mu_NS3D, rtol=0.003)
                
                mu_A = np.copy( mu_Suth_ref*(T/T_Suth_ref)**(3/2) * ((T_Suth_ref+S_Suth)/(T+S_Suth)) )
                mu_B = np.copy( C_Suth * T**(3/2) / (T + S_Suth) )
                np.testing.assert_allclose(mu_A, mu_B, rtol=1e-6) ## single precision
                
                np.testing.assert_allclose(mu, mu_A, rtol=0.003)
                np.testing.assert_allclose(mu, mu_B, rtol=0.003)
                
                ## !!! replace μ !!!
                if recalc_mu:
                    mu = np.copy( C_Suth * T**(3/2) / (T + S_Suth) )
                    if ('data/mu' in self):
                        del self['data/mu']
                    self.create_dataset('data/mu', data=mu.T, chunks=None)
                
                ## clear structured array from memory
                data = None ; del data
                
                ## derived values from base scalars
                a     = np.copy( np.sqrt( kappa * R * T )      )
                nu    = np.copy( mu / rho                      )
                umag  = np.copy( np.sqrt( u**2 + v**2 + w**2 ) )
                M     = np.copy( umag / np.sqrt(kappa * R * T) )
                
                T_tot   = np.copy( T   * (1 + (kappa-1)/2 * M**2)                    )
                p_tot   = np.copy( p   * (1 + (kappa-1)/2 * M**2)**(kappa/(kappa-1)) )
                rho_tot = np.copy( rho * (1 + (kappa-1)/2 * M**2)**(1/(kappa-1))     )
                
                ## write derived scalars
                self.create_dataset('data/a'       , data=a.T       , chunks=None)
                self.create_dataset('data/nu'      , data=nu.T      , chunks=None)
                self.create_dataset('data/umag'    , data=umag.T    , chunks=None)
                self.create_dataset('data/M'       , data=M.T       , chunks=None)
                self.create_dataset('data/T_tot'   , data=T_tot.T   , chunks=None)
                self.create_dataset('data/p_tot'   , data=p_tot.T   , chunks=None)
                self.create_dataset('data/rho_tot' , data=rho_tot.T , chunks=None)
        
        if fn_Re_fluct.exists(): ## Reynolds turbulent
            even_print('eas3 Re fluct',str(fn_Re_fluct.relative_to(Path())))
            with eas3(str(fn_Re_fluct),verbose=False) as f1:
                
                if (f1.t.shape[0]==1):
                    f1.total_avg_time = float(f1.t[0])
                else:
                    raise NotImplementedError
                
                ## duration over which avg was performed, iteration count and the sampling period of the avg
                Re_fluct_total_avg_time       = f1.total_avg_time
                Re_fluct_total_avg_iter_count = f1.total_avg_iter_count
                Re_fluct_dt                   = Re_fluct_total_avg_time/Re_fluct_total_avg_iter_count
                
                self.attrs['Re_fluct_total_avg_time'] = Re_fluct_total_avg_time
                self.attrs['Re_fluct_total_avg_iter_count'] = Re_fluct_total_avg_iter_count
                self.attrs['Re_fluct_dt'] = Re_fluct_dt
                
                ## assert grid,lchar are same
                if hasattr(self,'lchar') and hasattr(f1,'lchar'):
                    np.testing.assert_allclose(self.lchar, f1.lchar, rtol=1e-12)
                if hasattr(self,'x') and hasattr(f1,'x'):
                    np.testing.assert_allclose(self.x, f1.x*lchar, rtol=1e-12)
                if hasattr(self,'y') and hasattr(f1,'y'):
                    np.testing.assert_allclose(self.y, f1.y*lchar, rtol=1e-12)
                
                # ===
                
                if (f1.scalars != f1.attr_param):
                    raise AssertionError
                if (f1.ndim3!=1):
                    raise AssertionError
                
                if (f1.accuracy == f1.IEEES):
                    dtypes = [ np.float32 for _ in f1.scalars ]
                if (f1.accuracy == f1.IEEED):
                    dtypes = [ np.float64 for _ in f1.scalars ]
                else:
                    raise ValueError
                
                ## numpy structured array
                data = np.zeros( shape=(nx,ny), dtype={'names':f1.scalars,'formats':dtypes} )
                
                ## dict for name change
                dnc = {
                "r'r'":'rI_rI',
                "u'u'":'uI_uI',
                "v'v'":'vI_vI',
                "w'w'":'wI_wI',
                "T'T'":'TI_TI',
                "p'p'":'pI_pI',
                "mu'mu'":'muI_muI',
                "u'v'":'uI_vI',
                "u'w'":'uI_wI',
                "v'w'":'vI_wI',
                "u'T'":'uI_TI',
                "v'T'":'vI_TI',
                "w'T'":'wI_TI',
                "tau'_xx":'tauI_xx',
                "tau'_xy":'tauI_xy',
                "tau'_xz":'tauI_xz',
                "tau'_yy":'tauI_yy',
                "tau'_yz":'tauI_yz',
                "tau'_zz":'tauI_zz',
                }
                
                ## populate structured array from EAS3 binary data file
                progress_bar = tqdm(total=f1.nt*f1.npar, ncols=100, desc='import eas3 Re fluct', leave=False)
                for scalar in f1.attr_param:
                    if (scalar in dnc):
                        s_ = dnc[scalar]
                    else:
                        s_ = scalar
                    tqdm.write(even_print(f"{scalar} --> {s_}",f'({nx},{ny})',s=True))
                    for jj in range(f1.ndim2):
                        if f1.accuracy == f1.IEEES:
                            packet = struct.unpack('!'+str(f1.ndim1)+'f',f1.f.read(4*f1.ndim1))[:]
                        else:
                            packet = struct.unpack('!'+str(f1.ndim1)+'d',f1.f.read(8*f1.ndim1))[:]
                        data[scalar][:,jj] = packet
                    progress_bar.update()
                progress_bar.close()
                
                ## re-dimensionalize by characteristic freestream quantities
                for scalar in data.dtype.names:
                    if scalar in ["u'u'","v'v'","w'w'","u'v'","u'w'","v'w'",]:
                        data[scalar] *= U_inf**2
                    elif scalar in ["r'r'",]:
                        data[scalar] *= rho_inf**2
                    elif scalar in ["T'T'",]:
                        data[scalar] *= T_inf**2
                    elif scalar in ["p'p'",]:
                        data[scalar] *= rho_inf**2 * U_inf**4
                    elif scalar in ["mu'mu'",]:
                        data[scalar] *= mu_inf**2
                    elif scalar in ["u'T'","v'T'","w'T'",]:
                        data[scalar] *= U_inf * T_inf
                    elif scalar in ["tau'_xx","tau'_xy","tau'_xz","tau'_yy","tau'_yz","tau'_zz",]:
                        data[scalar] *= mu_inf * U_inf / lchar
                    else:
                        raise ValueError(f"condition needed for redimensionalizing '{scalar}'")
                
                ## write structured array to ZTMD
                for scalar in data.dtype.names:
                    self.create_dataset(f'data/{dnc[scalar]}', data=data[scalar].T, chunks=None)
                
                ## derived
                uI_uI_rms = np.copy( np.sqrt(       data["u'u'"]  )                         )
                vI_vI_rms = np.copy( np.sqrt(       data["v'v'"]  )                         )
                wI_wI_rms = np.copy( np.sqrt(       data["w'w'"]  )                         )
                uI_vI_rms = np.copy( np.sqrt(np.abs(data["u'v'"]) ) * np.sign(data["u'v'"]) )
                uI_wI_rms = np.copy( np.sqrt(np.abs(data["u'w'"]) ) * np.sign(data["u'w'"]) )
                vI_wI_rms = np.copy( np.sqrt(np.abs(data["v'w'"]) ) * np.sign(data["v'w'"]) )
                
                uI_TI_rms = np.copy( np.sqrt(np.abs(data["u'T'"]) ) * np.sign(data["u'T'"]) )
                vI_TI_rms = np.copy( np.sqrt(np.abs(data["v'T'"]) ) * np.sign(data["v'T'"]) )
                wI_TI_rms = np.copy( np.sqrt(np.abs(data["w'T'"]) ) * np.sign(data["w'T'"]) )
                
                rI_rI_rms   = np.copy( np.sqrt( data["r'r'"]   ) )
                TI_TI_rms   = np.copy( np.sqrt( data["T'T'"]   ) )
                pI_pI_rms   = np.copy( np.sqrt( data["p'p'"]   ) )
                muI_muI_rms = np.copy( np.sqrt( data["mu'mu'"] ) )
                
                M_rms = np.copy( uI_uI_rms / np.sqrt(kappa * R * T) )
                
                ## clear structured array from memory
                data = None ; del data
                
                self.create_dataset( 'data/uI_uI_rms' , data=uI_uI_rms.T , chunks=None )
                self.create_dataset( 'data/vI_vI_rms' , data=vI_vI_rms.T , chunks=None )
                self.create_dataset( 'data/wI_wI_rms' , data=wI_wI_rms.T , chunks=None )
                self.create_dataset( 'data/uI_vI_rms' , data=uI_vI_rms.T , chunks=None )
                self.create_dataset( 'data/uI_wI_rms' , data=uI_wI_rms.T , chunks=None )
                self.create_dataset( 'data/vI_wI_rms' , data=vI_wI_rms.T , chunks=None )
                
                self.create_dataset( 'data/uI_TI_rms' , data=uI_TI_rms.T , chunks=None )
                self.create_dataset( 'data/vI_TI_rms' , data=vI_TI_rms.T , chunks=None )
                self.create_dataset( 'data/wI_TI_rms' , data=wI_TI_rms.T , chunks=None )
                
                self.create_dataset( 'data/rI_rI_rms'   , data=rI_rI_rms.T   , chunks=None )
                self.create_dataset( 'data/TI_TI_rms'   , data=TI_TI_rms.T   , chunks=None )
                self.create_dataset( 'data/pI_pI_rms'   , data=pI_pI_rms.T   , chunks=None )
                self.create_dataset( 'data/muI_muI_rms' , data=muI_muI_rms.T , chunks=None )
                
                self.create_dataset( 'data/M_rms' , data=M_rms.T , chunks=None )
        
        if fn_Fv_mean.exists(): ## Favre mean
            even_print('eas3 Fv mean',str(fn_Fv_mean.relative_to(Path())))
            with eas3(str(fn_Fv_mean),verbose=False) as f1:
                
                if (f1.t.shape[0]==1):
                    f1.total_avg_time = float(f1.t[0])
                else:
                    raise NotImplementedError
                
                ## duration over which avg was performed, iteration count and the sampling period of the avg
                Fv_mean_total_avg_time       = f1.total_avg_time
                Fv_mean_total_avg_iter_count = f1.total_avg_iter_count
                Fv_mean_dt                   = Fv_mean_total_avg_time/Fv_mean_total_avg_iter_count
                
                self.attrs['Fv_mean_total_avg_time'] = Fv_mean_total_avg_time
                self.attrs['Fv_mean_total_avg_iter_count'] = Fv_mean_total_avg_iter_count
                self.attrs['Fv_mean_dt'] = Fv_mean_dt
                
                ## assert grid,lchar are same
                if hasattr(self,'lchar') and hasattr(f1,'lchar'):
                    np.testing.assert_allclose(self.lchar, f1.lchar, rtol=1e-12)
                if hasattr(self,'x') and hasattr(f1,'x'):
                    np.testing.assert_allclose(self.x, f1.x*lchar, rtol=1e-12)
                if hasattr(self,'y') and hasattr(f1,'y'):
                    np.testing.assert_allclose(self.y, f1.y*lchar, rtol=1e-12)
                
                # ===
                
                if (f1.scalars != f1.attr_param):
                    raise AssertionError
                if (f1.ndim3!=1):
                    raise AssertionError
                
                if (f1.accuracy == f1.IEEES):
                    dtypes = [ np.float32 for _ in f1.scalars ]
                if (f1.accuracy == f1.IEEED):
                    dtypes = [ np.float64 for _ in f1.scalars ]
                else:
                    raise ValueError
                
                ## numpy structured array
                data = np.zeros( shape=(nx,ny), dtype={'names':f1.scalars,'formats':dtypes} )
                
                ## dict for name change
                dnc = {
                'rho':'rho_Fv',
                'u':'u_Fv',
                'v':'v_Fv',
                'w':'w_Fv',
                'T':'T_Fv',
                'p':'p_Fv',
                'mu':'mu_Fv',
                'uu':'uu_Fv',
                'uv':'uv_Fv',
                }
                
                ## populate structured array from EAS3 binary data file
                progress_bar = tqdm(total=f1.nt*f1.npar, ncols=100, desc='import eas3 Fv mean', leave=False)
                for scalar in f1.attr_param:
                    if (scalar in dnc):
                        s_ = dnc[scalar]
                    else:
                        s_ = scalar
                    tqdm.write(even_print(f"{scalar} --> {s_}",f'({nx},{ny})',s=True))
                    for jj in range(f1.ndim2):
                        if f1.accuracy == f1.IEEES:
                            packet = struct.unpack('!'+str(f1.ndim1)+'f',f1.f.read(4*f1.ndim1))[:]
                        else:
                            packet = struct.unpack('!'+str(f1.ndim1)+'d',f1.f.read(8*f1.ndim1))[:]
                        data[scalar][:,jj] = packet
                    progress_bar.update()
                progress_bar.close()
                
                ## re-dimensionalize by characteristic freestream quantities
                for scalar in data.dtype.names:
                    if scalar in ["u","v","w",]:
                        data[scalar] *= U_inf
                    elif scalar in ["uu","uv",]:
                        data[scalar] *= U_inf**2
                    elif scalar in ["rho",]:
                        data[scalar] *= rho_inf
                    elif scalar in ["T",]:
                        data[scalar] *= T_inf
                    elif scalar in ["p",]:
                        data[scalar] *= rho_inf * U_inf**2
                    elif scalar in ["mu",]:
                        data[scalar] *= mu_inf
                    else:
                        raise ValueError(f"condition needed for redimensionalizing '{scalar}'")
                
                ## write
                for scalar in f1.attr_param:
                    self.create_dataset( f'data/{dnc[scalar]}' , data=data[scalar].T , chunks=None )
        
        if fn_Fv_fluct.exists(): ## Favre turbulent
            even_print('eas3 Fv fluct',str(fn_Fv_fluct.relative_to(Path())))
            with eas3(str(fn_Fv_fluct),verbose=False) as f1:
                
                if (f1.t.shape[0]==1):
                    f1.total_avg_time = float(f1.t[0])
                else:
                    raise NotImplementedError
                
                ## duration over which avg was performed, iteration count and the sampling period of the avg
                Fv_fluct_total_avg_time       = f1.total_avg_time
                Fv_fluct_total_avg_iter_count = f1.total_avg_iter_count
                Fv_fluct_dt                   = Fv_fluct_total_avg_time/Fv_fluct_total_avg_iter_count
                
                self.attrs['Fv_fluct_total_avg_time'] = Fv_fluct_total_avg_time
                self.attrs['Fv_fluct_total_avg_iter_count'] = Fv_fluct_total_avg_iter_count
                self.attrs['Fv_fluct_dt'] = Fv_fluct_dt
                
                ## assert grid,lchar are same
                if hasattr(self,'lchar') and hasattr(f1,'lchar'):
                    np.testing.assert_allclose(self.lchar, f1.lchar, rtol=1e-12)
                if hasattr(self,'x') and hasattr(f1,'x'):
                    np.testing.assert_allclose(self.x, f1.x*lchar, rtol=1e-12)
                if hasattr(self,'y') and hasattr(f1,'y'):
                    np.testing.assert_allclose(self.y, f1.y*lchar, rtol=1e-12)
                
                # ===
                
                if (f1.scalars != f1.attr_param):
                    raise AssertionError
                if (f1.ndim3!=1):
                    raise AssertionError
                
                if (f1.accuracy == f1.IEEES):
                    dtypes = [ np.float32 for _ in f1.scalars ]
                if (f1.accuracy == f1.IEEED):
                    dtypes = [ np.float64 for _ in f1.scalars ]
                else:
                    raise ValueError
                
                ## numpy structured array
                data = np.zeros( shape=(nx,ny), dtype={'names':f1.scalars,'formats':dtypes} )
                
                ## dict for name change
                dnc = {
                "r r''r''":'r_rII_rII',
                "r u''u''":'r_uII_uII',
                "r v''v''":'r_vII_vII',
                "r w''_w''":'r_wII_wII',
                "r T''T''":'r_TII_TII',
                "r p''p''":'r_pII_pII',
                "r mu''mu''":'r_muII_muII',
                "r u''v''":'r_uII_vII',
                "r u''w''":'r_uII_wII',
                "r w''v''":'r_vII_wII',
                "r u''T''":'r_uII_TII',
                "r v''T''":'r_vII_TII',
                "r w''T''":'r_wII_TII',
                }
                
                ## populate structured array from EAS3 binary data file
                progress_bar = tqdm(total=f1.nt*f1.npar, ncols=100, desc='import eas3 Fv fluct', leave=False)
                for scalar in f1.attr_param:
                    if (scalar in dnc):
                        s_ = dnc[scalar]
                    else:
                        s_ = scalar
                    tqdm.write(even_print(f"{scalar} --> {s_}",f'({nx},{ny})',s=True))
                    for jj in range(f1.ndim2):
                        if f1.accuracy == f1.IEEES:
                            packet = struct.unpack('!'+str(f1.ndim1)+'f',f1.f.read(4*f1.ndim1))[:]
                        else:
                            packet = struct.unpack('!'+str(f1.ndim1)+'d',f1.f.read(8*f1.ndim1))[:]
                        data[scalar][:,jj] = packet
                    progress_bar.update()
                progress_bar.close()
                
                ## re-dimensionalize by characteristic freestream quantities
                for scalar in data.dtype.names:
                    if scalar in ["r r''r''",]:
                        data[scalar] *= rho_inf**3
                    elif scalar in ["r u''u''","r v''v''","r w''w''","r w''_w''","r u''v''","r u''w''","r w''v''",]:
                        data[scalar] *= rho_inf * U_inf**2
                    elif scalar in ["r u''T''","r v''T''","r w''T''",]:
                        data[scalar] *= rho_inf * U_inf * T_inf
                    elif scalar in ["r mu''mu''",]:
                        data[scalar] *= rho_inf * mu_inf**2
                    elif scalar in ["r p''p''",]:
                        data[scalar] *= rho_inf * (rho_inf * U_inf**2)**2
                    elif scalar in ["r T''T''",]:
                        data[scalar] *= rho_inf * T_inf**2
                    else:
                        raise ValueError(f"condition needed for redimensionalizing '{scalar}'")
                
                ## write structured array to ZTMD
                for scalar in data.dtype.names:
                    self.create_dataset(f'data/{dnc[scalar]}', data=data[scalar].T, chunks=None)
                
                ## derived
                r_uII_uII_rms = np.copy( np.sqrt(       data["r u''u''"]  )                             )
                r_vII_vII_rms = np.copy( np.sqrt(       data["r v''v''"]  )                             )
                r_wII_wII_rms = np.copy( np.sqrt(       data["r w''_w''"] )                             )
                r_uII_vII_rms = np.copy( np.sqrt(np.abs(data["r u''v''"]) ) * np.sign(data["r u''v''"]) )
                r_uII_wII_rms = np.copy( np.sqrt(np.abs(data["r u''w''"]) ) * np.sign(data["r u''w''"]) )
                r_vII_wII_rms = np.copy( np.sqrt(np.abs(data["r w''v''"]) ) * np.sign(data["r w''v''"]) )
                ## ... ρ·u″T″
                
                self.create_dataset( 'data/r_uII_uII_rms' , data=r_uII_uII_rms.T , chunks=None )
                self.create_dataset( 'data/r_vII_vII_rms' , data=r_vII_vII_rms.T , chunks=None )
                self.create_dataset( 'data/r_wII_wII_rms' , data=r_wII_wII_rms.T , chunks=None )
                self.create_dataset( 'data/r_uII_vII_rms' , data=r_uII_vII_rms.T , chunks=None )
                self.create_dataset( 'data/r_uII_wII_rms' , data=r_uII_wII_rms.T , chunks=None )
                self.create_dataset( 'data/r_vII_wII_rms' , data=r_vII_wII_rms.T , chunks=None )
                ## ... ρ·u″T″
                
                ## clear structured array from memory
                data = None ; del data
        
        if fn_turb_budget.exists(): ## turbulent budget
            even_print('eas3 turb budget',str(fn_turb_budget.relative_to(Path())))
            with eas3(str(fn_turb_budget),verbose=False) as f1:
                
                if (f1.t.shape[0]==1):
                    f1.total_avg_time = float(f1.t[0])
                else:
                    raise NotImplementedError
                
                ## duration over which avg was performed, iteration count and the sampling period of the avg
                turb_budget_total_avg_time       = f1.total_avg_time
                turb_budget_total_avg_iter_count = f1.total_avg_iter_count
                turb_budget_dt                   = turb_budget_total_avg_time/turb_budget_total_avg_iter_count
                
                self.attrs['turb_budget_total_avg_time'] = turb_budget_total_avg_time
                self.attrs['turb_budget_total_avg_iter_count'] = turb_budget_total_avg_iter_count
                self.attrs['turb_budget_dt'] = turb_budget_dt
                
                ## assert grid,lchar are same
                if hasattr(self,'lchar') and hasattr(f1,'lchar'):
                    np.testing.assert_allclose(self.lchar, f1.lchar, rtol=1e-12)
                if hasattr(self,'x') and hasattr(f1,'x'):
                    np.testing.assert_allclose(self.x, f1.x*lchar, rtol=1e-12)
                if hasattr(self,'y') and hasattr(f1,'y'):
                    np.testing.assert_allclose(self.y, f1.y*lchar, rtol=1e-12)
                
                # ===
                
                if (f1.scalars != f1.attr_param):
                    raise AssertionError
                if (f1.ndim3!=1):
                    raise AssertionError
                
                if (f1.accuracy == f1.IEEES):
                    dtypes = [ np.float32 for _ in f1.scalars ]
                if (f1.accuracy == f1.IEEED):
                    dtypes = [ np.float64 for _ in f1.scalars ]
                else:
                    raise ValueError
                
                ## numpy structured array
                names_ = [ s for s in f1.scalars if ( 'restart' not in s ) ]
                data = np.zeros( shape=(nx,ny), dtype={'names':names_,'formats':dtypes} )
                
                ## dict for name change
                dnc = {
                "prod.":'production',
                "dis.":'dissipation',
                "t-transp.":'turb_transport',
                "v-diff.":'visc_diffusion',
                "p-diff.":'p_diffusion',
                "p-dilat.":'p_dilatation',
                "rho-terms":'rho_terms',
                }
                
                ## populate structured array from EAS3 binary data file
                progress_bar = tqdm(total=7, ncols=100, desc='import eas3 turb budget', leave=False)
                for scalar in ["prod.","dis.","t-transp.","v-diff.","p-diff.","p-dilat.","rho-terms",]:
                    if (scalar in dnc):
                        s_ = dnc[scalar]
                    else:
                        s_ = scalar
                    tqdm.write(even_print(f"{scalar} --> {s_}",f'({nx},{ny})',s=True))
                    for jj in range(f1.ndim2):
                        if f1.accuracy == f1.IEEES:
                            packet = struct.unpack('!'+str(f1.ndim1)+'f',f1.f.read(4*f1.ndim1))[:]
                        else:
                            packet = struct.unpack('!'+str(f1.ndim1)+'d',f1.f.read(8*f1.ndim1))[:]
                        data[scalar][:,jj] = packet
                    progress_bar.update()
                progress_bar.close()
                
                ## re-dimensionalize by characteristic freestream quantities
                for scalar in data.dtype.names:
                    if scalar in ["prod.","t-transp.","p-diff.","p-dilat.","rho-terms",]:
                        data[scalar] *= U_inf**3 * rho_inf / lchar
                    elif scalar in ["dis.","v-diff.",]:
                        data[scalar] *= U_inf**2 * mu_inf / lchar**2
                    else:
                        raise ValueError(f"condition needed for redimensionalizing '{scalar}'")
                
                ## write structured array to ZTMD
                for scalar in data.dtype.names:
                    self.create_dataset(f'data/{dnc[scalar]}', data=data[scalar].T, chunks=None)
                
                ## derived
                dissipation = np.copy( data['dis.'] )
                Kolm_len = (nu**3 / np.abs(dissipation))**(1/4)
                self.create_dataset('data/Kolm_len', data=Kolm_len.T, chunks=None)
                
                ## clear structured array from memory
                data = None ; del data
        
        self.get_header(verbose=True)
        if verbose: print(72*'-')
        if verbose: print('total time : turbx.ztmd.import_data_eas3() : %s'%format_time_string((timeit.default_timer() - t_start_func)))
        if verbose: print(72*'-')
        
        return
    
    def export_dict(self,**kwargs):
        '''
        pull all data from HDF5 container into memory and pack it into a dictionary
        - convenient for multi-case plotting scripts
        '''
        verbose   = kwargs.get('verbose',True)
        dsets     = kwargs.get('dsets',None)
        
        dd = {} ## the dict to return
        
        ## class-level ZTMD attrs
        attr_exclude_list = ['rank','comm','n_ranks','usingmpi','open_mode',
                             '_libver','_id','requires_wall_norm_interp',
                             'mod_avail_tqdm']
        for attr, val in self.__dict__.items():
            if (attr not in attr_exclude_list):
                
                ## throw error if not a routine type
                if isinstance(val, (int,np.int64,np.int32,float,str,dict,list,tuple,np.ndarray,bool,np.bool_,)):
                    pass
                elif (val is None):
                    pass
                else:
                    print(attr)
                    print(type(val))
                    raise TypeError
                
                dd[attr] = val
        
        ## HDF5 File Group attrs
        for attr, val in self.attrs.items():
            if (attr not in dd.keys()):
                dd[attr] = val
        
        ## Group: dims/
        for dsn in self['dims']:
            if (dsn not in dd.keys()):
                ds = self[f'dims/{dsn}']
                if (ds.ndim==0):
                    dd[dsn] = ds[()]
                elif (ds.ndim>0):
                    dd[dsn] = np.copy(ds[()])
                else:
                    raise ValueError
            else:
                #print(dsn)
                pass
        
        ## Group: data/
        for dsn in self['data']:
            if (dsn not in dd.keys()):
                if (dsets is None) or (dsn in dsets):
                    ds = self[f'data/{dsn}']
                    if (ds.ndim==2):
                        dd[dsn] = np.copy(ds[()].T)
                    else:
                        raise ValueError
            else:
                #print(dsn)
                pass
        
        ## Group: data_1Dx/
        for dsn in self['data_1Dx']:
            if (dsn not in dd.keys()):
                #if (dsets is not None) and (dsn in dsets):
                ds = self[f'data_1Dx/{dsn}']
                if (ds.ndim==1) or (ds.ndim==2):
                    dd[dsn] = np.copy(ds[()])
                else:
                    raise ValueError
            else:
                #print(dsn)
                pass
        
        if verbose:
            print(f'>>> {self.fname}')
        
        return dd
    
    def make_xdmf(self):
        '''
        generate an XDMF/XMF2 from ZTMD for processing with Paraview
        -----
        --> https://www.xdmf.org/index.php/XDMF_Model_and_Format
        '''
        
        if (self.rank==0):
            verbose = True
        else:
            verbose = False
        
        #makeVectors = kwargs.get('makeVectors',True) ## write vectors (e.g. velocity, vorticity) to XDMF
        #makeTensors = kwargs.get('makeTensors',True) ## write 3x3 tensors (e.g. stress, strain) to XDMF
        
        fname_path            = os.path.dirname(self.fname)
        fname_base            = os.path.basename(self.fname)
        fname_root, fname_ext = os.path.splitext(fname_base)
        fname_xdmf_base       = fname_root+'.xmf2'
        fname_xdmf            = os.path.join(fname_path, fname_xdmf_base)
        
        if verbose: print('\n'+'ztmd.make_xdmf()'+'\n'+72*'-')
        
        dataset_precision_dict = {} ## holds dtype.itemsize ints i.e. 4,8
        dataset_numbertype_dict = {} ## holds string description of dtypes i.e. 'Float','Integer'
        
        # === 1D coordinate dimension vectors --> get dtype.name
        for scalar in ['x','y','r','theta']:
            if ('dims/'+scalar in self):
                data = self['dims/'+scalar]
                dataset_precision_dict[scalar] = data.dtype.itemsize
                if (data.dtype.name=='float32') or (data.dtype.name=='float64'):
                    dataset_numbertype_dict[scalar] = 'Float'
                elif (data.dtype.name=='int8') or (data.dtype.name=='int16') or (data.dtype.name=='int32') or (data.dtype.name=='int64'):
                    dataset_numbertype_dict[scalar] = 'Integer'
                else:
                    raise ValueError('dtype not recognized, please update script accordingly')
        
        ## refresh header
        self.get_header(verbose=False)
        
        for scalar in self.scalars:
            data = self['data/%s'%scalar]
            
            dataset_precision_dict[scalar] = data.dtype.itemsize
            txt = '%s%s%s%s%s'%(data.dtype.itemsize, ' '*(4-len(str(data.dtype.itemsize))), data.dtype.name, ' '*(10-len(str(data.dtype.name))), data.dtype.byteorder)
            if verbose: even_print(scalar, txt)
            
            if (data.dtype.name=='float32') or (data.dtype.name=='float64'):
                dataset_numbertype_dict[scalar] = 'Float'
            elif (data.dtype.name=='int8') or (data.dtype.name=='int16') or (data.dtype.name=='int32') or (data.dtype.name=='int64'):
                dataset_numbertype_dict[scalar] = 'Integer'
            else:
                raise TypeError('dtype not recognized, please update script accordingly')
        
        if verbose: print(72*'-')
        
        # === write to .xdmf/.xmf2 file
        if (self.rank==0):
            
            if not os.path.isfile(fname_xdmf): ## if doesnt exist...
                Path(fname_xdmf).touch() ## touch XDMF file
                perms_h5 = oct(os.stat(self.fname).st_mode)[-3:] ## get permissions of ZTMD file
                os.chmod(fname_xdmf, int(perms_h5, base=8)) ## change permissions of XDMF file
            
            #with open(fname_xdmf,'w') as xdmf:
            with io.open(fname_xdmf,'w',newline='\n') as xdmf:
                
                xdmf_str='''
                         <?xml version="1.0" encoding="utf-8"?>
                         <!DOCTYPE Xdmf SYSTEM "Xdmf.dtd" []>
                         <Xdmf xmlns:xi="http://www.w3.org/2001/XInclude" Version="2.0">
                           <Domain>
                         '''
                
                xdmf.write(textwrap.indent(textwrap.dedent(xdmf_str.strip('\n')), 0*' '))
                
                if self.curvilinear:
                    xdmf_str=f'''
                            <Topology TopologyType="3DSMesh" NumberOfElements="{self.ny:d} {self.nx:d}"/>
                            <Geometry GeometryType="X_Y_Z">
                            <DataItem Dimensions="{self.nx:d} {self.ny:d}" NumberType="{dataset_numbertype_dict['x']}" Precision="{dataset_precision_dict['x']:d}" Format="HDF">
                                {fname_base}:/dims/{'x'}
                            </DataItem>
                            <DataItem Dimensions="{self.nx:d} {self.ny:d}" NumberType="{dataset_numbertype_dict['y']}" Precision="{dataset_precision_dict['y']:d}" Format="HDF">
                                {fname_base}:/dims/{'y'}
                            </DataItem>
                            </Geometry>
                            '''
                else:
                    xdmf_str=f'''
                            <Topology TopologyType="3DRectMesh" NumberOfElements="1 {self.ny:d} {self.nx:d}"/>
                            <Geometry GeometryType="VxVyVz">
                            <DataItem Dimensions="{self.nx:d}" NumberType="{dataset_numbertype_dict['x']}" Precision="{dataset_precision_dict['x']:d}" Format="HDF">
                                {fname_base}:/dims/{'x'}
                            </DataItem>
                            <DataItem Dimensions="{self.ny:d}" NumberType="{dataset_numbertype_dict['y']}" Precision="{dataset_precision_dict['y']:d}" Format="HDF">
                                {fname_base}:/dims/{'y'}
                            </DataItem>
                            <DataItem Dimensions="1" Format="XML">
                                0.0
                            </DataItem>
                            </Geometry>
                            '''
                    
                xdmf.write(textwrap.indent(textwrap.dedent(xdmf_str.strip('\n')), 4*' '))
                
                # ===
                
                xdmf_str='''
                         <!-- ==================== time series ==================== -->
                         '''
                
                xdmf.write(textwrap.indent(textwrap.dedent(xdmf_str.strip('\n')), 4*' '))
                
                # === the time series
                
                xdmf_str='''
                         <Grid Name="TimeSeries" GridType="Collection" CollectionType="Temporal">
                         '''
                
                xdmf.write(textwrap.indent(textwrap.dedent(xdmf_str.strip('\n')), 4*' '))
                
                for ti in range(len(self.t)):
                    
                    dset_name = 'ts_%08d'%ti
                    
                    xdmf_str='''
                             <!-- ============================================================ -->
                             '''
                    
                    xdmf.write(textwrap.indent(textwrap.dedent(xdmf_str.strip('\n')), 6*' '))
                    
                    # ===
                    
                    xdmf_str=f'''
                             <Grid Name="{dset_name}" GridType="Uniform">
                               <Time TimeType="Single" Value="{self.t[ti]:0.8E}"/>
                               <Topology Reference="/Xdmf/Domain/Topology[1]" />
                               <Geometry Reference="/Xdmf/Domain/Geometry[1]" />
                             '''
                    
                    xdmf.write(textwrap.indent(textwrap.dedent(xdmf_str.strip('\n')), 6*' '))
                    
                    # === .xdmf : <Grid> per 2D coordinate array
                    
                    if self.curvilinear:
                        
                        for scalar in ['x','y','r','theta']:
                            
                            dset_hf_path = 'dims/%s'%scalar
                            
                            if (dset_hf_path in self):
                                
                                scalar_name = scalar
                                
                                xdmf_str=f'''
                                        <!-- ===== scalar : {scalar} ===== -->
                                        <Attribute Name="{scalar_name}" AttributeType="Scalar" Center="Node">
                                        <DataItem Dimensions="{self.ny:d} {self.nx:d}" NumberType="{dataset_numbertype_dict[scalar]}" Precision="{dataset_precision_dict[scalar]:d}" Format="HDF">
                                            {fname_base}:/{dset_hf_path}
                                        </DataItem>
                                        </Attribute>
                                        '''
                                
                                xdmf.write(textwrap.indent(textwrap.dedent(xdmf_str.strip('\n')), 8*' '))
                    
                    # === .xdmf : <Grid> per scalar
                    
                    for scalar in self.scalars:
                        
                        dset_hf_path = 'data/%s'%scalar
                        
                        scalar_name = scalar
                        
                        if self.curvilinear:
                            xdmf_str=f'''
                                    <!-- ===== scalar : {scalar} ===== -->
                                    <Attribute Name="{scalar_name}" AttributeType="Scalar" Center="Node">
                                    <DataItem Dimensions="{self.ny:d} {self.nx:d}" NumberType="{dataset_numbertype_dict[scalar]}" Precision="{dataset_precision_dict[scalar]:d}" Format="HDF">
                                        {fname_base}:/{dset_hf_path}
                                    </DataItem>
                                    </Attribute>
                                    '''
                        else:
                            xdmf_str=f'''
                                    <!-- ===== scalar : {scalar} ===== -->
                                    <Attribute Name="{scalar_name}" AttributeType="Scalar" Center="Node">
                                    <DataItem Dimensions="1 {self.ny:d} {self.nx:d}" NumberType="{dataset_numbertype_dict[scalar]}" Precision="{dataset_precision_dict[scalar]:d}" Format="HDF">
                                        {fname_base}:/{dset_hf_path}
                                    </DataItem>
                                    </Attribute>
                                    '''
                        
                        xdmf.write(textwrap.indent(textwrap.dedent(xdmf_str.strip('\n')), 8*' '))
                    
                    # === .xdmf : <Grid> per scalar (cell-centered values)
                    
                    if ('data_cells' in self):
                        scalars_cells = list(self['data_cells'].keys())
                        for scalar in scalars_cells:
                            
                            dset_hf_path = 'data_cells/%s'%scalar
                            dset = self[dset_hf_path]
                            dset_precision = dset.dtype.itemsize
                            scalar_name = scalar
                            
                            if (dset.dtype.name=='float32') or (dset.dtype.name=='float64'):
                                dset_numbertype = 'Float'
                            elif (data.dtype.name=='int8') or (data.dtype.name=='int16') or (data.dtype.name=='int32') or (data.dtype.name=='int64'):
                                dset_numbertype = 'Integer'
                            else:
                                raise TypeError('dtype not recognized, please update script accordingly')
                            
                            xdmf_str=f'''
                                     <!-- ===== scalar : {scalar} ===== -->
                                     <Attribute Name="{scalar_name}" AttributeType="Scalar" Center="Cell">
                                       <DataItem Dimensions="{(self.ny-1):d} {(self.nx-1):d}" NumberType="{dset_numbertype}" Precision="{dset_precision:d}" Format="HDF">
                                         {fname_base}:/{dset_hf_path}
                                       </DataItem>
                                     </Attribute>
                                     '''
                            
                            xdmf.write(textwrap.indent(textwrap.dedent(xdmf_str.strip('\n')), 8*' '))
                    
                    xdmf_str='''
                             <!-- ===== end scalars ===== -->
                             '''
                    xdmf.write(textwrap.indent(textwrap.dedent(xdmf_str.strip('\n')), 8*' '))
                    
                    # === .xdmf : end Grid for this timestep
                    
                    xdmf_str='''
                             </Grid>
                             '''
                    xdmf.write(textwrap.indent(textwrap.dedent(xdmf_str.strip('\n')), 6*' '))
                
                # ===
                
                xdmf_str='''
                             </Grid>
                           </Domain>
                         </Xdmf>
                         '''
                xdmf.write(textwrap.indent(textwrap.dedent(xdmf_str.strip('\n')), 0*' '))
        
        if verbose: print('--w-> %s'%fname_xdmf_base)
        return
    
    # ==================================================================
    # External attachments
    # ==================================================================
    
    def calc_gradients(self, acc=6, edge_stencil='full', **kwargs):
        return _calc_gradients(self, acc=acc, edge_stencil=edge_stencil, **kwargs)
    
    def calc_psvel(self, **kwargs):
        return _calc_psvel(self, **kwargs)
    
    def calc_wall_quantities(self, acc=6, edge_stencil='full', **kwargs):
        return _calc_wall_quantities(self, acc=acc, edge_stencil=edge_stencil, **kwargs)
    
    def calc_bl_edge(self, **kwargs):
        return _calc_bl_edge(self, **kwargs)
    
    def calc_bl_edge_quantities(self, **kwargs):
        return _calc_bl_edge_quantities(self, **kwargs)
    
    def calc_d99(self, **kwargs):
        return _calc_d99(self, **kwargs)
    
    def calc_d99_quantities(self, **kwargs):
        return _calc_d99_quantities(self, **kwargs)
    
    def calc_bl_integral_quantities(self, **kwargs):
        return _calc_bl_integral_quantities(self, **kwargs)
    
    def calc_wake_parameter(self, **kwargs):
        return _calc_wake_parameter(self, **kwargs)
    
    def calc_VDII(self, **kwargs):
        return _calc_VDII(self, **kwargs)
    
    def calc_peak_tauI(self, **kwargs):
        return _calc_peak_tauI(self, **kwargs)
    
    def calc_comp_trafo(self, *args, **kwargs):
        return _calc_comp_trafo(self, *args, **kwargs)
    
    # ==================================================================
    # External attachments -- curvilinear
    # ==================================================================
    
    def calc_s_wall(self,**kwargs):
        return _calc_s_wall(self,**kwargs)
    
    def add_geom_data(self, fn_dat=None, **kwargs):
        return _add_geom_data(self, fn_dat=fn_dat, **kwargs)
    
    def add_csys_vecs_xy(self, fn_dat=None, **kwargs):
        return _add_csys_vecs_xy(self, fn_dat=fn_dat, **kwargs)
    
    def calc_vel_tangnorm(self, **kwargs):
        return _calc_vel_tangnorm(self, **kwargs)
    
    def calc_vel_tangnorm_mean_removed(self, **kwargs):
        return _calc_vel_tangnorm_mean_removed(self, **kwargs)
    
    # ==================================================================
    
    def post_TBL(self,acc=6,edge_stencil='full'):
        '''
        A wrapper for post-processing TBL ZTMD files
        '''
        
        self.calc_gradients(acc=acc, edge_stencil=edge_stencil, favre=True)
        self.calc_psvel()
        self.calc_wall_quantities(acc=acc, edge_stencil=edge_stencil)
        
        self.calc_bl_edge(method='vorticity', epsilon=5e-5, ongrid=True, acc=acc)
        self.calc_bl_edge_quantities()
        self.calc_d99(method='psvel', interp_kind='cubic')
        self.calc_d99_quantities(interp_kind='cubic')
        self.calc_bl_integral_quantities(interp_kind='cubic')
        
        self.calc_VDII(adiabatic=True)
        self.calc_comp_trafo(schemes=['VD','VIPL','TL','GFM'])
        
        self.calc_wake_parameter(k=0.384,B=4.173)
        self.calc_peak_tauI()
        self.make_xdmf()
        
        return
