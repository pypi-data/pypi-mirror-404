import io
import os
import re
import shutil
import subprocess
import sys
import textwrap
import time
import timeit
import types
from pathlib import Path

import h5py
import numpy as np
from mpi4py import MPI
from tqdm import tqdm

from .eas4 import eas4
from .h5 import h5_chunk_sizer, h5_ds_force_allocate_chunks
from .rgd_lambda2 import _calc_lambda2
from .rgd_mean import _calc_mean
from .rgd_xpln_ccor import _calc_ccor_xpln
from .rgd_xpln_coh import _calc_wall_coh_xpln
from .rgd_xpln_mean_dim import _add_mean_dimensional_data_xpln
from .rgd_xpln_spectrum import _calc_turb_cospectrum_xpln
from .rgd_xpln_stats import _calc_statistics_xpln
from .rgd_xpln_turb_budget import _calc_turb_budget_xpln
from .utils import even_print, format_time_string

# ======================================================================

class rgd(h5py.File):
    '''
    Rectilinear Grid Data (RGD)
    ---------------------------
    - super()'ed h5py.File class
    - 4D dataset storage
    - dimension coordinates are 4x 1D arrays defining [x,y,z,t] 
    
    to clear:
    ---------
    > os.system('h5clear -s tmp.h5')
    > hf = h5py.File('tmp.h5', 'r')
    > hf.close()
    
    Structure
    ---------
    
    rgd.h5
    │
    ├── dims/ --> 1D
    │   └── x
    │   └── y
    │   └── z
    │   └── t
    │
    └── data/<<scalar>> --> 4D [t,z,y,x]
    
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
            raise ValueError('EAS4 files should not be opened with turbx.rgd()')
        
        ## check if none-None communicator, but no driver='mpio'
        if ('comm' in kwargs) and (kwargs['comm'] is not None) and ('driver' not in kwargs):
            raise ValueError("comm is provided as not None, but driver='mpio' not provided")
        
        ## determine if using mpi
        if ('driver' in kwargs) and (kwargs['driver']=='mpio'):
            if ('comm' not in kwargs):
                raise ValueError("if driver='mpio', then comm should be provided")
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
            if ('comm' in kwargs):
                del kwargs['comm']
        
        ## rgd() unique kwargs (not h5py.File kwargs) --> pop() rather than get()
        stripe_count   = kwargs.pop('stripe_count'   , 16    )
        stripe_size_mb = kwargs.pop('stripe_size_mb' , 2     )
        perms          = kwargs.pop('perms'          , '640' )
        no_indep_rw    = kwargs.pop('no_indep_rw'    , False )
        
        if not isinstance(stripe_count, int):
            raise ValueError('stripe_count must be int')
        if not isinstance(stripe_size_mb, int):
            raise ValueError('stripe_size_mb must be int')
        if not isinstance(perms, str) or len(perms)!=3 or not re.fullmatch(r'\d{3}',perms):
            raise ValueError("perms must be 3-digit string like '660'")
        
        ## if not using MPI, remove 'driver' and 'comm' from kwargs
        if ( not self.usingmpi ) and ('driver' in kwargs):
            kwargs.pop('driver')
        if ( not self.usingmpi ) and ('comm' in kwargs):
            kwargs.pop('comm')
        
        ## | mpiexec --mca io romio321 -n $NP python3 ...
        ## | mpiexec --mca io ompio -n $NP python3 ...
        ## | ompi_info --> print ompi settings (grep 'MCA io' for I/O opts)
        ## | export ROMIO_FSTYPE_FORCE="lustre:" --> force Lustre driver over UFS when using ROMIO
        ## | export ROMIO_FSTYPE_FORCE="ufs:"
        ## | export ROMIO_PRINT_HINTS=1 --> show available hints
        ##
        ## https://doku.lrz.de/best-practices-hints-and-optimizations-for-io-10747318.html
        ##
        ## ## Using OMPIO
        ## export OMPI_MCA_sharedfp=^lockedfile,individual
        ## mpiexec --mca io ompio -n $NP python3 script.py
        ##
        ## ## Using Cray MPICH
        ## to print ROMIO hints : export MPICH_MPIIO_HINTS_DISPLAY=1
        
        ## set MPI hints, passed through 'mpi_info' dict
        if self.usingmpi:
            if ('info' in kwargs):
                self.mpi_info = kwargs['info']
            else:
                mpi_info = MPI.Info.Create()
                
                ## ROMIO -- data sieving & collective buffering
                mpi_info.Set('romio_ds_write' , 'disable'   ) ## ds = data sieving
                mpi_info.Set('romio_ds_read'  , 'disable'   )
                #mpi_info.Set('romio_cb_read'  , 'automatic' ) ## cb = collective buffering
                #mpi_info.Set('romio_cb_write' , 'automatic' )
                mpi_info.Set('romio_cb_read'  , 'enable' ) ## cb = collective buffering
                mpi_info.Set('romio_cb_write' , 'enable' )
                
                ## ROMIO -- collective buffer size
                mpi_info.Set('cb_buffer_size' , str(int(round(1*1024**3))) ) ## 1 [GB]
                
                ## ROMIO -- force collective I/O
                if no_indep_rw:
                    mpi_info.Set('romio_no_indep_rw' , 'true' )
                
                ## ROMIO -- N Aggregators
                #mpi_info.Set('cb_nodes' , str(min(16,self.n_ranks//2)) )
                mpi_info.Set('cb_nodes' , str(min(16,self.n_ranks)) )
                
                ## add to kwargs to be passed to h5py.File() at super() call
                kwargs['info'] = mpi_info
                self.mpi_info = mpi_info
        
        # === HDF5 tuning factors (independent of MPI I/O driver)
        
        ## rdcc_w0 : preemption policy (weight) for HDF5's raw data chunk cache
        ## - influences how HDF5 evicts chunks from the per-process chunk cache
        ## - 1.0 favors retaining fully-read chunks (good for read-heavy access)
        ## - 0.0 favors recently-used chunks (better for partial writes)
        if ('rdcc_w0' not in kwargs):
            kwargs['rdcc_w0'] = 0.75
        
        ## rdcc_nbytes : maximum total size of the HDF5 raw chunk cache per dataset per process
        if ('rdcc_nbytes' not in kwargs):
            kwargs['rdcc_nbytes'] = int(1*1024**3) ## 1 [GB]
        
        ## rdcc_nslots : number of hash table slots in the raw data chunk cache
        ## - should be ~= ( rdcc_nbytes / chunk size )
        if ('rdcc_nslots' not in kwargs):
            #kwargs['rdcc_nslots'] = 16381 ## prime
            kwargs['rdcc_nslots'] = kwargs['rdcc_nbytes'] // (2*1024**2) ## assume 2 [MB] chunks
            #kwargs['rdcc_nslots'] = kwargs['rdcc_nbytes'] // (128*1024**2) ## assume 128 [MB] chunks
        
        ## rgd() unique kwargs (not h5py.File kwargs) --> pop() rather than get()
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
                                  r       : Read only, file must exist
                                  r+      : Read/write, file must exist
                                  w       : Create file, truncate if exists
                                  w- or x : Create file, fail if exists
                                  a       : Read/write if exists, create otherwise
                                  
                                  or use force=True arg:
                                  
                                  >>> with rgd(<<fname>>,'w',force=True) as f:
                                  >>>     ...
                                  '''
                print(textwrap.indent(textwrap.dedent(openModeInfoStr), 2*' ').strip('\n'))
                print(72*'-'+'\n')
                sys.stdout.flush()
            
            if (self.comm is not None):
                self.comm.Barrier()
            raise FileExistsError
        
        ## if file open mode is 'w'
        ## --> <delete>, touch, chmod, stripe
        if (self.open_mode == 'w'):
            if (self.rank==0):
                if os.path.isfile(self.fname): ## if the file exists, delete it
                    os.remove(self.fname)
                    time.sleep(1.)
                Path(self.fname).touch() ## touch a new file
                time.sleep(1.)
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
        super(rgd, self).__init__(*args, **kwargs)
        self.get_header(verbose=verbose)
        return
    
    def get_header(self,**kwargs):
        '''
        Helper for __init__
        Read attributes of RGD class instance & attach
        '''
        
        verbose = kwargs.get('verbose',True)
        
        if (self.rank!=0):
            verbose=False
        
        # === attrs
        
        if ('duration_avg' in self.attrs.keys()):
            self.duration_avg = self.attrs['duration_avg']
        # if ('rectilinear' in self.attrs.keys()):
        #     self.rectilinear = self.attrs['rectilinear']
        # if ('curvilinear' in self.attrs.keys()):
        #     self.curvilinear = self.attrs['curvilinear']
        
        ## these should be set in the (init_from_() funcs)
        if ('fclass' in self.attrs.keys()):
            self.fclass = self.attrs['fclass'] ## 'rgd','cgd',...
        if ('fsubtype' in self.attrs.keys()):
            self.fsubtype = self.attrs['fsubtype'] ## 'unsteady','mean','prime',...
        
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
                setattr(self, key, self.attrs[key]) ## Attach to rgd() instance
        
        ## Read,attach -- derived attributes
        for key in header_attr_keys_derived:
            if key in self.attrs:
                setattr(self, key, self.attrs[key]) ## Attach to rgd() instance
        
        ## Check derived
        if all([ hasattr(self,key) for key in header_attr_keys ]): ## Has all base attrs
            
            cc = types.SimpleNamespace() ## Temporary obj
            
            ## Re-calculate derived attrs for assertion
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
            
            ## (1) Assert that re-calculated derived attrs are equal to HDF5 top-level attrs of same name
            ## (2) If for some reason a derived attribute was not cached in HDF5, then
            ##      attach the re-calculated value silently to self
            for key in header_attr_keys_derived:
                if hasattr(cc,key):
                    if hasattr(self,key):
                        np.testing.assert_allclose(
                            getattr(self,key),
                            getattr(cc,key),
                            rtol=1e-8,
                            atol=1e-8,
                            )
                    else:
                        setattr(self,key,getattr(cc, key))
            
            #if verbose: print(72*'-')
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
            if verbose: print(72*'-')
            #if verbose: print(72*'-'+'\n')
            
            ## Pack & attach a udef dict for convenience
            udef_keys = [
                'Ma','Re','Pr','kappa','R','p_inf','T_inf',
                'S_Suth','mu_Suth_ref','T_Suth_ref',
                'C_Suth','mu_inf','rho_inf','nu_inf',
                'a_inf','U_inf','cp','cv','recov_fac','Taw',
                'lchar','tchar','uchar','M_inf',
                'p_tot_inf','T_tot_inf','rho_tot_inf',
                ]
            self.udef = {}
            for key in udef_keys:
                if hasattr(self,key):
                    self.udef[key] = getattr(self,key)
        
        # === Coordinate vectors
        
        if all([('dims/x' in self),('dims/y' in self),('dims/z' in self)]):
            
            x   = self.x   = np.copy(self['dims/x'][()])
            y   = self.y   = np.copy(self['dims/y'][()])
            z   = self.z   = np.copy(self['dims/z'][()])
            nx  = self.nx  = x.size
            ny  = self.ny  = y.size
            nz  = self.nz  = z.size
            ngp = self.ngp = nx*ny*nz
            
            #if verbose: print(72*'-')
            if verbose: even_print('nx', '%i'%nx )
            if verbose: even_print('ny', '%i'%ny )
            if verbose: even_print('nz', '%i'%nz )
            if verbose: even_print('ngp', '%i'%ngp )
            if verbose: print(72*'-')
            
            if verbose: even_print('x_min', '%0.2f'%x.min())
            if verbose: even_print('x_max', '%0.2f'%x.max())
            if (self.nx>2):
                if verbose: even_print('dx begin : end', '%0.3E : %0.3E'%( (x[1]-x[0]), (x[-1]-x[-2]) ))
            if verbose: even_print('y_min', '%0.2f'%y.min())
            if verbose: even_print('y_max', '%0.2f'%y.max())
            if (self.ny>2):
                if verbose: even_print('dy begin : end', '%0.3E : %0.3E'%( (y[1]-y[0]), (y[-1]-y[-2]) ))
            if verbose: even_print('z_min', '%0.2f'%z.min())
            if verbose: even_print('z_max', '%0.2f'%z.max())
            if (self.nz>2):
                if verbose: even_print('dz begin : end', '%0.3E : %0.3E'%( (z[1]-z[0]), (z[-1]-z[-2]) ))
            #if verbose: print(72*'-'+'\n')
            if verbose: print(72*'-')
        
        else:
            pass
        
        # === 1D grid filters
        
        self.hasGridFilter=False
        if ('dims/xfi' in self):
            self.xfi  = np.copy(self['dims/xfi'][()])
            if not np.array_equal(self.xfi, np.arange(nx,dtype=np.int64)):
                self.hasGridFilter=True
            if ('dims/xfiR' in self):
                self.xfiR = np.copy(self['dims/xfiR'][()])
        if ('dims/yfi' in self):
            self.yfi  = np.copy(self['dims/yfi'][()])
            if not np.array_equal(self.yfi, np.arange(ny,dtype=np.int64)):
                self.hasGridFilter=True
            if ('dims/yfiR' in self):
                self.yfiR = np.copy(self['dims/yfiR'][()])
        if ('dims/zfi' in self):
            self.zfi  = np.copy(self['dims/zfi'][()])
            if not np.array_equal(self.zfi, np.arange(nz,dtype=np.int64)):
                self.hasGridFilter=True
            if ('dims/zfiR' in self):
                self.zfiR = np.copy(self['dims/zfiR'][()])
        
        # === Time vector
        
        if ('dims/t' in self):
            self.t = np.copy(self['dims/t'][()])
            
            if ('data' in self): ## check t dim and data arr agree
                nt,_,_,_ = self['data/%s'%list(self['data'].keys())[0]].shape ## 4D
                if (nt!=self.t.size):
                    raise AssertionError('nt!=self.t.size : %i!=%i'%(nt,self.t.size))
            
            nt = self.t.size
            
            try:
                self.dt = self.t[1] - self.t[0]
            except IndexError:
                self.dt = 0.
            
            self.nt       = self.t.size
            self.duration = self.t[-1] - self.t[0]
            self.ti       = np.array(range(self.nt), dtype=np.int64)
        
        elif all([('data' in self),('dims/t' not in self)]): ## data but no time
            self.scalars = list(self['data'].keys())
            nt,_,_,_ = self['data/%s'%self.scalars[0]].shape
            self.nt  = nt
            self.t   = np.arange(self.nt, dtype=np.float64)
            self.ti  = np.arange(self.nt, dtype=np.int64)
            self.dt  = 1.
            self.duration = self.t[-1]-self.t[0]
        
        else: ## no data, no time
            self.t  = np.array([], dtype=np.float64)
            self.ti = np.array([], dtype=np.int64)
            self.nt = nt = 0
            self.dt = 0.
            self.duration = 0.
        
        #if verbose: print(72*'-')
        if verbose: even_print('nt', '%i'%self.nt )
        if verbose: even_print('dt', '%0.6f'%self.dt)
        if verbose: even_print('duration', '%0.2f'%self.duration )
        if hasattr(self, 'duration_avg'):
            if verbose: even_print('duration_avg', '%0.2f'%self.duration_avg )
        #if verbose: print(72*'-'+'\n')
        
        # if hasattr(self,'rectilinear'):
        #     if verbose: even_print('rectilinear', str(self.rectilinear) )
        # if hasattr(self,'curvilinear'):
        #     if verbose: even_print('curvilinear', str(self.curvilinear) )
        
        # === ts group names & scalars
        
        if ('data' in self):
            self.scalars = list(self['data'].keys()) ## 4D : string names of scalars : ['u','v','w'],...
            self.n_scalars = len(self.scalars)
            self.scalars_dtypes = []
            for scalar in self.scalars:
                self.scalars_dtypes.append(self[f'data/{scalar}'].dtype)
            self.scalars_dtypes_dict = dict(zip(self.scalars, self.scalars_dtypes)) ## dict {<<scalar>>: <<dtype>>}
        else:
            self.scalars = []
            self.n_scalars = 0
            self.scalars_dtypes = []
            self.scalars_dtypes_dict = dict(zip(self.scalars, self.scalars_dtypes))
        
        return
    
    def init_from_eas4(self, fn_eas4, **kwargs):
        '''
        Initialize an RGD from an EAS4 (NS3D output format)
        -----
        - x_min/max xi_min/max : min/max coord/index
        - stride filters (sx,sy,sz)
        '''
        
        #EAS4_NO_G=1; EAS4_X0DX_G=2; EAS4_UDEF_G=3; EAS4_ALL_G=4; EAS4_FULL_G=5
        gmode_dict = {1:'EAS4_NO_G', 2:'EAS4_X0DX_G', 3:'EAS4_UDEF_G', 4:'EAS4_ALL_G', 5:'EAS4_FULL_G'}
        
        verbose = kwargs.get('verbose',True)
        if (self.rank!=0):
            verbose=False
        
        ## spatial resolution filter : take every nth grid point
        sx = kwargs.get('sx',1)
        sy = kwargs.get('sy',1)
        sz = kwargs.get('sz',1)
        
        ## spatial resolution filter : set x/y/z bounds
        x_min = kwargs.get('x_min',None)
        y_min = kwargs.get('y_min',None)
        z_min = kwargs.get('z_min',None)
        
        x_max = kwargs.get('x_max',None)
        y_max = kwargs.get('y_max',None)
        z_max = kwargs.get('z_max',None)
        
        xi_min = kwargs.get('xi_min',None)
        yi_min = kwargs.get('yi_min',None)
        zi_min = kwargs.get('zi_min',None)
        
        xi_max = kwargs.get('xi_max',None)
        yi_max = kwargs.get('yi_max',None)
        zi_max = kwargs.get('zi_max',None)
        
        ## Set default attributes
        self.attrs['fsubtype'] = 'unsteady'
        self.attrs['fclass']   = 'rgd'
        
        if verbose: print('\n'+'rgd.init_from_eas4()'+'\n'+72*'-')
        
        if not (os.path.isfile(fn_eas4) or (os.path.islink(fn_eas4) and os.path.isfile(os.path.realpath(fn_eas4)))):
            raise FileNotFoundError(f'{fn_eas4} is not a file or a symlink to an existing file')
        
        with eas4(fn_eas4, 'r', verbose=False, driver=self.driver, comm=self.comm) as hf_eas4:
            
            if verbose: even_print('infile', os.path.basename(fn_eas4))
            if verbose: even_print('infile size', '%0.2f [GB]'%(os.path.getsize(fn_eas4)/1024**3))
            
            if verbose: even_print( 'gmode dim1' , '%i / %s'%( hf_eas4.gmode_dim1, gmode_dict[hf_eas4.gmode_dim1] ) )
            if verbose: even_print( 'gmode dim2' , '%i / %s'%( hf_eas4.gmode_dim2, gmode_dict[hf_eas4.gmode_dim2] ) )
            if verbose: even_print( 'gmode dim3' , '%i / %s'%( hf_eas4.gmode_dim3, gmode_dict[hf_eas4.gmode_dim3] ) )
            
            ## Check gmode (RGD should not have more than ALL_G/4 on any dim)
            if (hf_eas4.gmode_dim1 > 4):
                raise ValueError('turbx.rgd cannot handle gmode > 4 (EAS4 gmode_dim1=%i)'%hf_eas4.gmode_dim1)
            if (hf_eas4.gmode_dim2 > 4):
                raise ValueError('turbx.rgd cannot handle gmode > 4 (EAS4 gmode_dim2=%i)'%hf_eas4.gmode_dim2)
            if (hf_eas4.gmode_dim3 > 4):
                raise ValueError('turbx.rgd cannot handle gmode > 4 (EAS4 gmode_dim3=%i)'%hf_eas4.gmode_dim3)
            
            if verbose: even_print( 'nx' , f'{hf_eas4.nx:d}' )
            if verbose: even_print( 'ny' , f'{hf_eas4.ny:d}' )
            if verbose: even_print( 'nz' , f'{hf_eas4.nz:d}' )
            if verbose: print(72*'-')
            if verbose: even_print('outfile', self.fname)
            
            # === Copy over freestream parameters
            
            header_attr_keys = [
                'Ma','Re','Pr',
                'kappa','R',
                'p_inf','T_inf',
                'S_Suth','mu_Suth_ref','T_Suth_ref',
                ]
            
            ## assert that top-level attributes don't already exist
            #if any([ key in self.attrs for key in header_attr_keys ]):
            #    raise ValueError('some udef keys are already present in target file.')
            
            ## udef dict from EAS4
            udef = hf_eas4.udef
            
            ## Strip dict into 2x arrays (keys,values) and save to HDF5
            udef_real    = list(udef.values())
            udef_char    = list(udef.keys())
            udef_real_h5 = np.array(udef_real, dtype=np.float64)
            udef_char_h5 = np.array([s.encode('ascii', 'ignore') for s in udef_char], dtype='S128')
            
            if ('header/udef_real' in self):
                del self['header/udef_real']
            if ('header/udef_char' in self):
                del self['header/udef_char']
            
            self.create_dataset('header/udef_real', data=udef_real_h5, dtype=np.float64)
            self.create_dataset('header/udef_char', data=udef_char_h5, dtype='S128')
            
            ## assert that all primary udef keys are available in EAS4
            ##  --> this could be fed into 'freestream_parameters()' instead
            for key in header_attr_keys:
                if key not in udef.keys():
                    raise ValueError(f"key '{key}' not found in udef of {fn_eas4}")
            
            ## write (primary) udef members as top-level attributes of HDF5 file
            for key in header_attr_keys:
                self.attrs[key] = udef[key]
            
            ## standard freestream parameters
            Ma          = udef['Ma']
            Re          = udef['Re']
            Pr          = udef['Pr']
            kappa       = udef['kappa']
            R           = udef['R']
            p_inf       = udef['p_inf']
            T_inf       = udef['T_inf']
            S_Suth      = udef['S_Suth']
            mu_Suth_ref = udef['mu_Suth_ref']
            T_Suth_ref  = udef['T_Suth_ref']
            
            ## compute derived freestream parameters
            C_Suth    = mu_Suth_ref/(T_Suth_ref**(3/2))*(T_Suth_ref + S_Suth) ## [kg/(m·s·√K)]
            mu_inf    = mu_Suth_ref*(T_inf/T_Suth_ref)**(3/2) * ((T_Suth_ref+S_Suth)/(T_inf+S_Suth))
            rho_inf   = p_inf/(R*T_inf)
            nu_inf    = mu_inf/rho_inf
            a_inf     = np.sqrt(kappa*R*T_inf)
            U_inf     = Ma*a_inf
            cp        = R*kappa/(kappa-1.)
            cv        = cp/kappa
            recov_fac = Pr**(1/3)
            Taw       = T_inf + recov_fac*U_inf**2/(2*cp)
            lchar     = Re*nu_inf/U_inf
            tchar     = lchar / U_inf
            
            ## aliases
            uchar = U_inf
            M_inf = Ma
            
            p_tot_inf   = p_inf   * (1 + (kappa-1)/2 * M_inf**2)**(kappa/(kappa-1))
            T_tot_inf   = T_inf   * (1 + (kappa-1)/2 * M_inf**2)
            rho_tot_inf = rho_inf * (1 + (kappa-1)/2 * M_inf**2)**(1/(kappa-1))
            
            ## write (derived) freestream parameters as top-level attributes of HDF5 file
            self.attrs['C_Suth']      = C_Suth
            self.attrs['mu_inf']      = mu_inf
            self.attrs['rho_inf']     = rho_inf
            self.attrs['nu_inf']      = nu_inf
            self.attrs['a_inf']       = a_inf
            self.attrs['U_inf']       = U_inf
            self.attrs['cp']          = cp
            self.attrs['cv']          = cv
            self.attrs['recov_fac']   = recov_fac
            self.attrs['Taw']         = Taw
            self.attrs['lchar']       = lchar
            self.attrs['tchar']       = tchar
            self.attrs['uchar']       = uchar
            self.attrs['M_inf']       = M_inf
            self.attrs['p_tot_inf']   = p_tot_inf
            self.attrs['T_tot_inf']   = T_tot_inf
            self.attrs['rho_tot_inf'] = rho_tot_inf
            
            # === copy over dims info
            
            if all([('dims/x' in self),('dims/y' in self),('dims/z' in self)]):
                pass
                ## future: 2D/3D handling here
            else:
                
                x = np.copy( hf_eas4.x )
                y = np.copy( hf_eas4.y )
                z = np.copy( hf_eas4.z )
                
                nx  = x.size
                ny  = y.size
                nz  = z.size
                ngp = nx*ny*nz
                
                if any([
                    (xi_min is not None),
                    (xi_max is not None),
                    (yi_min is not None),
                    (yi_max is not None),
                    (zi_min is not None),
                    (zi_max is not None),
                    (x_min is not None),
                    (x_max is not None),
                    (y_min is not None),
                    (y_max is not None),
                    (z_min is not None),
                    (z_max is not None),
                    (sx!=1),
                    (sy!=1),
                    (sz!=1),
                    ]):
                        hasFilters=True
                else:
                    hasFilters=False
                
                if hasFilters and verbose:
                    print(72*'-')
                    msg = 'Filtered Dim Info'
                    print(msg+'\n'+len(msg)*'-')
                
                ## READ boolean arrays for each axis
                xfiR = np.full(nx,False,dtype=bool)
                yfiR = np.full(ny,False,dtype=bool)
                zfiR = np.full(nz,False,dtype=bool)
                
                ## index arrays along each axis --> these get overwritten depending on filter choices
                xfi = np.arange(nx,dtype=np.int64)
                yfi = np.arange(ny,dtype=np.int64)
                zfi = np.arange(nz,dtype=np.int64)
                
                ## total bounds clip (physical nondimensional distance)
                if (x_min is not None):
                    xfi = np.array([i for i in xfi if (x[i] >= x_min)])
                    if verbose: even_print('x_min', '%0.3f'%x_min)
                if (x_max is not None):
                    xfi = np.array([i for i in xfi if (x[i] <= x_max)])
                    if verbose: even_print('x_max', '%0.3f'%x_max)
                if (y_min is not None):
                    yfi = np.array([i for i in yfi if (y[i] >= y_min)])
                    if verbose: even_print('y_min', '%0.3f'%y_min)
                if (y_max is not None):
                    yfi = np.array([i for i in yfi if (y[i] <= y_max)])
                    if verbose: even_print('y_max', '%0.3f'%y_max)
                if (z_min is not None):
                    zfi = np.array([i for i in zfi if (z[i] >= z_min)])
                    if verbose: even_print('z_min', '%0.3f'%z_min)
                if (z_max is not None):
                    zfi = np.array([i for i in zfi if (z[i] <= z_max)])
                    if verbose: even_print('z_max', '%0.3f'%z_max)
                
                # === total bounds clip (coordinate index)
                
                if (xi_min is not None):
                    
                    xfi_ = []
                    if verbose: even_print('xi_min', '%i'%xi_min)
                    for c in xfi:
                        if (xi_min<0) and (c>=(nx+xi_min)): ## support negative indexing
                            xfi_.append(c)
                        elif (xi_min>=0) and (c>=xi_min):
                            xfi_.append(c)
                    xfi=np.array(xfi_, dtype=np.int64)
                
                if (xi_max is not None):
                    
                    xfi_ = []
                    if verbose: even_print('xi_max', '%i'%xi_max)
                    for c in xfi:
                        if (xi_max<0) and (c<=(nx+xi_max)): ## support negative indexing
                            xfi_.append(c)
                        elif (xi_max>=0) and (c<=xi_max):
                            xfi_.append(c)
                    xfi=np.array(xfi_, dtype=np.int64)
                
                if (yi_min is not None):
                    
                    yfi_ = []
                    if verbose: even_print('yi_min', '%i'%yi_min)
                    for c in yfi:
                        if (yi_min<0) and (c>=(ny+yi_min)): ## support negative indexing
                            yfi_.append(c)
                        elif (yi_min>=0) and (c>=yi_min):
                            yfi_.append(c)
                    yfi=np.array(yfi_, dtype=np.int64)
                
                if (yi_max is not None):
                    
                    yfi_ = []
                    if verbose: even_print('yi_max', '%i'%yi_max)
                    for c in yfi:
                        if (yi_max<0) and (c<=(ny+yi_max)): ## support negative indexing
                            yfi_.append(c)
                        elif (yi_max>=0) and (c<=yi_max):
                            yfi_.append(c)
                    yfi=np.array(yfi_, dtype=np.int64)
                
                if (zi_min is not None):
                    
                    zfi_ = []
                    if verbose: even_print('zi_min', '%i'%zi_min)
                    for c in zfi:
                        if (zi_min<0) and (c>=(nz+zi_min)): ## support negative indexing
                            zfi_.append(c)
                        elif (zi_min>=0) and (c>=zi_min):
                            zfi_.append(c)
                    zfi=np.array(zfi_, dtype=np.int64)
                
                if (zi_max is not None):
                    
                    zfi_ = []
                    if verbose: even_print('zi_max', '%i'%zi_max)
                    for c in zfi:
                        if (zi_max<0) and (c<=(nz+zi_max)): ## support negative indexing
                            zfi_.append(c)
                        elif (zi_max>=0) and (c<=zi_max):
                            zfi_.append(c)
                    zfi=np.array(zfi_, dtype=np.int64)
                
                ## resolution filter (skip every n grid points in each direction)
                if (sx!=1):
                    if verbose: even_print('sx', '%i'%sx)
                    xfi = xfi[::sx]
                if (sy!=1):
                    if verbose: even_print('sy', '%i'%sy)
                    yfi = yfi[::sy]
                if (sz!=1):
                    if verbose: even_print('sz', '%i'%sz)
                    zfi = zfi[::sz]
                
                if hasFilters:
                    
                    if (xfi.size==0):
                        raise ValueError('x grid filter is empty... check!')
                    if (yfi.size==0):
                        raise ValueError('y grid filter is empty... check!')
                    if (zfi.size==0):
                        raise ValueError('z grid filter is empty... check!')
                    
                    ## set 'True' for indices to be read
                    xfiR[xfi] = True
                    yfiR[yfi] = True
                    zfiR[zfi] = True
                    
                    ## write 1D grid filters to HDF5
                    self.create_dataset('dims/xfi'  , data=xfi  )
                    self.create_dataset('dims/yfi'  , data=yfi  )
                    self.create_dataset('dims/zfi'  , data=zfi  )
                    self.create_dataset('dims/xfiR' , data=xfiR )
                    self.create_dataset('dims/yfiR' , data=yfiR )
                    self.create_dataset('dims/zfiR' , data=zfiR )
                    
                    ## overwrite 1D grid vectors
                    x = np.copy(x[xfi])
                    y = np.copy(y[yfi])
                    z = np.copy(z[zfi])
                    
                    nx = x.shape[0]
                    ny = y.shape[0]
                    nz = z.shape[0]
                    ngp = nx*ny*nz
                    
                    if verbose: even_print('nx'  ,  f'{nx:d}' )
                    if verbose: even_print('ny'  ,  f'{ny:d}' )
                    if verbose: even_print('nz'  ,  f'{nz:d}' )
                    if verbose: even_print('ngp' , f'{ngp:d}' )
                
                self.nx  = nx
                self.ny  = ny
                self.nz  = nz
                self.ngp = ngp
                
                ## write 1D [x,y,z] coord arrays
                if ('dims/x' in self):
                    del self['dims/x']
                self.create_dataset('dims/x', data=x)
                if ('dims/y' in self):
                    del self['dims/y']
                self.create_dataset('dims/y', data=y)
                if ('dims/z' in self):
                    del self['dims/z']
                self.create_dataset('dims/z', data=z)
        
        if verbose: print(72*'-')
        self.get_header(verbose=True)
        if verbose: print(72*'-')
        return
    
    def init_from_rgd(self, fn_rgd, **kwargs):
        '''
        initialize an RGD from an RGD (copy over header data & coordinate data)
        '''
        
        t_info = kwargs.get('t_info',True)
        #chunk_kb = kwargs.get('chunk_kb',4*1024) ## 4 [MB]
        
        #verbose = kwargs.get('verbose',True)
        #if (self.rank!=0):
        #    verbose=False
        
        ## set default attributes: fsubtype, fclass
        self.attrs['fsubtype'] = 'unsteady'
        self.attrs['fclass']   = 'rgd'
        
        with rgd(fn_rgd, 'r', driver=self.driver, comm=self.comm) as hf_ref:
            
            ## copy over fsubtype
            if hasattr(hf_ref,'fsubtype'):
                self.attrs['fsubtype'] = hf_ref.fsubtype
            
            # === copy over header info if needed
            
            ## copy top-level attributes
            for key in hf_ref.attrs:
                self.attrs[key] = hf_ref.attrs[key]
            
            if all([('header/udef_real' in self),('header/udef_char' in self)]):
                raise ValueError('udef already present')
            else:
                udef         = hf_ref.udef
                udef_real    = list(udef.values())
                udef_char    = list(udef.keys())
                udef_real_h5 = np.array(udef_real, dtype=np.float64)
                udef_char_h5 = np.array([s.encode('ascii', 'ignore') for s in udef_char], dtype='S128')
                
                self.create_dataset('header/udef_real', data=udef_real_h5, maxshape=np.shape(udef_real_h5), dtype=np.float64)
                self.create_dataset('header/udef_char', data=udef_char_h5, maxshape=np.shape(udef_char_h5), dtype='S128')
                self.udef      = udef
                self.udef_real = udef_real
                self.udef_char = udef_char
            
            # === copy over spatial dim info
            
            x = np.copy( hf_ref.x )
            y = np.copy( hf_ref.y )
            z = np.copy( hf_ref.z )
            
            self.nx  = x.size
            self.ny  = y.size
            self.nz  = z.size
            self.ngp = self.nx*self.ny*self.nz
            if ('dims/x' in self):
                del self['dims/x']
            if ('dims/y' in self):
                del self['dims/y']
            if ('dims/z' in self):
                del self['dims/z']
            
            self.create_dataset('dims/x', data=x)
            self.create_dataset('dims/y', data=y)
            self.create_dataset('dims/z', data=z)
            
            # === copy over temporal dim info
            
            if t_info:
                self.t  = hf_ref.t
                self.nt = self.t.size
                self.create_dataset('dims/t', data=hf_ref.t)
            else:
                t = np.array([0.], dtype=np.float64)
                if ('dims/t' in self):
                    del self['dims/t']
                self.create_dataset('dims/t', data=t)
            
            # ===
            
            ## copy over [data_dim/<>] dsets if present
            if ('data_dim' in hf_ref):
                for dsn in hf_ref['data_dim'].keys():
                    data = np.copy( hf_ref[f'data_dim/{dsn}'][()] ) 
                    self.create_dataset(f'data_dim/{dsn}', data=data, chunks=None)
                    if self.usingmpi: self.comm.Barrier()
        
        self.get_header(verbose=False)
        return
    
    def import_eas4(self, fn_eas4_list, **kwargs):
        '''
        import data from a series of EAS4 files to a RGD
        '''
        
        if (self.rank!=0):
            verbose=False
        else:
            verbose=True
        
        #EAS4_NO_G=1; EAS4_X0DX_G=2; EAS4_UDEF_G=3; EAS4_ALL_G=4; EAS4_FULL_G=5
        gmode_dict = {1:'EAS4_NO_G', 2:'EAS4_X0DX_G', 3:'EAS4_UDEF_G', 4:'EAS4_ALL_G', 5:'EAS4_FULL_G'}
        
        if verbose: print('\n'+'rgd.import_eas4()'+'\n'+72*'-')
        t_start_func = timeit.default_timer()
        
        ntbuf = kwargs.get('ntbuf',1) ## [t] R/W buffer size
        if not isinstance(ntbuf, int):
            raise ValueError('ntbuf must be type int')
        if (ntbuf<1):
            raise ValueError('ntbuf<1')
        
        if self.open_mode=='r':
            raise ValueError('cant do import or file initialization if file has been opened in read-only mode.')
        
        report_reads  = kwargs.get('report_reads',False)
        report_writes = kwargs.get('report_writes',True)
        
        ti_min = kwargs.get('ti_min',None)
        ti_max = kwargs.get('ti_max',None)
        tt_min = kwargs.get('tt_min',None)
        tt_max = kwargs.get('tt_max',None)
        
        ## dont actually copy over data, just initialize datasets with 0's
        init_dsets_only = kwargs.get('init_dsets_only',False)
        
        ## delete EAS4s after import --> DANGER!
        delete_after_import = kwargs.get('delete_after_import',False)
        
        ## if you're just initializing, don't allow delete
        if (init_dsets_only and delete_after_import):
            raise ValueError("if init_dsets_only=True, then delete_after_import should not be activated!")
        
        ## delete only allowed if no time ranges are selected
        if delete_after_import and any([(ti_min is not None),(ti_max is not None),(tt_min is not None),(tt_max is not None)]):
            raise ValueError("if delete_after_import=True, then ti_min,ti_max,tt_min,tt_max are not supported")
        
        chunk_kb   = kwargs.get('chunk_kb',2*1024) ## h5 chunk size: default 2 [MB]
        #chunk_kb   = kwargs.get('chunk_kb',64*1024) ## h5 chunk size: default 64 [MB]
        #chunk_base = kwargs.get('chunk_base',2)
        
        ## used later when determining whether to re-initialize datasets
        #chunk_constraint = kwargs.get('chunk_constraint',(1,None,None,None))
        chunk_constraint = kwargs.get('chunk_constraint',None)
        if chunk_constraint is None:
            chunk_constraint_was_provided = False
        else:
            chunk_constraint_was_provided = True
        
        ## float precision when copying
        ## default is 'single' i.e. cast data to single
        ## 'same' will preserve the floating point precision from the EAS4 file
        prec = kwargs.get('prec',None)
        if (prec is None):
            prec = 'single'
        elif (prec=='single'):
            pass
        elif (prec=='same'):
            pass
        else:
            raise ValueError('prec not set correctly')
        
        ## check for an often made mistake
        ## 'ts_min' / 'ts_max' should NOT be allowed as inputs
        ts_min = kwargs.get('ts_min',None)
        ts_max = kwargs.get('ts_max',None)
        if (ts_min is not None):
            raise ValueError('ts_min is not an option --> did you mean ti_min or tt_min?')
        if (ts_max is not None):
            raise ValueError('ts_max is not an option --> did you mean ti_max or tt_max?')
        del ts_min
        del ts_max
        
        ## check that the passed iterable of EAS4 files is OK
        if not hasattr(fn_eas4_list, '__iter__'):
            raise ValueError('first arg \'fn_eas4_list\' must be iterable')
        for fn_eas4 in fn_eas4_list:
            if not os.path.isfile(fn_eas4):
                raise FileNotFoundError('%s not found!'%fn_eas4)
        
        ## ranks per direction
        rx = kwargs.get('rx',1)
        ry = kwargs.get('ry',1)
        rz = kwargs.get('rz',1)
        rt = kwargs.get('rt',1)
        
        ## check validity of rank declaration
        if not all(isinstance(rr,int) and rr>0 for rr in (rx,ry,rz,rt)):
            raise ValueError('rx,ry,rz,rt must be positive integers')
        if (rx*ry*rz*rt != self.n_ranks):
            raise ValueError('rx*ry*rz*rt != self.n_ranks')
        if (rx>self.nx):
            raise ValueError('rx>self.nx')
        if (ry>self.ny):
            raise ValueError('ry>self.ny')
        if (rz>self.nz):
            raise ValueError('rz>self.nz')
        if not self.usingmpi:
            if rx>1:
                if verbose: print(f'WARNING: file not opened in MPI mode but rx={rx:d}... setting rx=1')
                rx = 1
            if ry>1:
                if verbose: print(f'WARNING: file not opened in MPI mode but ry={ry:d}... setting ry=1')
                ry = 1
            if rz>1:
                if verbose: print(f'WARNING: file not opened in MPI mode but rz={rz:d}... setting rz=1')
                rz = 1
        
        ## st = timestep skip
        ## spatial [x,y,z] skips done in init_from_XXX()
        st = kwargs.get('st',1)
        
        if not isinstance(st, int):
            raise ValueError('time skip parameter st should be type int')
        if (st<1):
            raise ValueError('st<1')
        
        ## update this RGD's header and attributes
        self.get_header(verbose=False)
        
        if self.usingmpi:
            comm_eas4 = MPI.COMM_WORLD ## communicator for opening EAS4s
        else:
            comm_eas4 = None
        
        ## get all time info & check
        if (self.rank==0):
            t = np.array([], dtype=np.float64)
            for fn_eas4 in fn_eas4_list:
                with eas4(fn_eas4, 'r', verbose=False) as hf_eas4:
                    t_ = np.copy(hf_eas4.t)
                t = np.concatenate((t,t_))
        else:
            t = np.array([],dtype=np.float64) ## 't' must exist on all ranks prior to bcast
        
        if self.usingmpi:
            self.comm.Barrier()
        
        ## broadcast concatenated time vector to all ranks
        if self.usingmpi:
            t = self.comm.bcast(t, root=0)
        
        if verbose: even_print('n EAS4 files','%i'%len(fn_eas4_list))
        if verbose: even_print('nt all files','%i'%t.size)
        if verbose: even_print('delete after import',str(delete_after_import))
        if verbose: print(72*'-')
        
        if (t.size>1):
            
            ## check no zero distance elements
            if np.any(np.diff(t) == 0):
                raise ValueError('t arr has zero-distance elements')
            else:
                if verbose: even_print('check: Δt!=0','passed')
            
            ## check monotonically increasing
            if not np.all(np.diff(t) > 0.):
                raise ValueError('t arr not monotonically increasing')
            else:
                if verbose: even_print('check: t mono increasing','passed')
            
            ## check constant Δt
            dt0 = np.diff(t)[0]
            if not np.all(np.isclose(np.diff(t), dt0, rtol=1e-3)):
                if (self.rank==0): print(np.diff(t))
                raise ValueError('t arr not uniformly spaced')
            else:
                if verbose: even_print('check: constant Δt','passed')
        
        # === get all grid info & check
        
        if len(fn_eas4_list)>1:
            if self.rank==0:
                eas4_x_arr = []
                eas4_y_arr = []
                eas4_z_arr = []
                for fn_eas4 in fn_eas4_list:
                    with eas4(fn_eas4, 'r', verbose=False) as hf_eas4:
                        eas4_x_arr.append( hf_eas4.x )
                        eas4_y_arr.append( hf_eas4.y )
                        eas4_z_arr.append( hf_eas4.z )
                
                ## check coordinate vectors are same
                if not np.all([np.allclose(eas4_z_arr[i],eas4_z_arr[0],rtol=1e-8,atol=1e-8) for i in range(len(fn_eas4_list))]):
                    raise ValueError('EAS4 files do not have the same [z] coordinates')
                    if self.usingmpi: self.comm.Abort(1)
                else:
                    if verbose: even_print('check: [z] coordinate vectors equal','passed')
                
                if not np.all([np.allclose(eas4_y_arr[i],eas4_y_arr[0],rtol=1e-8,atol=1e-8) for i in range(len(fn_eas4_list))]):
                    raise ValueError('EAS4 files do not have the same [y] coordinates')
                    if self.usingmpi: self.comm.Abort(1)
                else:
                    if verbose: even_print('check: [y] coordinate vectors equal','passed')
                
                if not np.all([np.allclose(eas4_x_arr[i],eas4_x_arr[0],rtol=1e-8,atol=1e-8) for i in range(len(fn_eas4_list))]):
                    raise ValueError('EAS4 files do not have the same [x] coordinates')
                    if self.usingmpi: self.comm.Abort(1)
                else:
                    if verbose: even_print('check: [x] coordinate vectors equal','passed')
                
                if verbose: print(72*'-')
            
            if self.usingmpi:
                self.comm.Barrier()
        
        ## [t] resolution filter (skip every N timesteps)
        tfi = np.arange(t.size, dtype=np.int64)
        if (st!=1):
            if verbose:
                even_print('st', f'{st:d}')
                print(72*'-')
            tfi = np.copy( tfi[::st] )
        
        ## initialize 'doRead' vector --> boolean vector to be updated
        doRead = np.full((t.size,), True, dtype=bool)
        
        ## skip filter
        if (st!=1):
            doRead[np.isin(np.arange(t.size),tfi,invert=True)] = False
        
        ## min/max index filter
        if (ti_min is not None):
            if not isinstance(ti_min, int):
                raise TypeError('ti_min must be type int')
            doRead[:ti_min] = False
        if (ti_max is not None):
            if not isinstance(ti_max, int):
                raise TypeError('ti_max must be type int')
            doRead[ti_max:] = False
        if (tt_min is not None):
            if (tt_min>=0.):
                doRead[np.where((t-t.min())<tt_min)] = False
            elif (tt_min<0.):
                doRead[np.where((t-t.max())<tt_min)] = False
        if (tt_max is not None):
            if (tt_max>=0.):
                doRead[np.where((t-t.min())>tt_max)] = False
            elif (tt_max<0.):
                doRead[np.where((t-t.max())>tt_max)] = False
        
        ## RGD time attributes
        self.t  = np.copy(t[doRead]) ## filter times by True/False from boolean vector doRead
        self.nt = self.t.shape[0]
        self.ti = np.arange(self.nt, dtype=np.int64)
        
        # ## update [t]
        # if ('dims/t' in self):
        #     t_ = np.copy(self['dims/t'][()])
        #     if not np.allclose(t_, self.t, rtol=1e-8, atol=1e-8):
        #         if verbose:
        #             print('>>> [t] in file not match [t] that has been determined ... overwriting')
        #         del self['dims/t']
        #         self.create_dataset('dims/t', data=self.t)
        # else:
        #     self.create_dataset('dims/t', data=self.t)
        
        ## update [t]
        if ('dims/t' in self):
            del self['dims/t']
        self.create_dataset('dims/t', data=self.t)
        
        ## divide spatial OUTPUT grid by ranks
        ## if no grid filter present, then INPUT = OUTPUT
        if self.usingmpi:
            comm4d = self.comm.Create_cart(dims=[rx,ry,rz,rt], periods=[False,False,False,False], reorder=False)
            t4d = comm4d.Get_coords(self.rank)
            
            rxl_ = np.array_split(np.arange(self.nx,dtype=np.int64),min(rx,self.nx))
            ryl_ = np.array_split(np.arange(self.ny,dtype=np.int64),min(ry,self.ny))
            rzl_ = np.array_split(np.arange(self.nz,dtype=np.int64),min(rz,self.nz))
            #rtl_ = np.array_split(np.arange(self.nt,dtype=np.int64),min(rt,self.nt))
            
            rxl = [[b[0],b[-1]+1] for b in rxl_ ]
            ryl = [[b[0],b[-1]+1] for b in ryl_ ]
            rzl = [[b[0],b[-1]+1] for b in rzl_ ]
            #rtl = [[b[0],b[-1]+1] for b in rtl_ ]
            
            rx1, rx2 = rxl[t4d[0]]
            ry1, ry2 = ryl[t4d[1]]
            rz1, rz2 = rzl[t4d[2]]
            #rt1, rt2 = rtl[t4d[3]]
            
            nxr = rx2 - rx1
            nyr = ry2 - ry1
            nzr = rz2 - rz1
            #ntr = rt2 - rt1
        
        else:
            nxr = self.nx
            nyr = self.ny
            nzr = self.nz
            #ntr = self.nt
        
        ## divide spatial READ/INPUT grid by ranks --> if grid filters present
        if self.hasGridFilter:
            if self.usingmpi:
                
                ## this rank's indices to read from FULL file, indices in global context
                xfi_ = np.copy( self.xfi[rx1:rx2] )
                yfi_ = np.copy( self.yfi[ry1:ry2] )
                zfi_ = np.copy( self.zfi[rz1:rz2] )
                
                ## this rank's global read RANGE from FULL file
                rx1R,rx2R = xfi_.min() , xfi_.max()+1
                ry1R,ry2R = yfi_.min() , yfi_.max()+1
                rz1R,rz2R = zfi_.min() , zfi_.max()+1
                
                ## this rank's LOCAL index filter to cut down read data
                xfi_local = np.copy( xfi_ - rx1R )
                yfi_local = np.copy( yfi_ - ry1R )
                zfi_local = np.copy( zfi_ - rz1R )
        
        ## determine RGD scalars (get from EAS4 scalars)
        if not hasattr(self,'scalars') or (len(self.scalars)==0):
            
            with eas4(fn_eas4_list[0], 'r', verbose=False, driver=self.driver, comm=comm_eas4) as hf_eas4:
                self.scalars   = hf_eas4.scalars
                self.n_scalars = len(self.scalars)
                
                ## decide dtypes
                for scalar in hf_eas4.scalars:
                    
                    ti = 0
                    dsn = f'Data/{hf_eas4.domainName}/ts_{ti:06d}/par_{hf_eas4.scalar_n_map[scalar]:06d}'
                    dset = hf_eas4[dsn]
                    dtype = dset.dtype
                    
                    if (prec=='same'):
                        self.scalars_dtypes_dict[scalar] = dtype
                    elif (prec=='single'):
                        if (dtype!=np.float32) and (dtype!=np.float64): ## make sure its either a single or double float
                            raise ValueError
                        self.scalars_dtypes_dict[scalar] = np.dtype(np.float32)
                    else:
                        raise ValueError
        
        if self.usingmpi:
            comm_eas4.Barrier()
        
        # ==============================================================
        # initialize datasets
        # ==============================================================
        
        if verbose:
            progress_bar = tqdm(
                total=len(self.scalars),
                ncols=100,
                desc='initialize dsets',
                leave=True,
                file=sys.stdout,
                mininterval=0.1,
                smoothing=0.,
                #bar_format="\033[B{l_bar}{bar}| {n}/{total} [{percentage:.1f}%] {elapsed}/{remaining}\033[A\n\b",
                bar_format="{l_bar}{bar}| {n}/{total} [{percentage:.1f}%] {elapsed}/{remaining}",
                ascii="░█",
                colour='#FF6600',
                )
        
        for scalar in self.scalars:
            
            dtype   = self.scalars_dtypes_dict[scalar]
            data_gb = dtype.itemsize * self.nt*self.nz*self.ny*self.nx / 1024**3
            shape   = (self.nt,self.nz,self.ny,self.nx)
            
            ## the user provided a chunk_constraint, so calculate it
            if chunk_constraint_was_provided:
                chunks = h5_chunk_sizer(nxi=shape, constraint=chunk_constraint, size_kb=chunk_kb, itemsize=dtype.itemsize)
            else:
                if self.usingmpi:
                    chunks = h5_chunk_sizer(nxi=shape, constraint=(1,('max',self.nz//rz),('max',self.ny//ry),('max',self.nx//rx)), size_kb=chunk_kb, itemsize=dtype.itemsize)
                else:
                    chunks = h5_chunk_sizer(nxi=shape, constraint=(1,None,None,None), size_kb=chunk_kb, itemsize=dtype.itemsize)
            
            do_dset_initialize = True ## default value which, if all conditions are met, will be turned False
            
            dsn = f'data/{scalar}'
            
            ## check if dataset already exists and matches conditions
            ## ... if conditions are met then skip re-initializing dataset
            if self.open_mode in ('a','r+') and (dsn in self):
                dset = self[dsn]
                if verbose:
                    tqdm.write(even_print(f'dset {dsn} already exists', str(True), s=True))
                
                shape_matches = dset.shape == shape
                dtype_matches = dset.dtype == dtype
                
                ## either 1) no constraint was given or 2) constraint was given AND it matches
                chunks_match = not chunk_constraint_was_provided or dset.chunks == chunks
                
                ## if no constraint was given, copy back existing chunk
                if not chunk_constraint_was_provided:
                    chunks = dset.chunks
                
                if verbose:
                    tqdm.write(even_print(f'dset {dsn} shape matches', str(shape_matches), s=True))
                    tqdm.write(even_print(f'dset {dsn} dtype matches', str(dtype_matches), s=True))
                    if chunk_constraint_was_provided:
                        tqdm.write(even_print(f'dset {dsn} chunks match', str(chunks_match), s=True))
                
                if shape_matches and dtype_matches and chunks_match:
                    do_dset_initialize = False
            
            if do_dset_initialize:
                
                if (f'data/{scalar}' in self):
                    del self[f'data/{scalar}']
                
                if self.usingmpi: self.comm.Barrier()
                t_start = timeit.default_timer()
                
                if verbose:
                    tqdm.write(even_print(f'initializing data/{scalar}', f'{data_gb:0.2f} [GB]', s=True))
                
                ## !!!!!!!!!!! this has a tendency to hang !!!!!!!!!!!
                ## --> increasing Lustre stripe size tends to fix this (kwarg 'stripe_size_mb' upon 'w' open)
                dset = self.create_dataset(
                                    dsn,
                                    shape=shape,
                                    dtype=dtype,
                                    chunks=chunks,
                                    )
                
                ## write dummy data to dataset to ensure that it is truly initialized
                if not self.usingmpi:
                    h5_ds_force_allocate_chunks(dset,verbose=verbose)
                
                if self.usingmpi: self.comm.Barrier()
                t_delta = timeit.default_timer() - t_start
                if verbose:
                    tqdm.write(even_print(f'initialize data/{scalar}', f'{data_gb:0.2f} [GB]  {t_delta:0.2f} [s]  {(data_gb/t_delta):0.3f} [GB/s]', s=True))
            
            chunk_kb_ = np.prod(dset.chunks) * dset.dtype.itemsize / 1024. ## actual
            if verbose:
                tqdm.write(even_print('chunk shape (t,z,y,x)', str(dset.chunks), s=True))
                tqdm.write(even_print('chunk size', f'{int(round(chunk_kb_)):d} [KB]', s=True))
            
            if verbose:
                progress_bar.update()
        
        if self.usingmpi:
            self.comm.Barrier()
        if verbose:
            progress_bar.close()
            print(72*'-')
        
        ## report size of RGD after initialization
        if verbose: tqdm.write(even_print(os.path.basename(self.fname), f'{os.path.getsize(self.fname)/1024**3:0.2f} [GB]', s=True))
        if verbose: print(72*'-')
        
        # ==============================================================
        # open & read EAS4s, read data into RAM, write to RGD
        # ==============================================================
        
        if not init_dsets_only:
            
            ## should we tell the EAS4 to open with MPIIO hint 'romio_no_indep_rw' ?
            if self.usingmpi:
                eas4_no_indep_rw = True
            else:
                eas4_no_indep_rw = False
            
            ## get main dtype and confirm all scalar dtypes are same (limitation)
            dtype = self.scalars_dtypes_dict[self.scalars[0]]
            for scalar in self.scalars:
                if not ( np.dtype(self.scalars_dtypes_dict[scalar]) == np.dtype(dtype) ):
                    raise NotImplementedError('dtype of scalars in output HDF5 file are not same. update!')
            
            ## current limitation of read buffer due to uncreative implementation
            if (self.nt%ntbuf!=0):
                raise ValueError(f'n timesteps to be read ({self.nt}) is not divisible by ntbuf ({ntbuf:d})')
            
            ## initialize read/write buffer
            databuf = np.zeros(shape=(ntbuf,nzr,nyr,nxr), dtype={'names':self.scalars, 'formats':[ dtype for s in self.scalars ]})
            buffer_nts_loaded = 0 ## counter for number of timesteps loaded in buffer
            buffers_written = -1 ## counter for number of buffers that have been written
            
            #print(f'rank {self.rank:d} databuf shape : {str(databuf["u"].shape)}')
            
            if self.usingmpi:
                self.comm.Barrier()
            
            ## report read/write buffer size
            if verbose:
                even_print( 'R/W buffer size (global)' , f'{ntbuf*np.prod(shape[1:])*len(self.scalars)*dtype.itemsize/1024**3:0.2f} [GB]' )
                print(72*'-')
            
            if verbose:
                progress_bar = tqdm(
                    #total=self.nt*self.n_scalars,
                    total=self.nt//ntbuf, ## N buffer writes
                    ncols=100,
                    desc='import',
                    leave=True,
                    file=sys.stdout,
                    mininterval=0.1,
                    smoothing=0.,
                    #bar_format="\033[B{l_bar}{bar}| {n}/{total} [{percentage:.1f}%] {elapsed}/{remaining}\033[A\n\b",
                    bar_format="{l_bar}{bar}| {n}/{total} [{percentage:.1f}%] {elapsed}/{remaining}",
                    ascii="░█",
                    colour='#FF6600',
                    )
            
            ## counters / timers
            data_gb_read  = 0.
            data_gb_write = 0.
            t_read  = 0.
            t_write = 0.
            
            tii  = -1 ## counter full series
            tiii = -1 ## counter RGD-local
            for fn_eas4 in fn_eas4_list: ## this has to stay the outer-most loop for file deletion purposes
                with eas4(fn_eas4, 'r', verbose=False, driver=self.driver, comm=comm_eas4, no_indep_rw=eas4_no_indep_rw) as hf_eas4:
                    
                    if verbose: tqdm.write(even_print(os.path.basename(fn_eas4), '%0.2f [GB]'%(os.path.getsize(fn_eas4)/1024**3), s=True))
                    
                    # if verbose: tqdm.write(even_print('gmode_dim1' , '%i'%hf_eas4.gmode_dim1  , s=True))
                    # if verbose: tqdm.write(even_print('gmode_dim2' , '%i'%hf_eas4.gmode_dim2  , s=True))
                    # if verbose: tqdm.write(even_print('gmode_dim3' , '%i'%hf_eas4.gmode_dim3  , s=True))
                    
                    if verbose: tqdm.write(even_print( 'gmode dim1' , '%i / %s'%( hf_eas4.gmode_dim1, gmode_dict[hf_eas4.gmode_dim1] ), s=True ))
                    if verbose: tqdm.write(even_print( 'gmode dim2' , '%i / %s'%( hf_eas4.gmode_dim2, gmode_dict[hf_eas4.gmode_dim2] ), s=True ))
                    if verbose: tqdm.write(even_print( 'gmode dim3' , '%i / %s'%( hf_eas4.gmode_dim3, gmode_dict[hf_eas4.gmode_dim3] ), s=True ))
                    
                    if verbose: tqdm.write(even_print('duration' , '%0.2f'%hf_eas4.duration , s=True))
                    
                    # ===
                    
                    for ti in range(hf_eas4.nt): ## this EAS4's time indices
                        tii += 1 ## full EAS4 series counter
                        if doRead[tii]:
                            tiii += 1 ## output RGD counter (takes into account skip, min/max)
                            
                            buffer_nts_loaded += 1
                            
                            #if verbose: tqdm.write(f'writing to buffer at index {tiii%ntbuf:d}') ## debug
                            
                            ## perform collective read, write to RAM buffer
                            for scalar in hf_eas4.scalars:
                                if (scalar in self.scalars):
                                    
                                    ## dset handle in EAS4
                                    dset = hf_eas4[f'Data/{hf_eas4.domainName}/ts_{ti:06d}/par_{hf_eas4.scalar_n_map[scalar]:06d}']
                                    
                                    if hf_eas4.dform==1:
                                        ds_nx,ds_ny,ds_nz = dset.shape
                                    elif hf_eas4.dform==2:
                                        ds_nz,ds_ny,ds_nx = dset.shape
                                    else:
                                        raise RuntimeError
                                    
                                    ## EAS4 has a 'collapsed' dimension but >1 ranks in that dim
                                    if ( ds_nx < rx ):
                                        raise ValueError(f'dset shape in [x] is <rx : dset.shape={str(dset.shape)} , rx={rx:d}')
                                    if ( ds_ny < ry ):
                                        raise ValueError(f'dset shape in [y] is <ry : dset.shape={str(dset.shape)} , ry={ry:d}')
                                    if ( ds_nz < rz ):
                                        raise ValueError(f'dset shape in [z] is <rz : dset.shape={str(dset.shape)} , rz={rz:d}')
                                    
                                    if hf_eas4.usingmpi: comm_eas4.Barrier()
                                    t_start = timeit.default_timer()
                                    
                                    if hf_eas4.usingmpi:
                                        if self.hasGridFilter:
                                            with dset.collective:
                                                if hf_eas4.dform==1:
                                                    d_ = dset[rx1R:rx2R,ry1R:ry2R,rz1R:rz2R]
                                                elif hf_eas4.dform==2:
                                                    d_ = dset[rz1R:rz2R,ry1R:ry2R,rx1R:rx2R]
                                                else:
                                                    raise RuntimeError
                                            
                                            if ( ds_nx == 1 ):
                                                xfi_local = [0,]
                                            if ( ds_ny == 1 ):
                                                yfi_local = [0,]
                                            if ( ds_nz == 1 ):
                                                zfi_local = [0,]
                                            
                                            databuf[scalar][tiii%ntbuf,:,:,:] = d_[ np.ix_(xfi_local,yfi_local,zfi_local) ].T
                                        
                                        else:
                                            with dset.collective:
                                                
                                                if hf_eas4.dform==1:
                                                    databuf[scalar][tiii%ntbuf,:,:,:] = dset[rx1:rx2,ry1:ry2,rz1:rz2].T
                                                elif hf_eas4.dform==2:
                                                    databuf[scalar][tiii%ntbuf,:,:,:] = dset[rz1:rz2,ry1:ry2,rx1:rx2]
                                                else:
                                                    raise RuntimeError
                                    
                                    else:
                                        if self.hasGridFilter:
                                            d_ = dset[()]
                                            databuf[scalar][tiii%ntbuf,:,:,:] = d_[ np.ix_(self.xfi,self.yfi,self.zfi) ].T
                                        else:
                                            if hf_eas4.dform==1:
                                                databuf[scalar][tiii%ntbuf,:,:,:] = dset[()].T
                                            elif hf_eas4.dform==2:
                                                databuf[scalar][tiii%ntbuf,:,:,:] = dset[()]
                                            else:
                                                raise RuntimeError
                                    
                                    if hf_eas4.usingmpi: comm_eas4.Barrier()
                                    t_delta = timeit.default_timer() - t_start
                                    
                                    data_gb       = dset.dtype.itemsize * np.prod(dset.shape) / 1024**3
                                    t_read       += t_delta
                                    data_gb_read += data_gb
                                    
                                    if report_reads and verbose:
                                        txt = even_print(f'read: {scalar}', f'{data_gb:0.3f} [GB]  {t_delta:0.3f} [s]  {data_gb/t_delta:0.3f} [GB/s]', s=True)
                                        tqdm.write(txt)
                            
                            ## collective write
                            if (buffer_nts_loaded%ntbuf==0): ## if buffer is full... initiate write
                                buffer_nts_loaded = 0 ## reset
                                buffers_written += 1 ## increment
                                
                                ## the time index range in RGD to write contents of R/W buffer to
                                ti1 = ntbuf*buffers_written
                                ti2 = ti1+ntbuf
                                #if verbose: tqdm.write(f'performing write: {ti1:d}:{ti2:d}') ## debug
                                
                                for scalar in self.scalars:
                                    
                                    dset = self[f'data/{scalar}'] ## dset in RGD
                                    
                                    if self.usingmpi: self.comm.Barrier()
                                    t_start = timeit.default_timer()
                                    if self.usingmpi:
                                        with dset.collective:
                                            dset[ti1:ti2,rz1:rz2,ry1:ry2,rx1:rx2] = databuf[scalar][:,:,:,:]
                                    else:
                                        dset[ti1:ti2,:,:,:] = databuf[scalar][:,:,:,:]
                                    
                                    if self.usingmpi: self.comm.Barrier()
                                    t_delta = timeit.default_timer() - t_start
                                    
                                    t_write       += t_delta
                                    data_gb       = ntbuf * databuf[scalar].dtype.itemsize * np.prod(dset.shape[1:]) / 1024**3
                                    data_gb_write += data_gb
                                    
                                    if report_writes and verbose:
                                        txt = even_print(f'write: {scalar}', f'{data_gb:0.3f} [GB]  {t_delta:0.3f} [s]  {data_gb/t_delta:0.3f} [GB/s]', s=True)
                                        tqdm.write(txt)
                                    
                                    ## write zeros to buffer (optional)
                                    databuf[scalar][:,:,:,:] = 0.
                                
                                if verbose: progress_bar.update() ## progress bar counts buffer dumps
                
                ## (optionally) delete source EAS4 file
                ## 'do_delete.txt' must be present to actually initiate deletion
                if delete_after_import:
                    if (self.rank==0):
                        if os.path.isfile('do_delete.txt'):
                            tqdm.write(even_print('deleting', fn_eas4, s=True))
                            os.remove(fn_eas4)
                    self.comm.Barrier()
            
            if verbose: progress_bar.close()
            
            if hf_eas4.usingmpi: comm_eas4.Barrier()
            if self.usingmpi: self.comm.Barrier()
        
        self.get_header(verbose=False)
        
        # ## get read read/write stopwatch totals all ranks
        # if not init_dsets_only:
        #     if self.usingmpi:
        #         G = self.comm.gather([data_gb_read, data_gb_write, self.rank], root=0)
        #         G = self.comm.bcast(G, root=0)
        #         data_gb_read  = sum([x[0] for x in G])
        #         data_gb_write = sum([x[1] for x in G])
        
        if init_dsets_only:
            if verbose: print('>>> init_dsets_only=True, so no EAS4 data was imported')
        
        if verbose: print(72*'-')
        if verbose: even_print('nt',       '%i'%self.nt )
        if verbose: even_print('dt',       '%0.8f'%self.dt )
        if verbose: even_print('duration', '%0.2f'%self.duration )
        
        if not init_dsets_only:
            if verbose: print(72*'-')
            if verbose: even_print('time read',format_time_string(t_read))
            if verbose: even_print('time write',format_time_string(t_write))
            if verbose: even_print('read total avg', f'{data_gb_read:0.2f} [GB]  {t_read:0.2f} [s]  {(data_gb_read/t_read):0.3f} [GB/s]')
            if verbose: even_print('write total avg', f'{data_gb_write:0.2f} [GB]  {t_write:0.2f} [s]  {(data_gb_write/t_write):0.3f} [GB/s]')
        
        ## report file
        if self.usingmpi:
            self.comm.Barrier()
        if verbose:
            print(72*'-')
            even_print( os.path.basename(self.fname), f'{(os.path.getsize(self.fname)/1024**3):0.2f} [GB]')
        if verbose: print(72*'-')
        if verbose: print('total time : rgd.import_eas4() : %s'%format_time_string((timeit.default_timer() - t_start_func)))
        if verbose: print(72*'-')
        return
    
    @staticmethod
    def copy(fn_rgd_src, fn_rgd_tgt, **kwargs):
        '''
        copy header info, selected scalars, and [x,y,z,t] range to new RGD file
        --> this currently does NOT work in serial mode
        '''
        
        try:
            comm    = MPI.COMM_WORLD
            rank    = MPI.COMM_WORLD.Get_rank()
            n_ranks = MPI.COMM_WORLD.Get_size()
        #except Exception as e:
        except Exception:
            print('rgd.copy() currently only works in MPI mode.')
            raise ## re-raise same exception, preserve traceback
        
        if (rank==0):
            verbose = True
        else:
            verbose = False
        
        if verbose: print('\n'+'rgd.copy()'+'\n'+72*'-')
        t_start_func = timeit.default_timer()
        
        if not h5py.h5.get_config().mpi:
            raise NotImplementedError('h5py must be parallel-enabled')
        
        rx       = kwargs.get('rx',1)
        ry       = kwargs.get('ry',1)
        rz       = kwargs.get('rz',1)
        rt       = kwargs.get('rt',1)
        force    = kwargs.get('force',False) ## overwrite or raise error if exists
        
        ti_min   = kwargs.get('ti_min',None)
        ti_max   = kwargs.get('ti_max',None)
        scalars  = kwargs.get('scalars',None)
        
        chunk_kb         = kwargs.get('chunk_kb',4*1024) ## h5 chunk size: default 4 [MB]
        chunk_constraint = kwargs.get('chunk_constraint',(1,None,None,None)) ## the 'constraint' parameter for sizing h5 chunks
        chunk_base       = kwargs.get('chunk_base',2)
        
        stripe_count   = kwargs.pop('stripe_count'   , 16 ) ## for initializing RGD file
        stripe_size_mb = kwargs.pop('stripe_size_mb' , 2  )
        
        xi_min = kwargs.get('xi_min',None) ## 4D coordinate 
        xi_max = kwargs.get('xi_max',None)
        yi_min = kwargs.get('yi_min',None)
        yi_max = kwargs.get('yi_max',None)
        zi_min = kwargs.get('zi_min',None)
        zi_max = kwargs.get('zi_max',None)
        ti_min = kwargs.get('ti_min',None)
        ti_max = kwargs.get('ti_max',None)
        
        ct = kwargs.get('ct',1) ## 'chunks' in time
        
        xi_step = kwargs.get('xi_step',1)
        yi_step = kwargs.get('yi_step',1)
        zi_step = kwargs.get('zi_step',1)
        
        prec_coords = kwargs.get('prec_coords',None)
        if (prec_coords is None):
            prec_coords = 'same'
        elif (prec_coords=='single'):
            pass
        elif (prec_coords=='same'):
            pass
        else:
            raise ValueError('prec_coords not set correctly')
        
        if (rt!=1):
            raise AssertionError('rt!=1')
        if (rx*ry*rz!=n_ranks):
            raise AssertionError('rx*ry*rz!=n_ranks')
        if not os.path.isfile(fn_rgd_src):
            raise FileNotFoundError(f'{fn_rgd_src} not found!')
        if os.path.isfile(fn_rgd_tgt) and not force:
            raise FileExistsError(f'{fn_rgd_tgt} already exists. delete it or use \'force=True\' kwarg')
        
        # ===
        
        with rgd(fn_rgd_src, 'r', comm=comm, driver='mpio') as hf_src:
            with rgd(fn_rgd_tgt, 'w', comm=comm, driver='mpio', force=force, stripe_count=stripe_count, stripe_size_mb=stripe_size_mb) as hf_tgt:
                
                ## copy over header info (source --> target)
                hf_tgt.init_from_rgd(fn_rgd_src)
                
                if (scalars is None):
                    scalars = hf_src.scalars
                
                if verbose:
                    even_print('fn_rgd_src' , fn_rgd_src )
                    even_print('nx' , '%i'%hf_src.nx )
                    even_print('ny' , '%i'%hf_src.ny )
                    even_print('nz' , '%i'%hf_src.nz )
                    even_print('nt' , '%i'%hf_src.nt )
                    if verbose: print(72*'-')
                
                if (rx>hf_src.nx):
                    raise AssertionError('rx>nx')
                if (ry>hf_src.ny):
                    raise AssertionError('ry>ny')
                if (rz>hf_src.nz):
                    raise AssertionError('rz>nz')
                if (rt>hf_src.nt):
                    raise AssertionError('rt>nt')
                
                ## for RGD, just load full grid on every rank
                x = np.copy( hf_src.x )
                y = np.copy( hf_src.y )
                z = np.copy( hf_src.z )
                t = np.copy( hf_src.t )
                
                xi = np.arange(hf_src.nx, dtype=np.int64) ## arange index vector, doesnt get touched!
                yi = np.arange(hf_src.ny, dtype=np.int64)
                zi = np.arange(hf_src.nz, dtype=np.int64)
                ti = np.arange(hf_src.nt, dtype=np.int64)
                
                xfi = np.arange(hf_src.nx, dtype=np.int64) ## gets clipped depending on x/y/z/t_min/max opts
                yfi = np.arange(hf_src.ny, dtype=np.int64)
                zfi = np.arange(hf_src.nz, dtype=np.int64)
                tfi = np.arange(hf_src.nt, dtype=np.int64)
                
                # === total bounds clip (coordinate index) --> supports negative indexing!
                
                if True: ## code folding
                    
                    if (xi_min is not None):
                        xfi_ = []
                        if verbose:
                            if (xi_min<0):
                                even_print('xi_min', '%i / %i'%(xi_min,xi[xi_min]))
                            else:
                                even_print('xi_min', '%i'%(xi_min,))
                        for c in xfi:
                            if (xi_min<0) and (c>=(hf_src.nx+xi_min)):
                                xfi_.append(c)
                            elif (xi_min>=0) and (c>=xi_min):
                                xfi_.append(c)
                        xfi=np.array(xfi_, dtype=np.int64)
                    else:
                        xi_min = 0
                    
                    if (xi_max is not None):
                        xfi_ = []
                        if verbose:
                            if (xi_max<0):
                                even_print('xi_max', '%i / %i'%(xi_max,xi[xi_max]))
                            else:
                                even_print('xi_max', '%i'%(xi_max,))
                        for c in xfi:
                            if (xi_max<0) and (c<=(hf_src.nx+xi_max)):
                                xfi_.append(c)
                            elif (xi_max>=0) and (c<=xi_max):
                                xfi_.append(c)
                        xfi=np.array(xfi_, dtype=np.int64)
                    else:
                        xi_max = xi[-1]
                    
                    ## check x
                    if ((xi[xi_max]-xi[xi_min]+1)<1):
                        raise ValueError('invalid xi range requested')
                    if (rx>(xi[xi_max]-xi[xi_min]+1)):
                        raise ValueError('more ranks than grid points in x')
                    
                    if (yi_min is not None):
                        yfi_ = []
                        if verbose:
                            if (yi_min<0):
                                even_print('yi_min', '%i / %i'%(yi_min,yi[yi_min]))
                            else:
                                even_print('yi_min', '%i'%(yi_min,))
                        for c in yfi:
                            if (yi_min<0) and (c>=(hf_src.ny+yi_min)):
                                yfi_.append(c)
                            elif (yi_min>=0) and (c>=yi_min):
                                yfi_.append(c)
                        yfi=np.array(yfi_, dtype=np.int64)
                    else:
                        yi_min = 0
                    
                    if (yi_max is not None):
                        yfi_ = []
                        if verbose:
                            if (yi_max<0):
                                even_print('yi_max', '%i / %i'%(yi_max,yi[yi_max]))
                            else:
                                even_print('yi_max', '%i'%(yi_max,))
                        for c in yfi:
                            if (yi_max<0) and (c<=(hf_src.ny+yi_max)):
                                yfi_.append(c)
                            elif (yi_max>=0) and (c<=yi_max):
                                yfi_.append(c)
                        yfi=np.array(yfi_, dtype=np.int64)
                    else:
                        yi_max = yi[-1]
                    
                    ## check y
                    if ((yi[yi_max]-yi[yi_min]+1)<1):
                        raise ValueError('invalid yi range requested')
                    if (ry>(yi[yi_max]-yi[yi_min]+1)):
                        raise ValueError('more ranks than grid points in y')
                    
                    if (zi_min is not None):
                        zfi_ = []
                        if verbose:
                            if (zi_min<0):
                                even_print('zi_min', '%i / %i'%(zi_min,zi[zi_min]))
                            else:
                                even_print('zi_min', '%i'%(zi_min,))
                        for c in zfi:
                            if (zi_min<0) and (c>=(hf_src.nz+zi_min)):
                                zfi_.append(c)
                            elif (zi_min>=0) and (c>=zi_min):
                                zfi_.append(c)
                        zfi=np.array(zfi_, dtype=np.int64)
                    else:
                        zi_min = 0
                    
                    if (zi_max is not None):
                        zfi_ = []
                        if verbose:
                            if (zi_max<0):
                                even_print('zi_max', '%i / %i'%(zi_max,zi[zi_max]))
                            else:
                                even_print('zi_max', '%i'%(zi_max,))
                        for c in zfi:
                            if (zi_max<0) and (c<=(hf_src.nz+zi_max)):
                                zfi_.append(c)
                            elif (zi_max>=0) and (c<=zi_max):
                                zfi_.append(c)
                        zfi=np.array(zfi_, dtype=np.int64)
                    else:
                        zi_max = zi[-1]
                    
                    ## check z
                    if ((zi[zi_max]-zi[zi_min]+1)<1):
                        raise ValueError('invalid zi range requested')
                    if (rz>(zi[zi_max]-zi[zi_min]+1)):
                        raise ValueError('more ranks than grid points in z')
                    
                    if (ti_min is not None):
                        tfi_ = []
                        if verbose:
                            if (ti_min<0):
                                even_print('ti_min', '%i / %i'%(ti_min,ti[ti_min]))
                            else:
                                even_print('ti_min', '%i'%(ti_min,))
                        for c in tfi:
                            if (ti_min<0) and (c>=(hf_src.nt+ti_min)):
                                tfi_.append(c)
                            elif (ti_min>=0) and (c>=ti_min):
                                tfi_.append(c)
                        tfi=np.array(tfi_, dtype=np.int64)
                    else:
                        ti_min = 0
                    
                    if (ti_max is not None):
                        tfi_ = []
                        if verbose:
                            if (ti_max<0):
                                even_print('ti_max', '%i / %i'%(ti_max,ti[ti_max]))
                            else:
                                even_print('ti_max', '%i'%(ti_max,))
                        for c in tfi:
                            if (ti_max<0) and (c<=(hf_src.nt+ti_max)):
                                tfi_.append(c)
                            elif (ti_max>=0) and (c<=ti_max):
                                tfi_.append(c)
                        tfi=np.array(tfi_, dtype=np.int64)
                    else:
                        ti_max = ti[-1]
                    
                    ## check t
                    if ((ti[ti_max]-ti[ti_min]+1)<1):
                        raise ValueError('invalid ti range requested')
                    if (ct>(ti[ti_max]-ti[ti_min]+1)):
                        raise ValueError('more chunks than timesteps')
                
                # === 3D/4D communicator
                
                comm4d = hf_src.comm.Create_cart(dims=[rx,ry,rz], periods=[False,False,False], reorder=False)
                t4d = comm4d.Get_coords(rank)
                
                rxl_ = np.array_split(xfi,rx)
                ryl_ = np.array_split(yfi,ry)
                rzl_ = np.array_split(zfi,rz)
                #rtl_ = np.array_split(tfi,rt)
                
                rxl = [[b[0],b[-1]+1] for b in rxl_ ]
                ryl = [[b[0],b[-1]+1] for b in ryl_ ]
                rzl = [[b[0],b[-1]+1] for b in rzl_ ]
                #rtl = [[b[0],b[-1]+1] for b in rtl_ ]
                
                ## the rank-local bounds for READ --> takes into acct clip but not step!
                rx1, rx2 = rxl[t4d[0]] #; nxr = rx2 - rx1
                ry1, ry2 = ryl[t4d[1]] #; nyr = ry2 - ry1
                rz1, rz2 = rzl[t4d[2]] #; nzr = rz2 - rz1
                #rt1, rt2 = rtl[t4d[3]] #; ntr = rt2 - rt1
                
                ## the global dim sizes for READ
                nx_read = xfi.shape[0]
                ny_read = yfi.shape[0]
                nz_read = zfi.shape[0]
                
                # === global step
                
                ## take every nth index (of the already bounds-clipped) index-to-take vector
                xfi = np.copy(xfi[::xi_step])
                yfi = np.copy(yfi[::yi_step])
                zfi = np.copy(zfi[::zi_step])
                
                ## the global dim sizes for WRITE
                nx = xfi.shape[0]
                ny = yfi.shape[0]
                nz = zfi.shape[0]
                
                # ===
                
                ## grid for target file (rectilinear case)
                x = np.copy(x[xfi]) ## target file
                y = np.copy(y[yfi])
                z = np.copy(z[zfi])
                t = np.copy(t[tfi])
                
                nx = x.shape[0] ## target file
                ny = y.shape[0]
                nz = z.shape[0]
                nt = t.shape[0]
                
                if verbose:
                    even_print('fn_rgd_tgt' , fn_rgd_tgt )
                    even_print('nx' , '%i'%nx )
                    even_print('ny' , '%i'%ny )
                    even_print('nz' , '%i'%nz )
                    even_print('nt' , '%i'%nt )
                    print(72*'-')
                
                ## REPLACE coordinate dimension arrays in target file
                if ('dims/x' in hf_tgt):
                    del hf_tgt['dims/x']
                    hf_tgt.create_dataset('dims/x', data=x, dtype=np.float64, chunks=None)
                if ('dims/y' in hf_tgt):
                    del hf_tgt['dims/y']
                    hf_tgt.create_dataset('dims/y', data=y, dtype=np.float64, chunks=None)
                if ('dims/z' in hf_tgt):
                    del hf_tgt['dims/z']
                    hf_tgt.create_dataset('dims/z', data=z, dtype=np.float64, chunks=None)
                if ('dims/t' in hf_tgt):
                    del hf_tgt['dims/t']
                    hf_tgt.create_dataset('dims/t', data=t, dtype=np.float64, chunks=None)
                
                # ## write filter index arrays to file
                # if ('filters/xfi' in hf_tgt):
                #     del hf_tgt['filters/xfi']
                # hf_tgt.create_dataset('filters/xfi', data=xfi, dtype=np.int64, chunks=None)
                # if ('filters/yfi' in hf_tgt):
                #     del hf_tgt['filters/yfi']
                # hf_tgt.create_dataset('filters/yfi', data=yfi, dtype=np.int64, chunks=None)
                # if ('filters/zfi' in hf_tgt):
                #     del hf_tgt['filters/zfi']
                # hf_tgt.create_dataset('filters/zfi', data=zfi, dtype=np.int64, chunks=None)
                
                # === bounds for outfile WRITE
                
                xiw     = np.array( [ i for i in xfi if all([(i>=rx1),(i<rx2)]) ], dtype=np.int32 ) ## the global indices in my local rank, taking into acct clip AND step
                nxiw    = xiw.shape[0]
                xiw_off = len([ i for i in xfi if (i<rx1) ]) ## this rank's left offset in the OUTFILE context
                rx1w    = xiw_off
                rx2w    = xiw_off + nxiw
                
                yiw     = np.array( [ i for i in yfi if all([(i>=ry1),(i<ry2)]) ], dtype=np.int32 )
                nyiw    = yiw.shape[0]
                yiw_off = len([ i for i in yfi if (i<ry1) ])
                ry1w    = yiw_off
                ry2w    = yiw_off + nyiw
                
                ziw     = np.array( [ i for i in zfi if all([(i>=rz1),(i<rz2)]) ], dtype=np.int32 )
                nziw    = ziw.shape[0]
                ziw_off = len([ i for i in zfi if (i<rz1) ])
                rz1w    = ziw_off
                rz2w    = ziw_off + nziw
                
                ## xiw,yiw,ziw are used to 'filter' the rank-local data that is read in
                ## xiw,yiw,ziw are currently in the global context, so we need to subtract off the left READ bound
                ## which is NOT just the min xiw
                xiw -= rx1
                yiw -= ry1
                ziw -= rz1
                
                # ===
                
                ## time 'chunks' split (number of timesteps to read / write at a time)
                ctl_ = np.array_split(tfi,ct)
                ctl = [[b[0],b[-1]+1] for b in ctl_ ]
                
                shape  = (nt,nz,ny,nx) ## target
                hf_tgt.scalars = []
                
                # ======================================================
                # initialize
                # ======================================================
                
                if verbose:
                    progress_bar = tqdm(
                        total=len( [ s for s in hf_src.scalars if (s in scalars) ] ),
                        ncols=100,
                        desc='initialize dsets',
                        leave=True,
                        file=sys.stdout,
                        mininterval=0.1,
                        smoothing=0.,
                        #bar_format="\033[B{l_bar}{bar}| {n}/{total} [{percentage:.1f}%] {elapsed}/{remaining}\033[A\n\b",
                        bar_format="{l_bar}{bar}| {n}/{total} [{percentage:.1f}%] {elapsed}/{remaining}",
                        ascii="░█",
                        colour='#FF6600',
                        )
                
                ## initialize scalar datasets
                t_start = timeit.default_timer()
                for scalar in hf_src.scalars:
                    
                    dtype = hf_src.scalars_dtypes_dict[scalar]
                    chunks = h5_chunk_sizer(nxi=shape, constraint=chunk_constraint, size_kb=chunk_kb, base=chunk_base, itemsize=dtype.itemsize)
                    data_gb = dtype.itemsize * nx * ny * nz * nt / 1024**3
                    
                    if (scalar in scalars):
                        if verbose:
                            tqdm.write(even_print(f'initializing data/{scalar}', f'{data_gb:0.2f} [GB]', s=True))
                        
                        dset = hf_tgt.create_dataset(
                                                'data/%s'%scalar,
                                                shape=shape,
                                                dtype=dtype,
                                                chunks=chunks,
                                                )
                        hf_tgt.scalars.append(scalar)
                        
                        chunk_kb_ = np.prod(dset.chunks)*dset.dtype.itemsize / 1024.
                        if verbose:
                            tqdm.write(even_print('chunk shape (t,z,y,x)', str(dset.chunks), s=True))
                            tqdm.write(even_print('chunk size', f'{int(round(chunk_kb_)):d} [KB]', s=True))
                        
                        if verbose:
                            progress_bar.update()
                
                hf_tgt.comm.Barrier()
                if verbose:
                    progress_bar.close()
                
                t_initialize = timeit.default_timer() - t_start
                if verbose:
                    print(72*'-')
                    even_print('time initialize',format_time_string(t_initialize))
                    print(72*'-')
                
                # ===
                
                hf_tgt.n_scalars = len(hf_tgt.scalars)
                
                # ===
                
                data_gb_read  = 0.
                data_gb_write = 0.
                t_read  = 0.
                t_write = 0.
                
                if verbose:
                    progress_bar = tqdm(
                        total=len(ctl)*hf_tgt.n_scalars,
                        ncols=100,
                        desc='copy',
                        leave=True,
                        file=sys.stdout,
                        mininterval=0.1,
                        smoothing=0.,
                        #bar_format="\033[B{l_bar}{bar}| {n}/{total} [{percentage:.1f}%] {elapsed}/{remaining}\033[A\n\b",
                        bar_format="{l_bar}{bar}| {n}/{total} [{percentage:.1f}%] {elapsed}/{remaining}",
                        ascii="░█",
                        colour='#FF6600',
                        )
                
                for scalar in hf_tgt.scalars:
                    dset_src = hf_src[f'data/{scalar}']
                    dset_tgt = hf_tgt[f'data/{scalar}']
                    
                    dtype = dset_src.dtype
                    
                    for ctl_ in ctl:
                        
                        ct1, ct2 = ctl_
                        
                        ct1_ = ct1 - ti[ti_min] ## coords in target file
                        ct2_ = ct2 - ti[ti_min]
                        
                        ## read
                        hf_src.comm.Barrier()
                        t_start = timeit.default_timer()
                        with dset_src.collective:
                            data = dset_src[ct1:ct2,rz1:rz2,ry1:ry2,rx1:rx2].T
                        hf_src.comm.Barrier()
                        t_delta = timeit.default_timer() - t_start
                        data_gb = dtype.itemsize * nx_read * ny_read * nz_read * (ct2-ct1) / 1024**3
                        
                        t_read       += t_delta
                        data_gb_read += data_gb
                        
                        if verbose:
                            tqdm.write(even_print(f'read: {scalar}', f'{data_gb:0.3f} [GB]  {t_delta:0.3f} [s]  {data_gb/t_delta:0.3f} [GB/s]', s=True))
                        
                        try:
                            data_out = np.copy( data[ np.ix_(xiw,yiw,ziw) ] )
                            #data_out = np.copy( data[ xiw[:,np.newaxis,np.newaxis], yiw[np.newaxis,:,np.newaxis], ziw[np.newaxis,np.newaxis,:] ] )
                        except Exception:
                            print('rgd.copy() : error in xiw,yiw,ziw')
                            MPI.COMM_WORLD.Abort(1)
                        
                        ## write
                        hf_tgt.comm.Barrier()
                        t_start = timeit.default_timer()
                        with dset_tgt.collective:
                            dset_tgt[ct1_:ct2_,rz1w:rz2w,ry1w:ry2w,rx1w:rx2w] = data_out.T
                        hf_tgt.flush()
                        hf_tgt.comm.Barrier()
                        t_delta = timeit.default_timer() - t_start
                        data_gb = dtype.itemsize * nx*ny*nz * (ct2-ct1) / 1024**3
                        
                        t_write       += t_delta
                        data_gb_write += data_gb
                        
                        if verbose:
                            tqdm.write(even_print(f'write: {scalar}', f'{data_gb:0.3f} [GB]  {t_delta:0.3f} [s]  {data_gb/t_delta:0.3f} [GB/s]', s=True))
                        
                        if verbose:
                            progress_bar.update()
                
                if verbose:
                    progress_bar.close()
        
        if verbose: print(72*'-')
        if verbose: even_print('time initialize',format_time_string(t_initialize))
        if verbose: even_print('time read',format_time_string(t_read))
        if verbose: even_print('time write',format_time_string(t_write))
        if verbose: even_print('read total avg', f'{data_gb_read:0.2f} [GB]  {t_read:0.2f} [s]  {(data_gb_read/t_read):0.3f} [GB/s]')
        if verbose: even_print('write total avg', f'{data_gb_write:0.2f} [GB]  {t_write:0.2f} [s]  {(data_gb_write/t_write):0.3f} [GB/s]')
        if verbose: print(72*'-')
        if verbose: even_print( os.path.basename(fn_rgd_src), f'{(os.path.getsize(fn_rgd_src)/1024**3):0.2f} [GB]')
        if verbose: even_print( os.path.basename(fn_rgd_tgt), f'{(os.path.getsize(fn_rgd_tgt)/1024**3):0.2f} [GB]')
        if verbose: print(72*'-')
        if verbose: print('total time : rgd.copy() : %s'%format_time_string((timeit.default_timer() - t_start_func)))
        if verbose: print(72*'-')
        return
    
    def make_xdmf(self, **kwargs):
        '''
        Generate an XDMF/XMF2 from RGD for processing with Paraview
        -----
        https://www.xdmf.org/index.php/XDMF_Model_and_Format
        '''
        
        if (self.rank==0):
            verbose = True
        else:
            verbose = False
        
        makeVectors = kwargs.get('makeVectors',True) ## write vectors (e.g. velocity, vorticity) to XDMF
        makeTensors = kwargs.get('makeTensors',True) ## write 3x3 tensors (e.g. stress, strain) to XDMF
        
        fname_path            = os.path.dirname(self.fname)
        fname_base            = os.path.basename(self.fname)
        fname_root, fname_ext = os.path.splitext(fname_base)
        fname_xdmf_base       = fname_root+'.xmf2'
        fname_xdmf            = os.path.join(fname_path, fname_xdmf_base)
        
        if verbose: print('\n'+'rgd.make_xdmf()'+'\n'+72*'-')
        
        dataset_precision_dict = {} ## holds dtype.itemsize ints i.e. 4,8
        dataset_numbertype_dict = {} ## holds string description of dtypes i.e. 'Float','Integer'
        
        # === 1D coordinate dimension vectors --> get dtype.name
        for scalar in ['x','y','z']:
            if ('dims/'+scalar in self):
                data = self['dims/'+scalar]
                dataset_precision_dict[scalar] = data.dtype.itemsize
                if (data.dtype.name=='float32') or (data.dtype.name=='float64'):
                    dataset_numbertype_dict[scalar] = 'Float'
                elif (data.dtype.name=='int8') or (data.dtype.name=='int16') or (data.dtype.name=='int32') or (data.dtype.name=='int64'):
                    dataset_numbertype_dict[scalar] = 'Integer'
                else:
                    raise ValueError('dtype not recognized, please update script accordingly')
        
        # scalar names dict
        # --> labels for Paraview could be customized (e.g. units could be added) using a dict
        # --> the block below shows one such example dict, though it is currently inactive
        
        if False:
            units = 'dimless'
            if (units=='SI') or (units=='si'): ## m,s,kg,K
                scalar_names = {'x':'x [m]',
                                'y':'y [m]',
                                'z':'z [m]', 
                                'u':'u [m/s]',
                                'v':'v [m/s]',
                                'w':'w [m/s]', 
                                'T':'T [K]',
                                'rho':'rho [kg/m^3]',
                                'p':'p [Pa]'}
            elif (units=='dimless') or (units=='dimensionless'):
                scalar_names = {'x':'x [dimless]',
                                'y':'y [dimless]',
                                'z':'z [dimless]', 
                                'u':'u [dimless]',
                                'v':'v [dimless]',
                                'w':'w [dimless]',
                                'T':'T [dimless]',
                                'rho':'rho [dimless]',
                                'p':'p [dimless]'}
            else:
                raise ValueError('choice of units not recognized : %s --> options are : %s / %s'%(units,'SI','dimless'))
        else:
            scalar_names = {} ## dummy/empty 
        
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
                perms_h5 = oct(os.stat(self.fname).st_mode)[-3:] ## get permissions of RGD file
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
                
                ## Dimensions can also be NumberOfElements
                xdmf_str=f'''
                         <Topology TopologyType="3DRectMesh" NumberOfElements="{self.nz:d} {self.ny:d} {self.nx:d}"/>
                         <Geometry GeometryType="VxVyVz">
                           <DataItem Dimensions="{self.nx:d}" NumberType="{dataset_numbertype_dict['x']}" Precision="{dataset_precision_dict['x']:d}" Format="HDF">
                             {fname_base}:/dims/{'x'}
                           </DataItem>
                           <DataItem Dimensions="{self.ny:d}" NumberType="{dataset_numbertype_dict['y']}" Precision="{dataset_precision_dict['y']:d}" Format="HDF">
                             {fname_base}:/dims/{'y'}
                           </DataItem>
                           <DataItem Dimensions="{self.nz:d}" NumberType="{dataset_numbertype_dict['z']}" Precision="{dataset_precision_dict['z']:d}" Format="HDF">
                             {fname_base}:/dims/{'z'}
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
                    
                    # =====
                    
                    xdmf_str=f'''
                             <Grid Name="{dset_name}" GridType="Uniform">
                               <Time TimeType="Single" Value="{self.t[ti]:0.8E}"/>
                               <Topology Reference="/Xdmf/Domain/Topology[1]" />
                               <Geometry Reference="/Xdmf/Domain/Geometry[1]" />
                             '''
                    
                    xdmf.write(textwrap.indent(textwrap.dedent(xdmf_str.strip('\n')), 6*' '))
                    
                    # ===== .xdmf : <Grid> per scalar
                    
                    for scalar in self.scalars:
                        
                        dset_hf_path = 'data/%s'%scalar
                        
                        ## get optional 'label' for Paraview (currently inactive)
                        if scalar in scalar_names:
                            scalar_name = scalar_names[scalar]
                        else:
                            scalar_name = scalar
                        
                        xdmf_str=f'''
                                 <!-- ===== scalar : {scalar} ===== -->
                                 <Attribute Name="{scalar_name}" AttributeType="Scalar" Center="Node">
                                   <DataItem ItemType="HyperSlab" Dimensions="{self.nz:d} {self.ny:d} {self.nx:d}" Type="HyperSlab">
                                     <DataItem Dimensions="3 4" NumberType="Integer" Format="XML">
                                       {ti:<6d} {0:<6d} {0:<6d} {0:<6d}
                                       {1:<6d} {1:<6d} {1:<6d} {1:<6d}
                                       {1:<6d} {self.nz:<6d} {self.ny:<6d} {self.nx:<6d}
                                     </DataItem>
                                     <DataItem Dimensions="{self.nt:d} {self.nz:d} {self.ny:d} {self.nx:d}" NumberType="{dataset_numbertype_dict[scalar]}" Precision="{dataset_precision_dict[scalar]:d}" Format="HDF">
                                       {fname_base}:/{dset_hf_path}
                                     </DataItem>
                                   </DataItem>
                                 </Attribute>
                                 '''
                        
                        xdmf.write(textwrap.indent(textwrap.dedent(xdmf_str.strip('\n')), 8*' '))
                    
                    if makeVectors:
                        
                        # === .xdmf : <Grid> per vector : velocity vector
                        
                        if ('u' in self.scalars) and ('v' in self.scalars) and ('w' in self.scalars):
                            
                            scalar_name    = 'velocity'
                            dset_hf_path_i = 'data/u'
                            dset_hf_path_j = 'data/v'
                            dset_hf_path_k = 'data/w'
                            
                            xdmf_str = f'''
                            <!-- ===== vector : {scalar_name} ===== -->
                            <Attribute Name="{scalar_name}" AttributeType="Vector" Center="Node">
                              <DataItem Dimensions="{self.nz:d} {self.ny:d} {self.nx:d} {3:d}" Function="JOIN($0, $1, $2)" ItemType="Function">
                                <!-- 1 -->
                                <DataItem ItemType="HyperSlab" Dimensions="{self.nz:d} {self.ny:d} {self.nx:d}" Type="HyperSlab">
                                  <DataItem Dimensions="3 4" NumberType="Integer" Format="XML">
                                    {ti:<6d} {0:<6d} {0:<6d} {0:<6d}
                                    {1:<6d} {1:<6d} {1:<6d} {1:<6d}
                                    {1:<6d} {self.nz:<6d} {self.ny:<6d} {self.nx:<6d}
                                  </DataItem>
                                  <DataItem Dimensions="{self.nt:d} {self.nz:d} {self.ny:d} {self.nx:d}" NumberType="{dataset_numbertype_dict['u']}" Precision="{dataset_precision_dict['u']:d}" Format="HDF">
                                    {fname_base}:/{dset_hf_path_i}
                                  </DataItem>
                                </DataItem>
                                <!-- 2 -->
                                <DataItem ItemType="HyperSlab" Dimensions="{self.nz:d} {self.ny:d} {self.nx:d}" Type="HyperSlab">
                                  <DataItem Dimensions="3 4" NumberType="Integer" Format="XML">
                                    {ti:<6d} {0:<6d} {0:<6d} {0:<6d}
                                    {1:<6d} {1:<6d} {1:<6d} {1:<6d}
                                    {1:<6d} {self.nz:<6d} {self.ny:<6d} {self.nx:<6d}
                                  </DataItem>
                                  <DataItem Dimensions="{self.nt:d} {self.nz:d} {self.ny:d} {self.nx:d}" NumberType="{dataset_numbertype_dict['v']}" Precision="{dataset_precision_dict['v']:d}" Format="HDF">
                                    {fname_base}:/{dset_hf_path_j}
                                  </DataItem>
                                </DataItem>
                                <!-- 3 -->
                                <DataItem ItemType="HyperSlab" Dimensions="{self.nz:d} {self.ny:d} {self.nx:d}" Type="HyperSlab">
                                  <DataItem Dimensions="3 4" NumberType="Integer" Format="XML">
                                    {ti:<6d} {0:<6d} {0:<6d} {0:<6d}
                                    {1:<6d} {1:<6d} {1:<6d} {1:<6d}
                                    {1:<6d} {self.nz:<6d} {self.ny:<6d} {self.nx:<6d}
                                  </DataItem>
                                  <DataItem Dimensions="{self.nt:d} {self.nz:d} {self.ny:d} {self.nx:d}" NumberType="{dataset_numbertype_dict['w']}" Precision="{dataset_precision_dict['w']:d}" Format="HDF">
                                    {fname_base}:/{dset_hf_path_k}
                                  </DataItem>
                                </DataItem>
                                <!-- - -->
                              </DataItem>
                            </Attribute>
                            '''
                            
                            xdmf.write(textwrap.indent(textwrap.dedent(xdmf_str.strip('\n')), 8*' '))
                        
                        # === .xdmf : <Grid> per vector : vorticity vector
                        
                        if ('vort_x' in self.scalars) and ('vort_y' in self.scalars) and ('vort_z' in self.scalars):
                            
                            scalar_name    = 'vorticity'
                            dset_hf_path_i = 'data/vort_x'
                            dset_hf_path_j = 'data/vort_y'
                            dset_hf_path_k = 'data/vort_z'
                            
                            xdmf_str = f'''
                            <!-- ===== vector : {scalar_name} ===== -->
                            <Attribute Name="{scalar_name}" AttributeType="Vector" Center="Node">
                              <DataItem Dimensions="{self.nz:d} {self.ny:d} {self.nx:d} {3:d}" Function="JOIN($0, $1, $2)" ItemType="Function">
                                <!-- 1 -->
                                <DataItem ItemType="HyperSlab" Dimensions="{self.nz:d} {self.ny:d} {self.nx:d}" Type="HyperSlab">
                                  <DataItem Dimensions="3 4" NumberType="Integer" Format="XML">
                                    {ti:<6d} {0:<6d} {0:<6d} {0:<6d}
                                    {1:<6d} {1:<6d} {1:<6d} {1:<6d}
                                    {1:<6d} {self.nz:<6d} {self.ny:<6d} {self.nx:<6d}
                                  </DataItem>
                                  <DataItem Dimensions="{self.nt:d} {self.nz:d} {self.ny:d} {self.nx:d}" NumberType="{dataset_numbertype_dict['vort_x']}" Precision="{dataset_precision_dict['vort_x']:d}" Format="HDF">
                                    {fname_base}:/{dset_hf_path_i}
                                  </DataItem>
                                </DataItem>
                                <!-- 2 -->
                                <DataItem ItemType="HyperSlab" Dimensions="{self.nz:d} {self.ny:d} {self.nx:d}" Type="HyperSlab">
                                  <DataItem Dimensions="3 4" NumberType="Integer" Format="XML">
                                    {ti:<6d} {0:<6d} {0:<6d} {0:<6d}
                                    {1:<6d} {1:<6d} {1:<6d} {1:<6d}
                                    {1:<6d} {self.nz:<6d} {self.ny:<6d} {self.nx:<6d}
                                  </DataItem>
                                  <DataItem Dimensions="{self.nt:d} {self.nz:d} {self.ny:d} {self.nx:d}" NumberType="{dataset_numbertype_dict['vort_y']}" Precision="{dataset_precision_dict['vort_y']:d}" Format="HDF">
                                    {fname_base}:/{dset_hf_path_j}
                                  </DataItem>
                                </DataItem>
                                <!-- 3 -->
                                <DataItem ItemType="HyperSlab" Dimensions="{self.nz:d} {self.ny:d} {self.nx:d}" Type="HyperSlab">
                                  <DataItem Dimensions="3 4" NumberType="Integer" Format="XML">
                                    {ti:<6d} {0:<6d} {0:<6d} {0:<6d}
                                    {1:<6d} {1:<6d} {1:<6d} {1:<6d}
                                    {1:<6d} {self.nz:<6d} {self.ny:<6d} {self.nx:<6d}
                                  </DataItem>
                                  <DataItem Dimensions="{self.nt:d} {self.nz:d} {self.ny:d} {self.nx:d}" NumberType="{dataset_numbertype_dict['vort_z']}" Precision="{dataset_precision_dict['vort_z']:d}" Format="HDF">
                                    {fname_base}:/{dset_hf_path_k}
                                  </DataItem>
                                </DataItem>
                                <!-- - -->
                              </DataItem>
                            </Attribute>
                            '''
                            
                            xdmf.write(textwrap.indent(textwrap.dedent(xdmf_str.strip('\n')), 8*' '))
                    
                    if makeTensors:
                        if all([('dudx' in self.scalars),('dvdx' in self.scalars),('dwdx' in self.scalars),
                                ('dudy' in self.scalars),('dvdy' in self.scalars),('dwdy' in self.scalars),
                                ('dudz' in self.scalars),('dvdz' in self.scalars),('dwdz' in self.scalars)]):
                            pass
                            pass ## TODO
                            pass
                    
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
        
        if self.usingmpi:
            self.comm.Barrier()
        if verbose: print('--w-> %s'%fname_xdmf_base)
        return
    
    # ==================================================================
    # External attachments
    # ==================================================================
    
    def calc_mean(self, **kwargs):
        return _calc_mean(self, **kwargs)
    
    def calc_lambda2(self, **kwargs):
        return _calc_lambda2(self, **kwargs)
    
    # === [x] plane
    
    def add_mean_dimensional_data_xpln(self, **kwargs):
        return _add_mean_dimensional_data_xpln(self, **kwargs)
    
    def calc_turb_cospectrum_xpln(self, **kwargs):
        return _calc_turb_cospectrum_xpln(self, **kwargs)
    
    def calc_wall_coh_xpln(self, **kwargs):
        return _calc_wall_coh_xpln(self, **kwargs)
    
    def calc_ccor_xpln(self, **kwargs):
        return _calc_ccor_xpln(self, **kwargs)
    
    def calc_statistics_xpln(self,**kwargs):
        return _calc_statistics_xpln(self,**kwargs)
    
    def calc_turb_budget_xpln(self,**kwargs):
        return _calc_turb_budget_xpln(self,**kwargs)
