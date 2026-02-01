import io
import struct

import numpy as np

from .utils import even_print

# ======================================================================

class eas3:
    '''
    Interface class for EAS3 files (legacy binary NS3D output format)
    - only binary read is supported, no writing
    '''
    
    def __init__(self, fname, **kwargs):
        '''
        initialize class instance
        '''
        self.fname   = fname
        self.verbose = kwargs.get('verbose',True)
        
        if isinstance(fname, str):
            self.f = open(fname,'rb')
        elif isinstance(fname, io.BytesIO):
            self.f = fname
        else:
            raise TypeError('fname should be type str or io.BytesIO')
        
        self.udef = self.get_header()
    
    def __enter__(self):
        '''
        for use with python 'with' statement
        '''
        #print('opening from enter() --> used with statement')
        return self
    
    def __exit__(self, exception_type, exception_value, exception_traceback):
        '''
        for use with python 'with' statement
        '''
        self.f.close()
        
        if exception_type is not None:
            print('\nsafely closed EAS3 due to exception')
            print(72*'-')
            print('exception type : '+str(exception_type))
        if exception_value is not None:
            print('exception_value : '+str(exception_value))
        if exception_traceback is not None:
            print('exception_traceback : '+str(exception_traceback))
        if exception_type is not None:
            print(72*'-')
    
    def close(self):
        '''
        close() passthrough to handle from binary open()
        '''
        self.f.close()
    
    def get_header(self, **kwargs):
        
        ATTRLEN     = kwargs.get('ATTRLEN',10)
        UDEFLEN     = kwargs.get('UDEFLEN',20)
        ChangeGmode = kwargs.get('ChangeGmode',1)
        
        ## Definitions
        #EAS2=1; EAS3=2
        IEEES=1; IEEED=2; IEEEQ=3
        #EAS3_NO_ATTR=1
        EAS3_ALL_ATTR=2
        EAS3_NO_G=1
        EAS3_X0DX_G=2
        #EAS3_UDEF_G=3
        EAS3_ALL_G=4
        #EAS3_FULL_G=5
        #EAS3_NO_UDEF=1
        EAS3_ALL_UDEF=2
        #EAS3_INT_UDEF=3
        
        self.IEEES = IEEES
        self.IEEED = IEEED
        self.IEEEQ = IEEEQ
        
        ## Identifier: 20 byte character
        #identifier = self.f.read(20).strip()
        
        ## File type: 8 byte integer
        #file_type = struct.unpack('!q',self.f.read(8))[0]
        
        ## Accuracy: 8 byte integer
        accuracy = struct.unpack('!q',self.f.read(8))[0]
        self.accuracy = accuracy
        
        if (self.accuracy == self.IEEES):
            self.dtype = np.float32
        elif (self.accuracy == self.IEEED):
            self.dtype = np.float64
        elif (self.accuracy == self.IEEEQ):
            self.dtype = np.float128
        else:
            raise ValueError('precision not identifiable')
        
        ## Array sizes: each 8 byte integer
        nzs   = struct.unpack('!q',self.f.read(8))[0]
        npar  = struct.unpack('!q',self.f.read(8))[0]
        ndim1 = struct.unpack('!q',self.f.read(8))[0]
        ndim2 = struct.unpack('!q',self.f.read(8))[0]
        ndim3 = struct.unpack('!q',self.f.read(8))[0]
        
        self.ndim1 = ndim1
        self.ndim2 = ndim2
        self.ndim3 = ndim3
        self.npar  = npar
        self.nzs   = nzs
        
        ## Attribute mode: 8 byte integer
        attribute_mode = struct.unpack('!q',self.f.read(8))[0]
        
        ## Geometry mode: each 8 byte integer
        gmode_time  = struct.unpack('!q',self.f.read(8))[0]
        gmode_param = struct.unpack('!q',self.f.read(8))[0]
        gmode_dim1  = struct.unpack('!q',self.f.read(8))[0]  
        gmode_dim2  = struct.unpack('!q',self.f.read(8))[0]
        gmode_dim3  = struct.unpack('!q',self.f.read(8))[0]
        
        ## Array sizes for geometry data: each 8 byte integer
        size_time  = struct.unpack('!q',self.f.read(8))[0]
        size_param = struct.unpack('!q',self.f.read(8))[0]
        size_dim1  = struct.unpack('!q',self.f.read(8))[0]
        size_dim2  = struct.unpack('!q',self.f.read(8))[0]
        size_dim3  = struct.unpack('!q',self.f.read(8))[0]
        
        ## Specification of user defined data: 8 byte integer
        udef = struct.unpack('!q',self.f.read(8))[0]
        
        ## Array sizes for used defined data: each 8 byte integer
        udef_char_size = struct.unpack('!q',self.f.read(8))[0]
        udef_int_size  = struct.unpack('!q',self.f.read(8))[0]
        udef_real_size = struct.unpack('!q',self.f.read(8))[0]
        
        ## Time step array: nzs x 8 byte
        time_step = np.zeros(nzs,int)
        for it in range(nzs):
            time_step[it] = struct.unpack('!q',self.f.read(8))[0]
        
        if attribute_mode==EAS3_ALL_ATTR:
            ## Time step attributes
            attr_time = [ self.f.read(ATTRLEN).decode('UTF-8').strip() ]
            for it in range(1,nzs):
                attr_time.append( self.f.read(ATTRLEN).decode('UTF-8').strip() )
            ## Parameter attributes
            attr_param = [ self.f.read(ATTRLEN).decode('UTF-8').strip() ]
            for it in range(1,npar):
                attr_param.append( self.f.read(ATTRLEN).decode('UTF-8').strip() )
            
            # Spatial attributes
            attr_dim1 = self.f.read(ATTRLEN).decode('UTF-8').strip()
            attr_dim2 = self.f.read(ATTRLEN).decode('UTF-8').strip()
            attr_dim3 = self.f.read(ATTRLEN).decode('UTF-8').strip()
        
        ## If geometry mode > EAS3_NO_G for time
        if gmode_time == EAS3_X0DX_G:
            time_data = np.zeros(2)
            for it in range(2):
                time_data[it] = struct.unpack('!d',self.f.read(8))[0]
        elif gmode_time == EAS3_ALL_G:
            time_data = np.zeros(size_time)
            for it in range(size_time):
                time_data[it] = struct.unpack('!d',self.f.read(8))[0]
        else:
            time_data = np.zeros(1)
        
        ## If geometry mode > EAS3_NO_G for parameters
        if gmode_param > EAS3_NO_G:
            param = np.zeros(size_param)
            for it in range(size_param):
                param[it] = struct.unpack('!d',self.f.read(8))[0]
        
        ## If geometry mode > EAS3_NO_G for dimensions 1 to 3
        dim1_data = np.zeros(size_dim1)
        if gmode_dim1 > EAS3_NO_G:
            for it in range(size_dim1):
                dim1_data[it] = struct.unpack('!d',self.f.read(8))[0]
            if abs(dim1_data[0]) < 1e-18: dim1_data[0] = 0.   
        dim2_data = np.zeros(size_dim2)
        if gmode_dim2 > EAS3_NO_G:
            for it in range(size_dim2):
                dim2_data[it] = struct.unpack('!d',self.f.read(8))[0]
            if abs(dim2_data[0]) < 1e-18: dim2_data[0] = 0.
        dim3_data = np.zeros(size_dim3)
        if gmode_dim3 > EAS3_NO_G:
            for it in range(size_dim3):
                dim3_data[it] = struct.unpack('!d',self.f.read(8))[0]
        else:
            dim3_data = None
        
        ## If user-defined data is chosen 
        if udef==EAS3_ALL_UDEF:
            udef_char = []
            for it in range(udef_char_size):
                udef_char.append(self.f.read(UDEFLEN).decode('UTF-8').strip())
            udef_int = np.zeros(udef_int_size,int)
            for it in range(udef_int_size):
                udef_int[it] = struct.unpack('!q',self.f.read(8))[0]
            udef_real = np.zeros(udef_real_size)
            for it in range(udef_real_size):
                udef_real[it] = struct.unpack('!d',self.f.read(8))[0]
        
        ## Option: convert gmode=EAS3_X0DX_G to gmode=EAS3_ALL_G
        if ChangeGmode==1:
            if gmode_dim1==EAS3_X0DX_G:
                dim1_data = np.linspace(dim1_data[0],dim1_data[0]+dim1_data[1]*(ndim1-1), ndim1)
                gmode_dim1=EAS3_ALL_G
            if gmode_dim2==EAS3_X0DX_G:
                dim2_data = np.linspace(dim2_data[0],dim2_data[0]+dim2_data[1]*(ndim2-1), ndim2)
                gmode_dim2=EAS3_ALL_G
            if gmode_dim3==EAS3_X0DX_G:
                dim3_data = np.linspace(dim3_data[0],dim3_data[0]+dim3_data[1]*(ndim3-1), ndim3)
                gmode_dim3=EAS3_ALL_G
            if gmode_time==EAS3_X0DX_G:
                time_data = np.linspace(time_data[0],time_data[0]+time_data[1]*(nzs  -1), nzs  )
                gmode_time=EAS3_ALL_G
        
        # ===
        
        self.attr_param = attr_param
        self.scalars    = attr_param
        self.t          = time_data
        self.nt         = self.t.size
        
        if (attr_dim1=='x'):
            self.x = dim1_data
        elif (attr_dim1=='y'):
            self.y = dim1_data
        elif (attr_dim1=='z'):
            self.z = dim1_data
        else:
            raise ValueError('attr_dim1 = %s not identifiable as any x,y,z'%attr_dim1)
        
        if (attr_dim2=='x'):
            self.x = dim2_data
        elif (attr_dim2=='y'):
            self.y = dim2_data
        elif (attr_dim2=='z'):
            self.z = dim2_data
        else:
            raise ValueError('attr_dim2 = %s not identifiable as any x,y,z'%attr_dim2)
        
        if (attr_dim3=='x'):
            self.x = dim3_data
        elif (attr_dim3=='y'):
            self.y = dim3_data
        elif (attr_dim3=='z'):
            self.z = dim3_data
        else:
            raise ValueError('attr_dim3 = %s not identifiable as any x,y,z'%attr_dim3)
        
        # === transpose order to [x,y,z]
        
        if all([(attr_dim1=='x'),(attr_dim2=='y'),(attr_dim3=='z')]):
            self.axes_transpose_xyz = (0,1,2)
        elif all([(attr_dim1=='y'),(attr_dim2=='x'),(attr_dim3=='z')]):
            self.axes_transpose_xyz = (1,0,2)
        elif all([(attr_dim1=='z'),(attr_dim2=='y'),(attr_dim3=='x')]):
            self.axes_transpose_xyz = (2,1,0)
        elif all([(attr_dim1=='x'),(attr_dim2=='z'),(attr_dim3=='y')]):
            self.axes_transpose_xyz = (0,2,1)
        elif all([(attr_dim1=='y'),(attr_dim2=='z'),(attr_dim3=='x')]):
            self.axes_transpose_xyz = (2,0,1)
        elif all([(attr_dim1=='z'),(attr_dim2=='x'),(attr_dim3=='y')]):
            self.axes_transpose_xyz = (1,2,0)
        else:
            raise ValueError('could not determine axes transpose')
        
        # ===
        
        self.nx  = self.x.shape[0]
        self.ny  = self.y.shape[0]
        self.nz  = self.z.shape[0]
        self.ngp = self.nx*self.ny*self.nz
        
        if self.verbose: print(72*'-')
        if self.verbose: even_print('nx', '%i'%self.nx )
        if self.verbose: even_print('ny', '%i'%self.ny )
        if self.verbose: even_print('nz', '%i'%self.nz )
        if self.verbose: even_print('ngp', '%i'%self.ngp )
        if self.verbose: print(72*'-')
        
        if self.verbose: even_print('x_min', '%0.2f'%self.x.min())
        if self.verbose: even_print('x_max', '%0.2f'%self.x.max())
        if self.verbose: even_print('dx begin : end', '%0.3E : %0.3E'%( (self.x[1]-self.x[0]), (self.x[-1]-self.x[-2]) ))
        if self.verbose: even_print('y_min', '%0.2f'%self.y.min())
        if self.verbose: even_print('y_max', '%0.2f'%self.y.max())
        if self.verbose: even_print('dy begin : end', '%0.3E : %0.3E'%( (self.y[1]-self.y[0]), (self.y[-1]-self.y[-2]) ))
        if self.verbose: even_print('z_min', '%0.2f'%self.z.min())
        if self.verbose: even_print('z_max', '%0.2f'%self.z.max())        
        if self.verbose: even_print('dz begin : end', '%0.3E : %0.3E'%( (self.z[1]-self.z[0]), (self.z[-1]-self.z[-2]) ))
        if self.verbose: print(72*'-'+'\n')
        
        # ===
        
        ## make a python dict from udef vectors
        udef_dict = {}
        for i in range(len(udef_char)):
            if (udef_char[i]!=''):
                if (udef_int[i]!=0):
                    udef_dict[udef_char[i]] = int(udef_int[i])
                elif (udef_real[i]!=0.):
                    udef_dict[udef_char[i]] = float(udef_real[i])
                else:
                    udef_dict[udef_char[i]] = 0.
        
        if self.verbose:
            print('udef from EAS3\n' + 72*'-')
            for key in udef_dict:
                if isinstance(udef_dict[key],float):
                    even_print(key, '%0.8f'%udef_dict[key])
                elif isinstance(udef_dict[key],int):
                    even_print(key, '%i'%udef_dict[key])
                else:
                    #print(type(udef_dict[key]))
                    raise TypeError('udef dict item not float or int')
            print(72*'-'+'\n')
        
        self.Ma    = udef_dict['Ma']
        self.Re    = udef_dict['Re']
        self.Pr    = udef_dict['Pr']
        self.kappa = udef_dict['kappa']
        self.R     = udef_dict['R']
        
        ## get T_inf
        if ('T_unend' in udef_dict):
            self.T_inf = udef_dict['T_unend']
        elif ('T_inf' in udef_dict):
            self.T_inf = udef_dict['T_inf']
        elif ('Tinf' in udef_dict):
            self.T_inf = udef_dict['Tinf']
        else:
            raise ValueError('T_inf not found in udef')
        
        ## get p_inf
        if ('p_unend' in udef_dict):
            self.p_inf = udef_dict['p_unend']
        elif ('p_inf' in udef_dict):
            self.p_inf = udef_dict['p_inf']
        elif ('pinf' in udef_dict):
            self.p_inf = udef_dict['pinf']
        else:
            raise ValueError('p_inf not found in udef')
        
        ## !!! import what is called 'C_Suth' in NS3D as 'S_Suth' !!!
        self.S_Suth = udef_dict['C_Suth'] ## [K] --> Sutherland temperature, usually 110.4 [K] for air
        
        self.mu_Suth_ref = udef_dict['mu_Suth_ref'] ## usually 1.716e-05 [kg/(m·s)] --> μ of air at T_Suth_ref = 273.15 [K]
        self.T_Suth_ref  = udef_dict['T_Suth_ref'] ## usually 273.15 [K]
        
        self.C_Suth = self.mu_Suth_ref/(self.T_Suth_ref**(3/2))*(self.T_Suth_ref + self.S_Suth) ## ~1.458e-6 [kg/(m·s·√K)]
        
        ## derived values
        self.rho_inf = self.p_inf/(self.R*self.T_inf) ## mass density [kg/m³]
        self.mu_inf  = self.mu_Suth_ref*(self.T_inf/self.T_Suth_ref)**(3/2) * ((self.T_Suth_ref+self.S_Suth)/(self.T_inf+self.S_Suth)) ## [Pa s] | [N s m^-2]
        self.nu_inf  = self.mu_inf / self.rho_inf ## kinematic viscosity [m²/s] --> momentum diffusivity
        
        ## additional
        if ('total_avg_time' in udef_dict):
            self.total_avg_time = udef_dict['total_avg_time']
        if ('total_avg_iter_count' in udef_dict):
            self.total_avg_iter_count = udef_dict['total_avg_iter_count']
        if ('nz' in udef_dict):
            self.nz = udef_dict['nz']
        if ('cp' in udef_dict):
            self.cp = udef_dict['cp']
        if ('cv' in udef_dict):
            self.cv = udef_dict['cv']
        
        # ===
        
        if self.verbose: print(72*'-')
        if self.verbose: even_print('Ma'          , '%0.2f [-]'           % self.Ma          )
        if self.verbose: even_print('Re'          , '%0.1f [-]'           % self.Re          )
        if self.verbose: even_print('Pr'          , '%0.3f [-]'           % self.Pr          )
        if self.verbose: even_print('T_inf'       , '%0.3f [K]'           % self.T_inf       )
        if self.verbose: even_print('p_inf'       , '%0.1f [Pa]'          % self.p_inf       )
        if self.verbose: even_print('kappa'       , '%0.3f [-]'           % self.kappa       )
        if self.verbose: even_print('R'           , '%0.3f [J/(kg·K)]'    % self.R           )
        if self.verbose: even_print('mu_Suth_ref' , '%0.6E [kg/(m·s)]'    % self.mu_Suth_ref )
        if self.verbose: even_print('T_Suth_ref'  , '%0.2f [K]'           % self.T_Suth_ref  )
        if self.verbose: even_print('C_Suth'      , '%0.5e [kg/(m·s·√K)]' % self.C_Suth      )
        if self.verbose: even_print('S_Suth'      , '%0.2f [K]'           % self.S_Suth      )
        if self.verbose: print(72*'-')
        
        self.a_inf     = np.sqrt(self.kappa*self.R*self.T_inf)
        self.U_inf     = self.Ma*self.a_inf
        self.cp        = self.R*self.kappa/(self.kappa-1.)
        self.cv        = self.cp/self.kappa
        self.recov_fac = self.Pr**(1/3)
        self.Taw       = self.T_inf + self.recov_fac*self.U_inf**2/(2*self.cp)
        self.lchar     = self.Re*self.nu_inf/self.U_inf
        
        if self.verbose: even_print('rho_inf'         , '%0.3f [kg/m³]'    % self.rho_inf   )
        if self.verbose: even_print('mu_inf'          , '%0.6E [kg/(m·s)]' % self.mu_inf    )
        if self.verbose: even_print('nu_inf'          , '%0.6E [m²/s]'     % self.nu_inf    )
        if self.verbose: even_print('a_inf'           , '%0.6f [m/s]'      % self.a_inf     )
        if self.verbose: even_print('U_inf'           , '%0.6f [m/s]'      % self.U_inf     )
        if self.verbose: even_print('cp'              , '%0.3f [J/(kg·K)]' % self.cp        )
        if self.verbose: even_print('cv'              , '%0.3f [J/(kg·K)]' % self.cv        )
        #if self.verbose: even_print('recovery factor' , '%0.6f [-]'        % self.recov_fac )
        #if self.verbose: even_print('Taw'             , '%0.3f [K]'        % self.Taw       )
        if self.verbose: even_print('lchar'           , '%0.6E [m]'        % self.lchar     )
        if self.verbose: print(72*'-'+'\n')
        
        # ===
        
        udef_char = [    'Ma',     'Re',     'Pr',     'kappa',    'R',    'p_inf',    'T_inf',    'C_Suth',    'mu_Suth_ref',    'T_Suth_ref' ]
        udef_real = [self.Ma , self.Re , self.Pr , self.kappa, self.R, self.p_inf, self.T_inf, self.C_Suth, self.mu_Suth_ref, self.T_Suth_ref  ]
        udef = dict(zip(udef_char, udef_real))
        
        return udef
