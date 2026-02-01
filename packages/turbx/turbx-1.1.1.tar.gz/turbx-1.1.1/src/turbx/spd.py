import io
import os
import re
import shutil
import subprocess
import sys
import textwrap
import time
import timeit
from pathlib import Path

import h5py
import numpy as np
from mpi4py import MPI
from tqdm import tqdm

from .h5 import h5_chunk_sizer
from .spd_wall_ccor import _calc_ccor_wall
from .spd_wall_ci import _calc_mean_uncertainty_BMBC
from .spd_wall_import import _import_eas4_wall, _init_from_eas4_wall
from .spd_wall_spectrum import _calc_turb_cospectrum_wall
from .spd_wall_stats import _calc_statistics_wall
from .utils import even_print, format_time_string

# ======================================================================

class spd(h5py.File):
    '''
    Surface Polydata (SPD)
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
            raise ValueError('EAS4 files should not be opened with turbx.spd()')
        
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
        
        ## spd() unique kwargs (not h5py.File kwargs) --> pop() rather than get()
        stripe_count   = kwargs.pop('stripe_count'   , 16    )
        stripe_size_mb = kwargs.pop('stripe_size_mb' , 2     )
        perms          = kwargs.pop('perms'          , '640' )
        no_indep_rw    = kwargs.pop('no_indep_rw'    , False )
        
        if not isinstance(stripe_count, int):
            raise ValueError
        if not isinstance(stripe_size_mb, int):
            raise ValueError
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
        ## | export ROMIO_FSTYPE_FORCE="lustre:" --> force Lustre driver over UFS when using romio --> causes crash
        ## | export ROMIO_FSTYPE_FORCE="ufs:"
        ## | export ROMIO_PRINT_HINTS=1 --> show available hints
        ##
        ## https://doku.lrz.de/best-practices-hints-and-optimizations-for-io-10747318.html
        ##
        ## OMPIO
        ## export OMPI_MCA_sharedfp=^lockedfile,individual
        ## mpiexec --mca io ompio -n $NP python3 script.py
        
        ## set MPI hints, passed through 'mpi_info' dict
        if self.usingmpi:
            if ('info' in kwargs):
                self.mpi_info = kwargs['info']
            else:
                mpi_info = MPI.Info.Create()
                
                ## ROMIO only ... ignored if OMPIO is used
                mpi_info.Set('romio_ds_write' , 'disable'   )
                mpi_info.Set('romio_ds_read'  , 'disable'   )
                #mpi_info.Set('romio_cb_read'  , 'automatic' )
                #mpi_info.Set('romio_cb_write' , 'automatic' )
                mpi_info.Set('romio_cb_read'  , 'enable' )
                mpi_info.Set('romio_cb_write' , 'enable' )
                
                ## ROMIO -- collective buffer size
                mpi_info.Set('cb_buffer_size' , str(int(round(1*1024**3))) ) ## 1 [GB]
                
                ## ROMIO -- force collective I/O
                if no_indep_rw:
                    mpi_info.Set('romio_no_indep_rw' , 'true' )
                
                ## cb_nodes: number of aggregator processes
                #mpi_info.Set('cb_nodes' , str(min(16,self.n_ranks//2)) )
                mpi_info.Set('cb_nodes' , str(min(16,self.n_ranks)) )
                
                kwargs['info'] = mpi_info
                self.mpi_info = mpi_info
        
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
        
        ## spd() unique kwargs (not h5py.File kwargs) --> pop() rather than get()
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
                                  
                                  >>> with spd(<<fname>>,'w',force=True) as f:
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
                    time.sleep(1)
        
        if (self.comm is not None):
            self.comm.Barrier()
        
        self.mod_avail_tqdm = ('tqdm' in sys.modules)
        
        ## call actual h5py.File.__init__()
        super(spd, self).__init__(*args, **kwargs)
        self.get_header(verbose=verbose)
    
    def get_header(self,**kwargs):
        '''
        initialize header attributes of SPD class instance
        '''
        
        verbose = kwargs.get('verbose',True)
        
        if (self.rank!=0):
            verbose=False
        
        # === udef (header vector dset based) --> the 'old' way but still present in RGD,CGD
        
        if ('header' in self):
            
            udef_real = np.copy(self['header/udef_real'][:])
            udef_char = np.copy(self['header/udef_char'][:]) ## the unpacked numpy array of |S128 encoded fixed-length character objects
            udef_char = [s.decode('utf-8') for s in udef_char] ## convert it to a python list of utf-8 strings
            self.udef = dict(zip(udef_char, udef_real)) ## make dict where keys are udef_char and values are udef_real
            
            # === characteristic values
            
            self.Ma          = self.udef['Ma']
            self.Re          = self.udef['Re']
            self.Pr          = self.udef['Pr']
            self.kappa       = self.udef['kappa']
            self.R           = self.udef['R']
            self.p_inf       = self.udef['p_inf']
            self.T_inf       = self.udef['T_inf']
            self.mu_Suth_ref = self.udef['mu_Suth_ref']
            self.T_Suth_ref  = self.udef['T_Suth_ref']
            self.S_Suth      = self.udef['S_Suth']
            #self.C_Suth      = self.udef['C_Suth']
            
            self.C_Suth = self.mu_Suth_ref/(self.T_Suth_ref**(3/2))*(self.T_Suth_ref + self.S_Suth) ## [kg/(m·s·√K)]
            self.udef['C_Suth'] = self.C_Suth
            
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
            
            # === characteristic values : derived
            
            ## mu_inf_1 = 14.58e-7*self.T_inf**1.5/(self.T_inf+110.4)
            ## mu_inf_2 = self.mu_Suth_ref*(self.T_inf/self.T_Suth_ref)**(3/2) * ((self.T_Suth_ref+self.S_Suth)/(self.T_inf+self.S_Suth))
            ## mu_inf_3 = self.C_Suth*self.T_inf**(3/2)/(self.T_inf+self.S_Suth)
            ## if not np.isclose(mu_inf_1, mu_inf_2, rtol=1e-14):
            ##     raise AssertionError('inconsistency in Sutherland calc --> check')
            ## if not np.isclose(mu_inf_2, mu_inf_3, rtol=1e-14):
            ##     raise AssertionError('inconsistency in Sutherland calc --> check')
            ## mu_inf = self.mu_inf = mu_inf_2
            
            self.mu_inf    = self.mu_Suth_ref*(self.T_inf/self.T_Suth_ref)**(3/2) * ((self.T_Suth_ref+self.S_Suth)/(self.T_inf+self.S_Suth))
            self.rho_inf   = self.p_inf/(self.R*self.T_inf)
            self.nu_inf    = self.mu_inf/self.rho_inf
            self.a_inf     = np.sqrt(self.kappa*self.R*self.T_inf)
            self.U_inf     = self.Ma*self.a_inf
            self.cp        = self.R*self.kappa/(self.kappa-1.)
            self.cv        = self.cp/self.kappa
            self.recov_fac = self.Pr**(1/3)
            self.Taw       = self.T_inf + self.recov_fac*self.U_inf**2/(2*self.cp)
            self.lchar     = self.Re*self.nu_inf/self.U_inf
            
            self.tchar = self.lchar / self.U_inf
            self.uchar = self.U_inf
            
            if verbose: print(72*'-')
            if verbose: even_print('rho_inf'         , '%0.3f [kg/m³]'    % self.rho_inf   )
            if verbose: even_print('mu_inf'          , '%0.6E [kg/(m·s)]' % self.mu_inf    )
            if verbose: even_print('nu_inf'          , '%0.6E [m²/s]'     % self.nu_inf    )
            if verbose: even_print('a_inf'           , '%0.6f [m/s]'      % self.a_inf     )
            if verbose: even_print('U_inf'           , '%0.6f [m/s]'      % self.U_inf     )
            if verbose: even_print('cp'              , '%0.3f [J/(kg·K)]' % self.cp        )
            if verbose: even_print('cv'              , '%0.3f [J/(kg·K)]' % self.cv        )
            if verbose: even_print('recovery factor' , '%0.6f [-]'        % self.recov_fac )
            if verbose: even_print('Taw'             , '%0.3f [K]'        % self.Taw       )
            if verbose: even_print('lchar'           , '%0.6E [m]'        % self.lchar     )
            if verbose: even_print('tchar'           , '%0.6E [s]'        % self.tchar     )
            #if verbose: print(72*'-'+'\n')
            #if verbose: print(72*'-')
            
            # === write the 'derived' udef variables to a dict attribute of the SPD instance
            self.udef_deriv = { 'rho_inf':self.rho_inf,
                                'mu_inf':self.mu_inf,
                                'nu_inf':self.nu_inf,
                                'a_inf':self.a_inf,
                                'U_inf':self.U_inf,
                                'cp':self.cp,
                                'cv':self.cv,
                                'recov_fac':self.recov_fac,
                                'Taw':self.Taw,
                                'lchar':self.lchar,
                              }
        
        else:
            #print("dset 'header' not in SPD")
            pass
        
        # === udef (attr based)
        
        header_attr_str_list = ['Ma','Re','Pr','kappa','R','p_inf','T_inf','S_Suth','mu_Suth_ref','T_Suth_ref'] ## ,'C_Suth'
        if all([ attr_str in self.attrs.keys() for attr_str in header_attr_str_list ]):
            header_attr_based = True
        else:
            header_attr_based = False
        
        if header_attr_based:
            
            ## set all attributes
            for attr_str in header_attr_str_list:
                setattr( self, attr_str, self.attrs[attr_str] )
            
            self.C_Suth = self.mu_Suth_ref/(self.T_Suth_ref**(3/2))*(self.T_Suth_ref + self.S_Suth) ## [kg/(m·s·√K)]
            #self.udef['C_Suth'] = self.C_Suth
            
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
            
            # === characteristic values : derived
            
            ## mu_inf_1 = 14.58e-7*self.T_inf**1.5/(self.T_inf+110.4)
            ## mu_inf_2 = self.mu_Suth_ref*(self.T_inf/self.T_Suth_ref)**(3/2) * ((self.T_Suth_ref+self.S_Suth)/(self.T_inf+self.S_Suth))
            ## mu_inf_3 = self.C_Suth*self.T_inf**(3/2)/(self.T_inf+self.S_Suth)
            ## if not np.isclose(mu_inf_1, mu_inf_2, rtol=1e-14):
            ##     raise AssertionError('inconsistency in Sutherland calc --> check')
            ## if not np.isclose(mu_inf_2, mu_inf_3, rtol=1e-14):
            ##     raise AssertionError('inconsistency in Sutherland calc --> check')
            ## mu_inf = self.mu_inf = mu_inf_2
            
            self.mu_inf    = self.mu_Suth_ref*(self.T_inf/self.T_Suth_ref)**(3/2) * ((self.T_Suth_ref+self.S_Suth)/(self.T_inf+self.S_Suth))
            self.rho_inf   = self.p_inf/(self.R*self.T_inf)
            self.nu_inf    = self.mu_inf/self.rho_inf
            self.a_inf     = np.sqrt(self.kappa*self.R*self.T_inf)
            self.U_inf     = self.Ma*self.a_inf
            self.cp        = self.R*self.kappa/(self.kappa-1.)
            self.cv        = self.cp/self.kappa
            self.recov_fac = self.Pr**(1/3)
            self.Taw       = self.T_inf + self.recov_fac*self.U_inf**2/(2*self.cp)
            self.lchar     = self.Re*self.nu_inf/self.U_inf
            
            self.tchar = self.lchar / self.U_inf
            self.uchar = self.U_inf
            
            if verbose: print(72*'-')
            if verbose: even_print('rho_inf'         , '%0.3f [kg/m³]'    % self.rho_inf   )
            if verbose: even_print('mu_inf'          , '%0.6E [kg/(m·s)]' % self.mu_inf    )
            if verbose: even_print('nu_inf'          , '%0.6E [m²/s]'     % self.nu_inf    )
            if verbose: even_print('a_inf'           , '%0.6f [m/s]'      % self.a_inf     )
            if verbose: even_print('U_inf'           , '%0.6f [m/s]'      % self.U_inf     )
            if verbose: even_print('cp'              , '%0.3f [J/(kg·K)]' % self.cp        )
            if verbose: even_print('cv'              , '%0.3f [J/(kg·K)]' % self.cv        )
            if verbose: even_print('recovery factor' , '%0.6f [-]'        % self.recov_fac )
            if verbose: even_print('Taw'             , '%0.3f [K]'        % self.Taw       )
            if verbose: even_print('lchar'           , '%0.6E [m]'        % self.lchar     )
            if verbose: even_print('tchar'           , '%0.6E [s]'        % self.tchar     )
            #if verbose: print(72*'-'+'\n')
            if verbose: print(72*'-')
            
            # === write the 'derived' udef variables to a dict attribute of the RGD instance
            self.udef_deriv = { 'rho_inf':self.rho_inf,
                                'mu_inf':self.mu_inf,
                                'nu_inf':self.nu_inf,
                                'a_inf':self.a_inf,
                                'U_inf':self.U_inf,
                                'cp':self.cp,
                                'cv':self.cv,
                                'recov_fac':self.recov_fac,
                                'Taw':self.Taw,
                                'lchar':self.lchar,
                              }
        
        #if ('duration_avg' in self.attrs.keys()):
        #    self.duration_avg = self.attrs['duration_avg']
        #if ('nx' in self.attrs.keys()):
        #    self.nx = self.attrs['nx']
        #if ('ny' in self.attrs.keys()):
        #    self.ny = self.attrs['ny']
        
        # if ('p_inf' in self.attrs.keys()):
        #     self.p_inf = self.attrs['p_inf']
        # if ('lchar' in self.attrs.keys()):
        #     self.lchar = self.attrs['lchar']
        # if ('U_inf' in self.attrs.keys()):
        #     self.U_inf = self.attrs['U_inf']
        # if ('Re' in self.attrs.keys()):
        #     self.Re = self.attrs['Re']
        # if ('T_inf' in self.attrs.keys()):
        #     self.T_inf = self.attrs['T_inf']
        # if ('rho_inf' in self.attrs.keys()):
        #     self.rho_inf = self.attrs['rho_inf']
        
        if 0: ## could potentially be big
            if ('dims/xyz' in self):
                self.xyz = np.copy( self['dims/xyz'][()] )
        if ('dims/stang' in self):
            self.stang = np.copy( self['dims/stang'][()] )
        if ('dims/snorm' in self):
            self.snorm = np.copy( self['dims/snorm'][()] )
        if ('dims/crv_R' in self):
            self.crv_R = np.copy( self['dims/crv_R'][()] )
        
        if ('n_quads' in self.attrs.keys()):
            self.n_quads = int( self.attrs['n_quads'] )
        if ('n_pts' in self.attrs.keys()):
            self.n_pts = int( self.attrs['n_pts'] )
        if ('ni' in self.attrs.keys()):
            self.ni = int( self.attrs['ni'] )
        if ('nj' in self.attrs.keys()):
            self.nj = int( self.attrs['nj'] )
        
        if ('nt' in self.attrs.keys()):
            self.nt = int( self.attrs['nt'] )
        
        if ('dims/t' in self):
            self.t = np.copy( self['dims/t'][()] )
        if hasattr(self,'t'):
            if (self.t.ndim!=1):
                raise ValueError('self.t.ndim!=1')
            nt = self.t.shape[0]
            
            if hasattr(self,'nt'):
                if not isinstance(self.nt, (int,np.int32,np.int64)):
                    raise TypeError('self.nt is not type int')
                if (self.nt != nt):
                    raise ValueError('self.nt != nt')
            else:
                #self.attrs['nt'] = nt
                self.nt = nt
        
        ## check n_quads / n_pts is consistent with xyz
        ## if xyz exists and attrs n_quads/n_pts do not exist, set them
        if hasattr(self,'xyz'):
            if (self.xyz.ndim!=3):
                raise ValueError('self.xyz.ndim!=3')
            ni,nj,three = self.xyz.shape
            
            if hasattr(self,'ni'):
                if not isinstance(self.ni, (int,np.int32,np.int64)):
                    raise TypeError('self.ni is not type int')
                if (self.ni != ni):
                    raise ValueError('self.ni != ni')
            else:
                #self.attrs['ni'] = ni
                self.ni = ni
            
            if hasattr(self,'nj'):
                if not isinstance(self.nj, (int,np.int32,np.int64)):
                    raise TypeError('self.nj is not type int')
                if (self.nj != nj):
                    raise ValueError('self.nj != nj')
            else:
                #self.attrs['nj'] = nj
                self.nj = nj
            
            if hasattr(self,'n_quads'):
                if not isinstance(self.n_quads, (int,np.int32,np.int64)):
                    raise TypeError('self.n_quads is not type int')
                if (self.n_quads != (ni-1)*(nj-1)):
                    raise ValueError('self.n_quads != (ni-1)*(nj-1)')
            else:
                #self.attrs['n_quads'] = (ni-1)*(nj-1)
                self.n_quads = (ni-1)*(nj-1)
            
            if hasattr(self,'n_pts'):
                if not isinstance(self.n_pts, (int,np.int32,np.int64)):
                    raise TypeError('self.n_pts is not type int')
                if (self.n_pts != ni*nj):
                    raise ValueError('self.n_pts != ni*nj')
            else:
                #self.attrs['n_pts'] = ni*nj
                self.n_pts = ni*nj
        
        if any([hasattr(self,'ni'), hasattr(self,'nj'), hasattr(self,'n_quads'), hasattr(self,'n_pts') ]):
            if verbose and hasattr(self,'nt'):      even_print('nt',      f'{self.nt:d}')
            if verbose and hasattr(self,'ni'):      even_print('ni',      f'{self.ni:d}')
            if verbose and hasattr(self,'nj'):      even_print('nj',      f'{self.nj:d}')
            if verbose and hasattr(self,'n_quads'): even_print('n_quads', f'{self.n_quads:d}')
            if verbose and hasattr(self,'n_pts'):   even_print('n_pts',   f'{self.n_pts:d}')
            #if verbose: print(72*'-')
        
        # === ts group names & scalars
        
        if ('data' in self):
            #self.scalars = list(self['data'].keys())
            self.scalars = [ k for k,v in self['data'].items() if isinstance(v,h5py.Dataset) ]
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
    
    def gen_unstruct_xyz(self,**kwargs):
        '''
        convert structured grid coords (data/xyz) to unstructured:
        dims/quads
        dims/pts
        '''
        
        verbose    = kwargs.get( 'verbose'    , True )
        #indexing   = kwargs.get( 'indexing'   , 'xy' ) ## 'xy', 'ij'
        chunk_kb   = kwargs.get( 'chunk_kb'   , 1*1024 ) ## 1 [MB]
        chunk_base = kwargs.get( 'chunk_base' , 2 )
        
        if self.usingmpi:
            raise ValueError('spd.gen_unstruct_xyz() should not be run in MPI mode')
        
        if ('dims/xyz' not in self):
            raise ValueError('dims/xyz not in file')
        
        if verbose: print('\n'+'spd.gen_unstruct_xyz()'+'\n'+72*'-')
        t_start_func = timeit.default_timer()
        
        xyz = np.copy( self['dims/xyz'][()] )
        if verbose:
            even_print('dims/xyz',str(xyz.shape))
        
        if (xyz.ndim!=3):
            raise ValueError('xyz.ndim!=3')
        
        ni,nj,three = xyz.shape
        
        n_quads = (ni-1)*(nj-1)
        n_pts   = ni*nj
        nt      = self.nt
        
        if verbose:
            even_print('ni'      , f'{ni:d}' )
            even_print('nj'      , f'{nj:d}' )
            even_print('n_quads' , f'{n_quads:d}' )
            even_print('n_pts'   , f'{n_pts:d}' )
            even_print('nt'      , f'{nt:d}' )
        
        # ===
        
        indexing = 'xy'
        
        xi, yi = np.meshgrid(np.arange(ni,dtype=np.int64), np.arange(nj,dtype=np.int64), indexing=indexing)
        
        inds_list = np.stack((xi,yi), axis=2)
        inds_list = np.reshape(inds_list, (ni*nj,2), order='C')
        inds_list = np.ravel_multi_index((inds_list[:,0],inds_list[:,1]), (ni,nj), order='F')
        inds_list = np.reshape(inds_list, (ni,nj), order='C')
        
        if verbose:
            progress_bar = tqdm(
                total=(ni-1)*(nj-1),
                ncols=100,
                desc='quads',
                leave=True,
                file=sys.stdout,
                mininterval=0.1,
                smoothing=0.,
                #bar_format="\033[B{l_bar}{bar}| {n}/{total} [{percentage:.1f}%] {elapsed}/{remaining}\033[A\n\b",
                bar_format="{l_bar}{bar}| {n}/{total} [{percentage:.1f}%] {elapsed}/{remaining}",
                ascii="░█",
                colour='#FF6600',
                )
        
        ## quad index array
        quads = np.zeros(((ni-1),(nj-1),4), dtype=np.int64)
        for i in range(ni-1):
            for j in range(nj-1):
                
                ## Counter-Clockwise (CCW)
                quads[i,j,0] = inds_list[i,   j  ]
                quads[i,j,1] = inds_list[i+1, j  ]
                quads[i,j,2] = inds_list[i+1, j+1]
                quads[i,j,3] = inds_list[i,   j+1]
                
                ## Clockwise (CW)
                #quads[i,j,0] = inds_list[i,   j  ]
                #quads[i,j,1] = inds_list[i,   j+1]
                #quads[i,j,2] = inds_list[i+1, j+1]
                #quads[i,j,3] = inds_list[i+1, j  ]
                
                if verbose: progress_bar.update()
        if verbose: progress_bar.close()
        
        # ===
        
        if (indexing=='xy'):
            order='C'
        elif (indexing=='ij'):
            order = 'F'
        else:
            raise ValueError
        
        # === dims_unstruct/quads
        
        ## flatten quad index vector
        quads = np.reshape(quads, ((ni-1)*(nj-1),4), order=order)
        
        dsn = 'dims/quads'
        if (dsn in self):
            del self[dsn]
        
        shape = quads.shape
        dtype = quads.dtype
        itemsize = quads.dtype.itemsize
        chunks = h5_chunk_sizer(nxi=shape, constraint=(None,None), size_kb=chunk_kb, base=chunk_base, itemsize=itemsize)
        ds = self.create_dataset(
                            dsn,
                            shape=shape,
                            chunks=chunks,
                            dtype=dtype,
                            )
        
        chunk_kb_ = np.prod(ds.chunks)*itemsize / 1024. ## actual
        if verbose:
            even_print('chunk shape (n_quads,4)','%s'%str(ds.chunks))
            even_print('chunk size','%i [KB]'%int(round(chunk_kb_)))
        
        if verbose: even_print(dsn,'%s'%str(ds.shape))
        
        ## write
        ds[:,:] = quads
        
        # === dims_unstruct/pts
        
        ## flatten point coordinate vector
        pts = np.reshape(xyz, (ni*nj,3), order=order)
        
        dsn = 'dims/pts'
        if (dsn in self):
            del self[dsn]
        
        shape = pts.shape
        dtype = pts.dtype
        itemsize = pts.dtype.itemsize
        chunks = h5_chunk_sizer(nxi=shape, constraint=(None,None), size_kb=chunk_kb, base=chunk_base, itemsize=itemsize)
        ds = self.create_dataset(
                            dsn,
                            shape=shape,
                            chunks=chunks,
                            dtype=dtype,
                            )
        
        chunk_kb_ = np.prod(ds.chunks)*itemsize / 1024. ## actual
        if verbose:
            even_print('chunk shape (n_pts,3)','%s'%str(ds.chunks))
            even_print('chunk size','%i [KB]'%int(round(chunk_kb_)))
        
        if verbose: even_print(dsn,'%s'%str(ds.shape))
        
        ## write
        ds[:,:] = pts
        
        if verbose: print(72*'-')
        if verbose: print('total time : spd.gen_unstruct_xyz() : %s'%format_time_string((timeit.default_timer() - t_start_func)))
        if verbose: print(72*'-')
        return
    
    @staticmethod
    def copy(fn_spd_src, fn_spd_tgt, **kwargs):
        '''
        copy header info, selected scalars, and [i,j,t] range to new SPD file
        - currently copies complete [i,j] range
        - if [i,j] range clipping were to be implemented, taking data_unstruct would be difficult
        --> this currently does NOT work in serial mode
        '''
        
        #comm    = MPI.COMM_WORLD
        rank    = MPI.COMM_WORLD.Get_rank()
        n_ranks = MPI.COMM_WORLD.Get_size()
        
        if (rank==0):
            verbose = True
        else:
            verbose = False
        
        if verbose: print('\n'+'spd.copy()'+'\n'+72*'-')
        t_start_func = timeit.default_timer()
        
        rx       = kwargs.get('rx',None)
        ry       = kwargs.get('ry',None)
        rz       = kwargs.get('rz',None)
        
        ri       = kwargs.get('ri',1)
        rj       = kwargs.get('rj',1)
        
        rt       = kwargs.get('rt',1)
        force    = kwargs.get('force',False) ## overwrite or raise error if exists
        
        ti_min   = kwargs.get('ti_min',None)
        ti_max   = kwargs.get('ti_max',None)
        #scalars  = kwargs.get('scalars',None)
        
        i_min  = kwargs.get( 'i_min'  , None )
        i_max  = kwargs.get( 'i_max'  , None )
        j_min  = kwargs.get( 'j_min'  , None )
        j_max  = kwargs.get( 'j_max'  , None )
        ti_min = kwargs.get( 'ti_min' , None )
        ti_max = kwargs.get( 'ti_max' , None )
        
        ct = kwargs.get('ct',1) ## 'chunks' in time
        
        chunk_kb         = kwargs.get('chunk_kb',2*1024) ## h5 chunk size: default 2 [MB]
        chunk_constraint = kwargs.get('chunk_constraint',(None,None,1)) ## the 'constraint' parameter for sizing h5 chunks (i,j,t)
        chunk_base       = kwargs.get('chunk_base',2)
        
        stripe_count   = kwargs.pop('stripe_count'   , 16 ) ## for initializing SPD file
        stripe_size_mb = kwargs.pop('stripe_size_mb' , 2  )
        
        #xi_step = kwargs.get('xi_step',1)
        #yi_step = kwargs.get('yi_step',1)
        #zi_step = kwargs.get('zi_step',1)
        
        if (rx is not None):
            raise ValueError('rx not a valid option for spd.copy(). accepted are: ri,rj')
        if (ry is not None):
            raise ValueError('ry not a valid option for spd.copy(). accepted are: ri,rj')
        if (rz is not None):
            raise ValueError('rz not a valid option for spd.copy(). accepted are: ri,rj')
        
        if (i_min is not None):
            raise NotImplementedError('i/j_min/max not yet supported')
        if (i_max is not None):
            raise NotImplementedError('i/j_min/max not yet supported')
        if (j_min is not None):
            raise NotImplementedError('i/j_min/max not yet supported')
        if (j_max is not None):
            raise NotImplementedError('i/j_min/max not yet supported')
        
        if (rt!=1):
            raise AssertionError('rt!=1')
        if (ri*rj!=n_ranks):
            raise AssertionError('ri*rj!=n_ranks')
        if not os.path.isfile(fn_spd_src):
            raise FileNotFoundError('%s not found!'%fn_spd_src)
        if os.path.isfile(fn_spd_tgt) and not force:
            raise FileExistsError('%s already exists. delete it or use \'force=True\' kwarg'%fn_spd_tgt)
        
        # ===
        
        with spd(fn_spd_src, 'r', comm=MPI.COMM_WORLD, driver='mpio') as hf_src:
            with spd(fn_spd_tgt, 'w',
                     force=force,
                     comm=MPI.COMM_WORLD,
                     driver='mpio',
                     stripe_count=stripe_count,
                     stripe_size_mb=stripe_size_mb) as hf_tgt:
                
                ni      = hf_src.ni
                nj      = hf_src.nj
                #n_quads = hf_src.n_quads
                #n_pts   = hf_src.n_pts
                nt      = hf_src.nt
                
                ## report info from source file
                fsize = os.path.getsize(hf_src.fname)/1024**3
                if verbose: even_print(os.path.basename(hf_src.fname),'%0.1f [GB]'%fsize)
                if verbose: even_print('ni','%i'%hf_src.ni)
                if verbose: even_print('nj','%i'%hf_src.nj)
                if verbose: even_print('nt','%i'%hf_src.nt)
                if verbose: even_print('n_quads','%i'%hf_src.n_quads)
                if verbose: even_print('n_pts','%i'%hf_src.n_pts)
                if verbose: print(72*'-')
                
                # ===
                
                ## get OUTPUT times
                t_  = np.copy(hf_src['dims/t'][()])
                ti_ = np.arange(t_.shape[0], dtype=np.int32)
                if (ti_min is None):
                    ti_min = ti_.min()
                if (ti_max is None):
                    ti_max = ti_.max()
                ti  = np.copy(ti_[ti_min:ti_max+1])
                if (ti.shape[0]==0):
                    raise ValueError('ti_min/ti_max combo yields no times')
                ti1 = ti.min()
                ti2 = ti.max()+1
                t   = np.copy(t_[ti1:ti2])
                nt  = t.shape[0]
                
                if (ti_min<0):
                    if verbose: even_print('ti_min', f'{ti_min:d} / {ti1:d}')
                else:
                    if verbose: even_print('ti_min', f'{ti_min:d}')
                
                if (ti_max<0):
                    if verbose: even_print('ti_max', f'{ti_max:d} / {ti2:d}')
                else:
                    if verbose: even_print('ti_max', f'{ti_max:d}')
                
                if verbose: even_print('t range', f'{ti.shape[0]:d}/{ti_.shape[0]:d}')
                
                # ===
                
                ## time chunk ranges
                if (ct>nt):
                    raise ValueError('ct>nt')
                
                tfi = np.arange(ti1,ti2,dtype=np.int64)
                ctl_ = np.array_split(tfi,ct)
                ctl = [[b[0],b[-1]+1] for b in ctl_ ]
                
                if verbose: print(72*'-')
                
                # ===
                
                ## copy over attributes
                for key,val in hf_src.attrs.items():
                    hf_tgt.attrs[key] = val
                
                # === get rank distribution over (i,j) dims
                
                comm2d = hf_src.comm.Create_cart(dims=[ri,rj], periods=[False,False], reorder=False)
                t2d = comm2d.Get_coords(rank)
                
                ril_ = np.array_split(np.arange(hf_src.ni,dtype=np.int64),ri)
                rjl_ = np.array_split(np.arange(hf_src.nj,dtype=np.int64),rj)
                
                ril = [[b[0],b[-1]+1] for b in ril_ ]
                rjl = [[b[0],b[-1]+1] for b in rjl_ ]
                
                ri1, ri2 = ril[t2d[0]] #; nir = ri2 - ri1
                rj1, rj2 = rjl[t2d[1]] #; njr = rj2 - rj1
                
                # === copy over non-attribute metadata
                
                ## 'dims/xyz' : 3D polydata grid coordinates : shape=(ni,nj,3)
                dsn = 'dims/xyz'
                dset = hf_src[dsn]
                dtype = dset.dtype
                float_bytes = dtype.itemsize
                with dset.collective:
                    xyz = np.copy( dset[ri1:ri2,rj1:rj2,:] )
                shape  = (ni,nj,3)
                chunks = h5_chunk_sizer(nxi=shape, constraint=(None,None,3), size_kb=chunk_kb, base=4, itemsize=float_bytes)
                data_gb = float_bytes * ni * nj / 1024**3
                if verbose:
                    even_print(f'initializing {dsn}','%0.1f [GB]'%(data_gb,))
                dset = hf_tgt.create_dataset(dsn, dtype=xyz.dtype, shape=shape, chunks=chunks)
                chunk_kb_ = np.prod(dset.chunks)*float_bytes / 1024. ## actual
                if verbose:
                    even_print('chunk shape (i,j,3)',str(dset.chunks))
                    even_print('chunk size','%i [KB]'%int(round(chunk_kb_)))
                with dset.collective:
                    dset[ri1:ri2,rj1:rj2,:] = xyz
                
                if verbose: print(72*'-')
                
                ## copy over [t]
                dsn = 'dims/t'
                ds = hf_tgt.create_dataset(dsn, chunks=None, data=t)
                if verbose: even_print(dsn,str(ds.shape))
                hf_tgt.attrs['nt'] = t.shape[0]
                
                ## copy over additional [dims/<>] dsets
                for dsn in [ 'dims/stang', 'dims/snorm', 'dims/crv_R', 'dims/x', 'dims/y', 'dims/z' ]:
                    if (dsn in hf_src):
                        data = np.copy(hf_src[dsn][()])
                        ds = hf_tgt.create_dataset(dsn, data=data, chunks=None)
                        if verbose: even_print(dsn,str(ds.shape))
                    else:
                        if verbose: even_print(dsn,'not found')
                
                ## copy over additional [csys/<>] dsets
                for dsn in [ 'csys/vtang', 'csys/vnorm' ]:
                    if (dsn in hf_src):
                        data = np.copy(hf_src[dsn][()])
                        ds = hf_tgt.create_dataset(dsn, data=data, chunks=None)
                        if verbose: even_print(dsn,str(ds.shape))
                    else:
                        if verbose: even_print(dsn,'not found')
                
                if verbose: print(72*'-')
                hf_tgt.get_header(verbose=verbose)
                if verbose: print(72*'-')
                
                # === initialize datasets in target file
                
                for scalar in hf_src.scalars:
                    
                    dsn = f'data/{scalar}'
                    ds = hf_src[dsn]
                    dtype = ds.dtype
                    float_bytes = dtype.itemsize
                    
                    data_gb = ni * nj * nt * float_bytes / 1024**3
                    shape   = (ni,nj,nt)
                    chunks  = h5_chunk_sizer(nxi=shape, constraint=chunk_constraint, size_kb=chunk_kb, base=chunk_base, itemsize=float_bytes)
                    
                    if verbose:
                        even_print(f'initializing data/{scalar}','%0.1f [GB]'%(data_gb,))
                    if (dsn in hf_tgt):
                        del hf_tgt[dsn]
                    dset = hf_tgt.create_dataset(
                                            dsn,
                                            shape=shape,
                                            dtype=dtype,
                                            chunks=chunks,
                                            )
                    
                    chunk_kb_ = np.prod(dset.chunks)*4 / 1024. ## actual
                    if verbose:
                        even_print('chunk shape (i,j,t)','%s'%str(dset.chunks))
                        even_print('chunk size','%i [KB]'%int(round(chunk_kb_)))
                
                if verbose: print(72*'-')
                
                # === main loop
                
                data_gb_read  = 0.
                data_gb_write = 0.
                t_read  = 0.
                t_write = 0.
                
                if verbose:
                    progress_bar = tqdm(
                        total=len(ctl)*hf_src.n_scalars,
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
                
                for scalar in hf_src.scalars:
                    dset_src = hf_src[f'data/{scalar}']
                    dset_tgt = hf_tgt[f'data/{scalar}']
                    
                    dtype = dset_src.dtype
                    float_bytes = dtype.itemsize
                    
                    for ctl_ in ctl:
                        ct1, ct2 = ctl_
                        ntc = ct2 - ct1
                        
                        ## read
                        hf_src.comm.Barrier()
                        t_start = timeit.default_timer()
                        with dset_src.collective:
                            data = np.copy( dset_src[ri1:ri2,rj1:rj2,ct1:ct2] )
                        hf_src.comm.Barrier()
                        t_delta = timeit.default_timer() - t_start
                        data_gb = float_bytes * ni * nj * ntc / 1024**3
                        
                        t_read       += t_delta
                        data_gb_read += data_gb
                        
                        if verbose:
                            tqdm.write(even_print(f'read: {scalar}', '%0.3f [GB]  %0.3f [s]  %0.3f [GB/s]'%(data_gb,t_delta,(data_gb/t_delta)), s=True))
                        
                        ## write
                        hf_tgt.comm.Barrier()
                        t_start = timeit.default_timer()
                        with dset_tgt.collective:
                            dset_tgt[ri1:ri2,rj1:rj2,:] = data
                        hf_tgt.comm.Barrier()
                        t_delta = timeit.default_timer() - t_start
                        data_gb = float_bytes * ni * nj * ntc / 1024**3
                        
                        t_write       += t_delta
                        data_gb_write += data_gb
                        
                        if verbose:
                            tqdm.write(even_print(f'write: {scalar}', '%0.3f [GB]  %0.3f [s]  %0.3f [GB/s]'%(data_gb,t_delta,(data_gb/t_delta)), s=True))
                        
                        if verbose: progress_bar.update()
                
                if verbose: progress_bar.close()
        
        if verbose: print(72*'-')
        if verbose: print('total time : spd.copy() : %s'%format_time_string((timeit.default_timer() - t_start_func)))
        if verbose: print(72*'-')
        return
    
    def make_xdmf(self):
        '''
        generate an XDMF/XMF2 from SPD for processing with Paraview
        -----
        --> https://www.xdmf.org/index.php/XDMF_Model_and_Format
        '''
        
        if (self.rank==0):
            verbose = True
        else:
            verbose = False
        
        fname_path            = os.path.dirname(self.fname)
        fname_base            = os.path.basename(self.fname)
        fname_root, fname_ext = os.path.splitext(fname_base)
        fname_xdmf_base       = fname_root+'.xmf2'
        fname_xdmf            = os.path.join(fname_path, fname_xdmf_base)
        
        if 'dims/quads' not in self:
            raise ValueError('dims/quads not in file')
        if 'dims/pts' not in self:
            raise ValueError('dims/pts not in file')
        
        ## this should be added to spd.get_header()
        dsn = 'dims/quads'
        n_quads,four = self[dsn].shape
        dsn = 'dims/pts'
        n_pts,three = self[dsn].shape
        self.n_quads = n_quads
        self.n_pts   = n_pts
        
        if verbose: print('\n'+'spd.make_xdmf()'+'\n'+72*'-')
        
        dataset_precision_dict = {} ## holds dtype.itemsize ints i.e. 4,8
        dataset_numbertype_dict = {} ## holds string description of dtypes i.e. 'Float','Integer'
        
        # === 1D coordinate dimension vectors --> get dtype.name
        for dsn in ['pts','quads']:
            if (f'dims/{dsn}' in self):
                data = self[f'dims/{dsn}']
                dataset_precision_dict[dsn] = data.dtype.itemsize
                if (data.dtype.name=='float32') or (data.dtype.name=='float64'):
                    dataset_numbertype_dict[dsn] = 'Float'
                elif (data.dtype.name=='int8') or (data.dtype.name=='int16') or (data.dtype.name=='int32') or (data.dtype.name=='int64'):
                    dataset_numbertype_dict[dsn] = 'Integer'
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
                perms_h5 = oct(os.stat(self.fname).st_mode)[-3:] ## get permissions of SPD file
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
                
                xdmf_str=f'''
                         <Topology TopologyType="Quadrilateral" NumberOfElements="{n_quads:d}">
                             <DataItem Dimensions="{n_quads:d} 4" NumberType="{dataset_numbertype_dict['quads']}" Precision="{dataset_precision_dict['quads']}" Format="HDF">
                                 {self.fname_base}:/dims/quads
                             </DataItem>
                         </Topology>
                         <Geometry GeometryType="XYZ">
                             <DataItem Dimensions="{n_pts:d} 3" NumberType="{dataset_numbertype_dict['pts']}" Precision="{dataset_precision_dict['pts']}" Format="HDF">
                                 {self.fname_base}:/dims/pts
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
                    
                    xdmf_str = f'''
                                <!-- ==================== ts = {ti:d} ==================== -->
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
                    
                    # === .xdmf : <Grid> per scalar
                    
                    for scalar in self.scalars:
                        dset_hf_path = f'data/{scalar}'
                        scalar_name = scalar
                        
                        xdmf_str=f'''
                                 <!-- {scalar} -->
                                 <Attribute Name="{scalar_name}" AttributeType="Scalar" Center="Node">
                                   <DataItem ItemType="HyperSlab" Dimensions="{self.ni:d} {self.nj:d}" Type="HyperSlab">
                                     <DataItem Dimensions="3 3" NumberType="Integer" Format="XML">
                                       {0:<9d} {0:<9d} {ti:d}
                                       {1:<9d} {1:<9d} {1:d}
                                       {self.ni:<9d} {self.nj:<9d} {1:d}
                                     </DataItem>
                                     <DataItem Dimensions="{self.ni:d} {self.nj:d} {self.nt:d}" NumberType="{dataset_numbertype_dict[scalar]}" Precision="{dataset_precision_dict[scalar]:d}" Format="HDF">
                                       {fname_base}:/{dset_hf_path}
                                     </DataItem>
                                   </DataItem>
                                 </Attribute>
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
    
    def init_from_eas4_wall(self, fn_eas4, **kwargs):
        return _init_from_eas4_wall(self, fn_eas4, **kwargs)
    
    def import_eas4_wall(self, fn_eas4_list, **kwargs):
        return _import_eas4_wall(self, fn_eas4_list, **kwargs)
    
    def calc_turb_cospectrum_wall(self, **kwargs):
        return _calc_turb_cospectrum_wall(self, **kwargs)
    
    def calc_ccor_wall(self, **kwargs):
        return _calc_ccor_wall(self, **kwargs)
    
    def calc_statistics_wall(self, **kwargs):
        return _calc_statistics_wall(self, **kwargs)
    
    def calc_mean_uncertainty_BMBC(self, **kwargs):
        return _calc_mean_uncertainty_BMBC(self, **kwargs)
