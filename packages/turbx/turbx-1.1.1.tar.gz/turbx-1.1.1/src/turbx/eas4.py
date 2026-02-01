import os

import h5py
import numpy as np
from mpi4py import MPI

from .utils import even_print

# ======================================================================

class eas4(h5py.File):
    '''
    Interface class for EAS4 files
    ------------------------------
    - super()'ed h5py.File class
    - EAS4 is the HDF5-based output format from the flow solver NS3D
    - 3D dataset storage ([x,y,z] per [t])
    '''
    
    def __init__(self, *args, **kwargs):
        
        ## if grid MUST be read as 3D, i.e. the GMODE=(5,5,5), only read if this is TRUE
        ## this can lead to huge RAM usage in MPI mode, so OFF by default
        ##
        ## if a single dimension has GMODE=5 but not ALL, i.e. (5,5,2), this allows for
        ## grid to be read as some combination of 2D&1D
        self.read_3d_grid = kwargs.pop('read_3d_grid', False)
        
        self.fname, openMode = args
        
        self.fname_path = os.path.dirname(self.fname)
        self.fname_base = os.path.basename(self.fname)
        self.fname_root, self.fname_ext = os.path.splitext(self.fname_base)
        
        ## default to libver='latest' if none provided
        if ('libver' not in kwargs):
            kwargs['libver'] = 'latest'
        
        if (openMode!='r'):
            raise ValueError('turbx.eas4(): opening EAS4 in anything but read mode \'r\' is not allowed!')
        
        ## catch possible user error --> user tries to open non-EAS4 with turbx.eas4()
        if (self.fname_ext!='.eas'):
            raise ValueError('turbx.eas4() should not be used to open non-EAS4 files')
        
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
        
        ## set library version to latest (if not otherwise set)
        if ('libver' not in kwargs):
            kwargs['libver']='latest'
        
        ## unique kwargs (not h5py.File kwargs) --> pop() rather than get()
        no_indep_rw = kwargs.pop('no_indep_rw', False)
        if not isinstance(no_indep_rw, bool):
            raise ValueError('no_indep_rw must be type bool')
        
        ## set MPI hints, passed through 'mpi_info' dict
        if self.usingmpi:
            if ('info' in kwargs):
                self.mpi_info = kwargs['info']
            else:
                mpi_info = MPI.Info.Create()
                ##
                mpi_info.Set('romio_ds_write' , 'disable'   )
                mpi_info.Set('romio_ds_read'  , 'disable'   )
                #mpi_info.Set('romio_cb_read'  , 'automatic' )
                #mpi_info.Set('romio_cb_write' , 'automatic' )
                mpi_info.Set('romio_cb_read'  , 'enable' )
                mpi_info.Set('romio_cb_write' , 'enable' )
                
                ## ROMIO -- collective buffer size
                mpi_info.Set('cb_buffer_size' , str(int(round(1024**3))) ) ## 1 [GB]
                
                ## ROMIO -- force collective I/O
                if no_indep_rw:
                    mpi_info.Set('romio_no_indep_rw' , 'true' )
                
                ## ROMIO -- N Aggregators
                #mpi_info.Set('cb_nodes' , str(min(16,self.n_ranks//2)) )
                mpi_info.Set('cb_nodes' , str(min(16,self.n_ranks)) )
                
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
        
        self.domainName = 'DOMAIN_000000' ## turbx only handles one domain for now
        
        ## eas4() unique kwargs (not h5py.File kwargs) --> pop() rather than get()
        verbose = kwargs.pop('verbose',False)
        self.verbose = verbose
        ## force = kwargs.pop('force',False) ## --> dont need, always read-only!
        
        ## call actual h5py.File.__init__()
        super(eas4, self).__init__(*args, **kwargs)
        self.get_header()
    
    def get_header(self):
        
        EAS4_NO_G=1
        EAS4_X0DX_G=2
        #EAS4_UDEF_G=3
        EAS4_ALL_G=4
        EAS4_FULL_G=5
        gmode_dict = {1:'EAS4_NO_G', 2:'EAS4_X0DX_G', 3:'EAS4_UDEF_G', 4:'EAS4_ALL_G', 5:'EAS4_FULL_G'}
        
        self.bform = self['Kennsatz'].attrs['bform'] ## binary format : 1=single  , 2=double
        self.dform = self['Kennsatz'].attrs['dform'] ## data format   : 1=C-order , 2=Fortran-order
        
        # === characteristic values
        
        if self.verbose: print(72*'-')
        Ma    = self['Kennsatz']['FLOWFIELD_PROPERTIES'].attrs['Ma'][0]
        Re    = self['Kennsatz']['FLOWFIELD_PROPERTIES'].attrs['Re'][0]
        Pr    = self['Kennsatz']['FLOWFIELD_PROPERTIES'].attrs['Pr'][0]
        kappa = self['Kennsatz']['FLOWFIELD_PROPERTIES'].attrs['kappa'][0]
        R     = self['Kennsatz']['FLOWFIELD_PROPERTIES'].attrs['R'][0]
        p_inf = self['Kennsatz']['FLOWFIELD_PROPERTIES'].attrs['p_inf'][0]
        T_inf = self['Kennsatz']['FLOWFIELD_PROPERTIES'].attrs['T_inf'][0]
        
        ## !!! import what is called 'C_Suth' in NS3D as 'S_Suth' !!!
        S_Suth = self['Kennsatz']['VISCOUS_PROPERTIES'].attrs['C_Suth'][0]
        
        mu_Suth_ref = self['Kennsatz']['VISCOUS_PROPERTIES'].attrs['mu_Suth_ref'][0]
        T_Suth_ref  = self['Kennsatz']['VISCOUS_PROPERTIES'].attrs['T_Suth_ref'][0]
        
        C_Suth = mu_Suth_ref/(T_Suth_ref**(3/2))*(T_Suth_ref + S_Suth) ## [kg/(m·s·√K)]
        
        if self.verbose: even_print('Ma'          , '%0.2f [-]'           % Ma          )
        if self.verbose: even_print('Re'          , '%0.1f [-]'           % Re          )
        if self.verbose: even_print('Pr'          , '%0.3f [-]'           % Pr          )
        if self.verbose: even_print('T_inf'       , '%0.3f [K]'           % T_inf       )
        if self.verbose: even_print('p_inf'       , '%0.1f [Pa]'          % p_inf       )
        if self.verbose: even_print('kappa'       , '%0.3f [-]'           % kappa       )
        if self.verbose: even_print('R'           , '%0.3f [J/(kg·K)]'    % R           )
        if self.verbose: even_print('mu_Suth_ref' , '%0.6E [kg/(m·s)]'    % mu_Suth_ref )
        if self.verbose: even_print('T_Suth_ref'  , '%0.2f [K]'           % T_Suth_ref  )
        if self.verbose: even_print('S_Suth'      , '%0.2f [K]'           % S_Suth      )
        if self.verbose: even_print('C_Suth'      , '%0.5e [kg/(m·s·√K)]' % C_Suth      ) ## actually derived
        
        # === characteristic values : derived
        
        # mu_inf_1 = 14.58e-7*T_inf**1.5/(T_inf+110.4)
        # mu_inf_2 = mu_Suth_ref*(T_inf/T_Suth_ref)**(3/2) * ((T_Suth_ref+S_Suth)/(T_inf+S_Suth))
        # mu_inf_3 = C_Suth*T_inf**(3/2)/(T_inf+S_Suth)
        # if not np.isclose(mu_inf_1, mu_inf_2, rtol=1e-14):
        #     raise AssertionError('inconsistency in Sutherland calc --> check')
        # if not np.isclose(mu_inf_2, mu_inf_3, rtol=1e-14):
        #     raise AssertionError('inconsistency in Sutherland calc --> check')
        # mu_inf    = mu_inf_3
        
        if self.verbose: print(72*'-')
        mu_inf      = mu_Suth_ref*(T_inf/T_Suth_ref)**(3/2) * ((T_Suth_ref+S_Suth)/(T_inf+S_Suth))
        rho_inf     = p_inf / ( R * T_inf )
        nu_inf      = mu_inf/rho_inf
        a_inf       = np.sqrt(kappa*R*T_inf)
        U_inf       = Ma*a_inf
        cp          = R*kappa/(kappa-1.)
        cv          = cp/kappa
        recov_fac   = Pr**(1/3) ## for turbulent boundary layer
        Taw         = T_inf + recov_fac*U_inf**2/(2*cp)
        lchar       = Re * nu_inf / U_inf
        tchar       = lchar / U_inf
        uchar       = U_inf ## alias
        M_inf       = Ma ## alias
        p_tot_inf   = p_inf   * (1 + (kappa-1)/2 * M_inf**2)**(kappa/(kappa-1))
        T_tot_inf   = T_inf   * (1 + (kappa-1)/2 * M_inf**2)
        rho_tot_inf = rho_inf * (1 + (kappa-1)/2 * M_inf**2)**(1/(kappa-1))
        
        if self.verbose: even_print('rho_inf'         , '%0.3f [kg/m³]'    % rho_inf   )
        if self.verbose: even_print('mu_inf'          , '%0.6E [kg/(m·s)]' % mu_inf    )
        if self.verbose: even_print('nu_inf'          , '%0.6E [m²/s]'     % nu_inf    )
        if self.verbose: even_print('a_inf'           , '%0.6f [m/s]'      % a_inf     )
        if self.verbose: even_print('U_inf'           , '%0.6f [m/s]'      % U_inf     )
        if self.verbose: even_print('cp'              , '%0.3f [J/(kg·K)]' % cp        )
        if self.verbose: even_print('cv'              , '%0.3f [J/(kg·K)]' % cv        )
        #if self.verbose: even_print('recovery factor' , '%0.6f [-]'        % recov_fac )
        if self.verbose: even_print('Taw'             , '%0.3f [K]'        % Taw       )
        if self.verbose: even_print('lchar'           , '%0.6E [m]'        % lchar     )
        if self.verbose: even_print('tchar'           , '%0.6E [s]'        % tchar     )
        if self.verbose: print(72*'-'+'\n')
        
        # ===
        
        self.Ma           = Ma
        self.Re           = Re
        self.Pr           = Pr
        self.kappa        = kappa
        self.R            = R
        self.p_inf        = p_inf
        self.T_inf        = T_inf
        self.C_Suth       = C_Suth
        self.S_Suth       = S_Suth
        self.mu_Suth_ref  = mu_Suth_ref
        self.T_Suth_ref   = T_Suth_ref
        
        self.rho_inf     = rho_inf
        self.mu_inf      = mu_inf
        self.nu_inf      = nu_inf
        self.a_inf       = a_inf
        self.U_inf       = U_inf
        self.cp          = cp
        self.cv          = cv
        self.recov_fac   = recov_fac
        self.Taw         = Taw
        self.lchar       = lchar
        
        self.tchar       = tchar
        self.uchar       = uchar
        self.M_inf       = M_inf
        self.p_tot_inf   = p_tot_inf
        self.T_tot_inf   = T_tot_inf
        self.rho_tot_inf = rho_tot_inf
        
        # === check if this a 2D average file like 'mean_flow_mpi.eas'
        
        if self.verbose: print(72*'-')
        if ('/Kennsatz/AUXILIARY/AVERAGING' in self):
            self.total_avg_time       = self['/Kennsatz/AUXILIARY/AVERAGING'].attrs['total_avg_time'][0]
            self.total_avg_iter_count = self['/Kennsatz/AUXILIARY/AVERAGING'].attrs['total_avg_iter_count'][0]
            if self.verbose: even_print('total_avg_time', '%0.2f'%self.total_avg_time)
            if self.verbose: even_print('total_avg_iter_count', '%i'%self.total_avg_iter_count)
            self.measType = 'mean'
        else:
            self.measType = 'unsteady'
        if self.verbose: even_print('meas type', '\'%s\''%self.measType)
        if self.verbose: print(72*'-'+'\n')
        
        # === grid info
        
        ndim1 = int( self['Kennsatz/GEOMETRY/%s'%self.domainName].attrs['DOMAIN_SIZE'][0] )
        ndim2 = int( self['Kennsatz/GEOMETRY/%s'%self.domainName].attrs['DOMAIN_SIZE'][1] )
        ndim3 = int( self['Kennsatz/GEOMETRY/%s'%self.domainName].attrs['DOMAIN_SIZE'][2] )
        
        nx = self.nx = ndim1
        ny = self.ny = ndim2
        nz = self.nz = ndim3
        
        if (self.measType=='mean'):
            nz = self.nz = 1
        
        ngp = self.ngp = nx*ny*nz
        
        if self.verbose: print('grid info\n'+72*'-')
        if self.verbose: even_print('nx',  '%i'%nx  )
        if self.verbose: even_print('ny',  '%i'%ny  )
        if self.verbose: even_print('nz',  '%i'%nz  )
        if self.verbose: even_print('ngp', '%i'%ngp )
        
        gmode_dim1 = self.gmode_dim1 = self['Kennsatz/GEOMETRY/%s'%self.domainName].attrs['DOMAIN_GMODE'][0]
        gmode_dim2 = self.gmode_dim2 = self['Kennsatz/GEOMETRY/%s'%self.domainName].attrs['DOMAIN_GMODE'][1]
        gmode_dim3 = self.gmode_dim3 = self['Kennsatz/GEOMETRY/%s'%self.domainName].attrs['DOMAIN_GMODE'][2]
        
        ## the original gmode (pre-conversion)
        #gmode_dim1_orig = self.gmode_dim1_orig = gmode_dim1
        #gmode_dim2_orig = self.gmode_dim2_orig = gmode_dim2
        #gmode_dim3_orig = self.gmode_dim3_orig = gmode_dim3
        
        if self.verbose: even_print( 'gmode dim1' , '%i / %s'%(gmode_dim1,gmode_dict[gmode_dim1]) )
        if self.verbose: even_print( 'gmode dim2' , '%i / %s'%(gmode_dim2,gmode_dict[gmode_dim2]) )
        if self.verbose: even_print( 'gmode dim3' , '%i / %s'%(gmode_dim3,gmode_dict[gmode_dim3]) )
        if self.verbose: print(72*'-')
        
        # === (automatic) grid read
        
        ## can fail if >2[GB] and using driver=='mpio' and using one process
        ## https://github.com/h5py/h5py/issues/1052
        
        if True:
            
            ## dset object handles, no read yet
            dset1 = self[f'Kennsatz/GEOMETRY/{self.domainName}/dim01']
            dset2 = self[f'Kennsatz/GEOMETRY/{self.domainName}/dim02']
            dset3 = self[f'Kennsatz/GEOMETRY/{self.domainName}/dim03']
            
            #float_bytes1  = dset1.dtype.itemsize
            #float_bytes2  = dset2.dtype.itemsize
            #float_bytes3  = dset3.dtype.itemsize
            
            #data_gb_dim1 = float_bytes1*np.prod(dset1.shape) / 1024**3
            #data_gb_dim2 = float_bytes2*np.prod(dset2.shape) / 1024**3
            #data_gb_dim3 = float_bytes3*np.prod(dset3.shape) / 1024**3
            
            ## no 3D datasets, because no dim's GMODE is 5
            ## in this case, the dsets are just 0D/1D, so just read completely to all ranks
            if not any([ (gmode_dim1==5) , (gmode_dim2==5) , (gmode_dim3==5) ]):
                
                self.is_curvilinear = False
                self.is_rectilinear = True
                
                ## check just to be sure that the coord dsets in the HDF5 are indeed not 3D
                if (dset1.ndim>2):
                    raise ValueError
                if (dset2.ndim>2):
                    raise ValueError
                if (dset2.ndim>2):
                    raise ValueError
                
                ## read 1D datasets completely... this should never be a problem for RAM in MPI mode
                dim1_data = np.copy(dset1[()])
                dim2_data = np.copy(dset2[()])
                dim3_data = np.copy(dset3[()])
            
            else:
                
                '''
                at least one dim has GMODE=5, so 3D datasets exist, BUT unless GMODE==(5,5,5) 
                it is still possible to read as combo of 1D/2D, which is safe for MPI
                '''
                
                self.is_curvilinear = True
                self.is_rectilinear = False
                
                if (gmode_dim1==5) and (gmode_dim2==5) and (gmode_dim3==5): ## MUST read as 3D... only do here if read_3d_grid=True explicitly set
                    
                    ## this becomes very RAM intensive in MPI mode (all rannks are reading full 3D coord data)
                    if self.read_3d_grid:
                        dim1_data = np.copy(dset1[()])
                        dim2_data = np.copy(dset2[()])
                        dim3_data = np.copy(dset3[()])
                    else:
                        dim1_data = None
                        dim2_data = None
                        dim3_data = None
                
                elif (gmode_dim1==5) and (gmode_dim2==5) and (gmode_dim3==1): ## 551
                    dim1_data = np.copy(dset1[:,:,0][:,:,np.newaxis]) ## [x] is (nx,ny,1)
                    dim2_data = np.copy(dset2[:,:,0][:,:,np.newaxis]) ## [y] is (nx,ny,1)
                    dim3_data = np.copy(dset3[()])                    ## [z]
                
                elif (gmode_dim1==5) and (gmode_dim2==5) and (gmode_dim3==2): ## 552
                    dim1_data = np.copy(dset1[:,:,0][:,:,np.newaxis]) ## [x] is (nx,ny,1)
                    dim2_data = np.copy(dset2[:,:,0][:,:,np.newaxis]) ## [y] is (nx,ny,1)
                    dim3_data = np.copy(dset3[()])                    ## [z]
                
                elif (gmode_dim1==5) and (gmode_dim2==5) and (gmode_dim3==4): ## 554
                    dim1_data = np.copy(dset1[:,:,0][:,:,np.newaxis]) ## [x] is (nx,ny,1)
                    dim2_data = np.copy(dset2[:,:,0][:,:,np.newaxis]) ## [y] is (nx,ny,1)
                    dim3_data = np.copy(dset3[()])                    ## [z]
                
                else:
                    
                    print(f'gmode combo ({gmode_dim1:d},{gmode_dim2:d},{gmode_dim3:d}) does not yet have instructions in eas4.get_header()')
                    raise NotImplementedError
        
        ## old snippet for getting around HDF5 / h5py bug if >2[GB] and using driver=='mpio' and using one process
        ## keeping here for now
        ## https://github.com/h5py/h5py/issues/1052
        #except OSError:
        if False:
            
            if (gmode_dim1 == EAS4_FULL_G):
                dim1_data = np.zeros((nx,ny,nz), dtype = self['Kennsatz/GEOMETRY/%s/dim01'%self.domainName].dtype)
                for i in range(nx):
                    dim1_data[i,:,:] = self['Kennsatz/GEOMETRY/%s/dim01'%self.domainName][i,:,:]
            else:
                dim1_data = self['Kennsatz/GEOMETRY/%s/dim01'%self.domainName][:]
            
            if (gmode_dim2 == EAS4_FULL_G):
                dim2_data = np.zeros((nx,ny,nz), dtype = self['Kennsatz/GEOMETRY/%s/dim02'%self.domainName].dtype)
                for i in range(nx):
                    dim2_data[i,:,:] = self['Kennsatz/GEOMETRY/%s/dim02'%self.domainName][i,:,:]
            else:
                dim2_data = self['Kennsatz/GEOMETRY/%s/dim02'%self.domainName][:]
            
            if (gmode_dim3 == EAS4_FULL_G):
                dim3_data = np.zeros((nx,ny,nz), dtype = self['Kennsatz/GEOMETRY/%s/dim03'%self.domainName].dtype)
                for i in range(nx):
                    dim3_data[i,:,:] = self['Kennsatz/GEOMETRY/%s/dim03'%self.domainName][i,:,:]
            else:
                dim3_data = self['Kennsatz/GEOMETRY/%s/dim03'%self.domainName][:]
        
        ## check grid for span avg
        if False:
            if (self.measType == 'mean'):
                if (gmode_dim1 == EAS4_FULL_G):
                    if not np.allclose(dim1_data[:,:,0], dim1_data[:,:,1], rtol=1e-08):
                        raise AssertionError('check')
                if (gmode_dim2 == EAS4_FULL_G):
                    if not np.allclose(dim2_data[:,:,0], dim2_data[:,:,1], rtol=1e-08):
                        raise AssertionError('check')
        
        # === expand gmodes 1,2 --> 4 (always ok, even for MPI mode)
        
        ## convert EAS4_NO_G to EAS4_ALL_G (1 --> 4) --> always do this
        ## dim_n_data are already numpy arrays of shape (1,) --> no conversion necessary, just update 'gmode_dimn' attr
        if (gmode_dim1 == EAS4_NO_G):
            gmode_dim1 = self.gmode_dim1 = EAS4_ALL_G
        if (gmode_dim2 == EAS4_NO_G):
            gmode_dim2 = self.gmode_dim2 = EAS4_ALL_G
        if (gmode_dim3 == EAS4_NO_G):
            gmode_dim3 = self.gmode_dim3 = EAS4_ALL_G
        
        ## convert EAS4_X0DX_G to EAS4_ALL_G (2 --> 4) --> always do this
        if (gmode_dim1 == EAS4_X0DX_G):
            dim1_data  = np.linspace(dim1_data[0],dim1_data[0]+dim1_data[1]*(ndim1-1), ndim1, dtype=np.float64)
            gmode_dim1 = self.gmode_dim1 = EAS4_ALL_G
        if (gmode_dim2 == EAS4_X0DX_G):
            dim2_data  = np.linspace(dim2_data[0],dim2_data[0]+dim2_data[1]*(ndim2-1), ndim2, dtype=np.float64)
            gmode_dim2 = self.gmode_dim2 = EAS4_ALL_G
        if (gmode_dim3 == EAS4_X0DX_G):
            dim3_data  = np.linspace(dim3_data[0],dim3_data[0]+dim3_data[1]*(ndim3-1), ndim3, dtype=np.float64)
            gmode_dim3 = self.gmode_dim3 = EAS4_ALL_G
        
        # ===
        
        x = self.x = np.copy(dim1_data)
        y = self.y = np.copy(dim2_data)
        z = self.z = np.copy(dim3_data)
        
        # ## bug check
        # if (z.size > 1):
        #     if np.all(np.isclose(z,z[0],rtol=1e-12)):
        #         raise AssertionError('z has size > 1 but all grid coords are identical!')
        
        if self.verbose: even_print('x_min', '%0.2f'%x.min())
        if self.verbose: even_print('x_max', '%0.2f'%x.max())
        if self.is_rectilinear:
            if (self.nx>2):
                if self.verbose: even_print('dx begin : end', '%0.3E : %0.3E'%( (x[1]-x[0]), (x[-1]-x[-2]) ))
        if self.verbose: even_print('y_min', '%0.2f'%y.min())
        if self.verbose: even_print('y_max', '%0.2f'%y.max())
        if self.is_rectilinear:
            if (self.ny>2):
                if self.verbose: even_print('dy begin : end', '%0.3E : %0.3E'%( (y[1]-y[0]), (y[-1]-y[-2]) ))
        if self.verbose: even_print('z_min', '%0.2f'%z.min())
        if self.verbose: even_print('z_max', '%0.2f'%z.max())
        if self.is_rectilinear:
            if (self.nz>2):
                if self.verbose: even_print('dz begin : end', '%0.3E : %0.3E'%( (z[1]-z[0]), (z[-1]-z[-2]) ))
        if self.verbose: print(72*'-'+'\n')
        
        # === time & scalar info
        
        if self.verbose: print('time & scalar info\n'+72*'-')
        
        n_scalars = self['Kennsatz/PARAMETER'].attrs['PARAMETER_SIZE'][0]
        
        if ('Kennsatz/PARAMETER/PARAMETERS_ATTRS' in self):
            scalars =  [ s.decode('utf-8').strip() for s in self['Kennsatz/PARAMETER/PARAMETERS_ATTRS'][()] ]
        else:
            ## this is the older gen structure
            scalars = [ self['Kennsatz/PARAMETER'].attrs['PARAMETERS_ATTR_%06d'%i][0].decode('utf-8').strip() for i in range(n_scalars) ]
        
        scalar_n_map = dict(zip(scalars, range(n_scalars)))
        
        self.scalars_dtypes = []
        for scalar in scalars:
            dset_path = 'Data/%s/ts_%06d/par_%06d'%(self.domainName,0,scalar_n_map[scalar])
            if (dset_path in self):
                self.scalars_dtypes.append(self[dset_path].dtype)
            else:
                #self.scalars_dtypes.append(np.float32)
                raise AssertionError('dset not found: %s'%dset_path)
        
        self.scalars_dtypes_dict = dict(zip(scalars, self.scalars_dtypes)) ## dict {<<scalar>>: <<dtype>>}
        
        nt         = self['Kennsatz/TIMESTEP'].attrs['TIMESTEP_SIZE'][0] 
        gmode_time = self['Kennsatz/TIMESTEP'].attrs['TIMESTEP_MODE'][0]
        
        ## a baseflow will not have a TIMEGRID
        if ('Kennsatz/TIMESTEP/TIMEGRID' in self):
            t = self['Kennsatz/TIMESTEP/TIMEGRID'][:]
        else:
            t = np.array( [0.] , dtype=np.float64 )
        
        if (gmode_time==EAS4_X0DX_G): ## =2 --> i.e. more than one timestep
            t = np.linspace(t[0],t[0]+t[1]*(nt - 1), nt  )
            gmode_time = EAS4_ALL_G
        else:
            #print('gmode_time : '+str(gmode_time))
            pass
        
        if (t.size>1):
            dt = t[1] - t[0]
            duration = t[-1] - t[0]
        else:
            dt = 0.
            duration = 0.
        
        if self.verbose: even_print('nt', '%i'%nt )
        if self.verbose: even_print('dt', '%0.6f'%dt)
        if self.verbose: even_print('duration', '%0.2f'%duration )
        
        # === attach to instance
        
        self.n_scalars    = n_scalars
        self.scalars      = scalars
        self.scalar_n_map = scalar_n_map
        self.t            = t
        self.dt           = dt
        self.nt           = nt
        self.duration     = duration
        
        self.ti           = np.arange(self.nt, dtype=np.float64)
        
        if self.verbose: print(72*'-'+'\n')
        
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
        
        return
    
    def get_mean(self, **kwargs):
        '''
        get spanwise mean of 2D EAS4 file
        '''
        axis = kwargs.get('axis',(2,)) ## default: avg over [z]
        
        if (self.measType!='mean'):
            raise NotImplementedError('get_mean() not yet valid for measType=\'%s\''%self.measType)
        
        ## numpy structured array
        data_mean = np.zeros(shape=(self.nx,self.ny), dtype={'names':self.scalars, 'formats':self.scalars_dtypes})
        
        for si, scalar in enumerate(self.scalars):
            scalar_dtype = self.scalars_dtypes[si]
            dset_path = 'Data/%s/ts_%06d/par_%06d'%(self.domainName,0,self.scalar_n_map[scalar])
            data = np.copy(self[dset_path][()])
            ## perform np.mean() with float64 accumulator!
            scalar_mean = np.mean(data, axis=axis, dtype=np.float64).astype(scalar_dtype)
            data_mean[scalar] = scalar_mean
        
        return data_mean
    
    def make_xdmf(self):
        print('make_xdmf() not yet implemented for turbx class EAS4')
        raise NotImplementedError
        return
