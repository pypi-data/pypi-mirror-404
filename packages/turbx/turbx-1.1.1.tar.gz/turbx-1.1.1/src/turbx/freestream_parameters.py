import numpy as np

from .utils import even_print

# ======================================================================

class freestream_parameters(object):
    '''
    calculate freestream parameters & characteristic scales for dry air (21% O2 / 78% N2) and standard conditions
    '''
    
    def __init__(self, Re=None, M_inf=None, lchar=None, U_inf=None, T_inf=None, p_inf=None, rho_inf=None, Pr=None, compressible=True, HTfac=1.0):
        
        if not isinstance(compressible, bool):
            raise ValueError
        
        self.compressible = compressible
        
        ## dry air (21% O2 / 78% N2)
        M_molar = 28.9647e-3        ## molar mass [kg/mol]
        R_molar = 8.31446261815324  ## molar gas constant [J/(K·mol)]
        R       = R_molar / M_molar ## specific / individual gas constant [J/(kg·K)]
        cp      = (7/2)*R           ## isobaric specific heat (ideal gas) [J/(kg·K)]
        cv      = (5/2)*R           ## isochoric specific heat (ideal gas) [J/(kg·K)]
        kappa   = cp/cv
        
        # === get freestream static T_inf, p_inf, ρ_inf
        
        # T_inf   = 273.15 + 15        ## freestream static temperature [K]
        # p_inf   = 101325.            ## freestream static pressure [Pa]
        # rho_inf = 1.2249908312142817 ## freestream mass density [kg/m³]
        
        if all([(T_inf is None),(p_inf is None),(rho_inf is None)]): ## NONE of T,p,ρ provided --> use standard atmosphere
            T_inf   = 273.15 + 15
            p_inf   = 101325.
            rho_inf = p_inf/(R*T_inf)
        elif all([(T_inf is not None),(p_inf is not None),(rho_inf is not None)]): ## ALL T,p,ρ provided --> check
            np.testing.assert_allclose(rho_inf, p_inf/(R*T_inf), rtol=1e-12, atol=1e-12)
        elif (T_inf is not None) and (p_inf is None) and (rho_inf is None): ## only T provided
            p_inf   = 101325.
            rho_inf = p_inf/(R*T_inf)
        elif (T_inf is None) and (p_inf is not None) and (rho_inf is None): ## only p provided
            T_inf   = 273.15 + 15
            rho_inf = p_inf/(R*T_inf)
        elif (T_inf is None) and (p_inf is None) and (rho_inf is not None): ## only ρ provided
            T_inf   = 273.15 + 15
            p_inf = rho_inf*R*T_inf
        elif (T_inf is not None) and (p_inf is not None) and (rho_inf is None): ## T & p provided
            rho_inf = p_inf/(R*T_inf)
        elif (T_inf is not None) and (p_inf is None) and (rho_inf is not None): ## T & ρ provided
            p_inf = rho_inf*R*T_inf
        elif (T_inf is None) and (p_inf is not None) and (rho_inf is not None): ## p & ρ provided
            T_inf = p_inf/(rho_inf*R)
        else:
            raise ValueError('this should never happen.')
        
        np.testing.assert_allclose(rho_inf, p_inf/(R*T_inf), rtol=1e-12, atol=1e-12)
        
        # === get freestream dynamic & kinematic viscosities using Sutherland's Law
        
        ## Sutherland's Law : dynamic viscosity : μ(T)
        ## https://www.cfd-online.com/Wiki/Sutherland%27s_law
        ## White 2006 'Viscous Fluid Flow' 3rd Edition, p. 28-31
        S_Suth      = 110.4    ## [K] --> Sutherland temperature
        mu_Suth_ref = 1.716e-5 ## [kg/(m·s)] --> μ of air at T_Suth_ref = 273.15 [K]
        T_Suth_ref  = 273.15   ## [K]
        C_Suth      = mu_Suth_ref/(T_Suth_ref**(3/2))*(T_Suth_ref + S_Suth) ## [kg/(m·s·√K)]
        
        mu_inf_1 = C_Suth*T_inf**(3/2)/(T_inf+S_Suth) ## [Pa·s] | [N·s/m²]
        mu_inf_2 = mu_Suth_ref*(T_inf/T_Suth_ref)**(3/2) * ((T_Suth_ref+S_Suth)/(T_inf+S_Suth)) ## [Pa·s] | [N·s/m²]
        np.testing.assert_allclose(mu_inf_1, mu_inf_2, rtol=1e-12, atol=1e-12)
        mu_inf = mu_inf_1
        
        nu_inf = mu_inf / rho_inf ## kinematic viscosity [m²/s] --> momentum diffusivity
        
        # === get Prandtl number, thermal conductivity, thermal diffusivity
        
        if (Pr is None):
            
            ## Sutherland's Law : thermal conductivity : k(T)
            ## White 2006 'Viscous Fluid Flow' 3rd Edition, p. 28-31
            k_Suth_ref = 0.0241 ## [W/(m·K)] reference thermal conductivity
            Sk_Suth    = 194.0  ## [K]
            k_inf      = k_Suth_ref*(T_inf/T_Suth_ref)**(3/2) * ((T_Suth_ref+Sk_Suth)/(T_inf+Sk_Suth)) ## thermal conductivity [W/(m·K)]
            
            alpha     = k_inf/(rho_inf*cp) ## thermal diffusivity [m²/s]
            Pr        = nu_inf/alpha       ## [-] ==cp·mu/k_inf
        
        else:
            
            k_inf = cp*mu_inf/Pr ## thermal conductivity [W/(m·K)]
            alpha = k_inf/(rho_inf*cp) ## thermal diffusivity [m²/s]
        
        np.testing.assert_allclose(nu_inf/alpha, cp*mu_inf/k_inf, rtol=1e-12, atol=1e-12)
        np.testing.assert_allclose(Pr, nu_inf/alpha, rtol=1e-12, atol=1e-12)
        np.testing.assert_allclose(Pr, cp*mu_inf/k_inf, rtol=1e-12, atol=1e-12)
        
        # === get freestream velocity magnitude U_inf, freestream speed of sound a_inf, and Mach number M_inf
        
        a_inf = np.sqrt(kappa*R*T_inf) ## speed of sound [m/s]
        
        if (not self.compressible): ## incompressible
            
            if (U_inf is None):
                raise ValueError('if compressible=False, then providing U_inf is required')
            if (M_inf is not None) and (M_inf != 0.):
                raise ValueError('if compressible=False, then providing a non-zero M_inf makes no sense')
            
            M_inf = 0.
            a_inf = np.inf
        
        else: ## compressible
            
            if (U_inf is None) and (M_inf is None):
                raise ValueError('provide either U_inf or M_inf')
            elif (U_inf is not None) and (M_inf is not None):
                np.testing.assert_allclose(M_inf, U_inf/a_inf, rtol=1e-12, atol=1e-12)
            elif (U_inf is None) and (M_inf is not None):
                U_inf = a_inf * M_inf ## velocity freestream [m/s]
            elif (U_inf is not None) and (M_inf is None):
                M_inf = U_inf / a_inf ## Mach number
            else:
                raise ValueError('this should never happen.')
        
        np.testing.assert_allclose(M_inf, U_inf/a_inf, rtol=1e-12, atol=1e-12)
        
        # === get characteristic freestream scales: length, time, velocity
        
        if (lchar is None) and (Re is None):
            raise ValueError('provide either lchar or Re')
        elif (lchar is not None) and (Re is not None):
            np.testing.assert_allclose(Re, lchar * U_inf / nu_inf, rtol=1e-12, atol=1e-12)
        elif (lchar is None) and (Re is not None):
            lchar = Re * nu_inf / U_inf
        elif (lchar is not None) and (Re is None):
            Re = lchar * U_inf / nu_inf
        else:
            raise ValueError('this should never happen.')
        
        np.testing.assert_allclose(Re, lchar*U_inf/nu_inf, rtol=1e-12, atol=1e-12)
        
        tchar = lchar / U_inf
        uchar = lchar / tchar
        if not np.isclose(uchar, U_inf, rtol=1e-12):
            raise AssertionError('U_inf!=uchar')
        
        np.testing.assert_allclose(lchar, uchar*tchar, rtol=1e-12, atol=1e-12)
        
        # === get isentropic total state
        
        if self.compressible:
            T_tot   = T_inf   * (1 + (kappa-1)/2 * M_inf**2)
            p_tot   = p_inf   * (1 + (kappa-1)/2 * M_inf**2)**(kappa/(kappa-1))
            rho_tot = rho_inf * (1 + (kappa-1)/2 * M_inf**2)**(1/(kappa-1))
        else:
            T_tot   = T_inf + U_inf**2 / (2 * cp)
            p_tot   = p_inf + 0.5*rho_inf*U_inf**2 ## Bernoulli
            rho_tot = p_tot/(R*T_tot)
        
        np.testing.assert_allclose(T_tot , T_inf + U_inf**2/(2*cp) , rtol=1e-12, atol=1e-12)
        np.testing.assert_allclose(p_tot , rho_tot*R*T_tot         , rtol=1e-12, atol=1e-12)
        
        # === get wall temperatures for a turbulent boundary layer
        
        recov_fac = pow(Pr,1/3) ## recovery factor (turbulent flat plate boundary layer)
        Taw       = T_inf + recov_fac * U_inf**2/(2*cp) ## adiabatic wall temperature
        Tw        = T_inf + recov_fac * U_inf**2/(2*cp) * HTfac ## wall temperature (with heat transfer factor)
        
        # === attach to self
        
        self.R_molar     = R_molar
        self.M_molar     = M_molar
        self.R           = R
        self.cp          = cp
        self.cv          = cv
        self.kappa       = kappa
        
        self.T_inf       = T_inf
        self.p_inf       = p_inf
        self.rho_inf     = rho_inf
        
        self.S_Suth      = S_Suth
        self.mu_Suth_ref = mu_Suth_ref
        self.T_Suth_ref  = T_Suth_ref
        self.C_Suth      = C_Suth
        self.mu_inf      = mu_inf
        self.nu_inf      = nu_inf
        
        #self.k_Suth_ref  = k_Suth_ref
        #self.Sk_Suth     = Sk_Suth
        self.k_inf       = k_inf
        
        self.alpha       = alpha
        self.Pr          = Pr
        
        self.M_inf       = M_inf
        self.a_inf       = a_inf
        self.U_inf       = U_inf
        
        self.Re          = Re
        self.lchar       = lchar
        self.tchar       = tchar
        self.uchar       = uchar
        
        self.T_tot       = T_tot
        self.p_tot       = p_tot
        self.rho_tot     = rho_tot
        
        self.recov_fac   = recov_fac
        self.HTfac       = HTfac
        self.Taw         = Taw
        self.Tw          = Tw
    
    def set_Re(self, Re):
        '''
        set reference Reynolds Number, which determines lchar & tchar
        '''
        self.Re    = Re
        self.lchar = Re * self.nu_inf / self.U_inf
        self.tchar = self.lchar / self.U_inf
        self.uchar = self.lchar / self.tchar
        if not np.isclose(self.uchar, self.U_inf, rtol=1e-12):
            raise AssertionError('U_inf!=uchar')
        return
    
    def print(self,):
        
        even_print('R_molar'        , '%0.6f [J/(K·mol)]'   % self.R_molar    )
        even_print('M_molar'        , '%0.5e [kg/mol]'      % self.M_molar    )
        even_print('R'              , '%0.3f [J/(kg·K)]'    % self.R          )
        even_print('cp'             , '%0.3f [J/(kg·K)]'    % self.cp         )
        even_print('cv'             , '%0.3f [J/(kg·K)]'    % self.cv         )
        even_print('kappa'          , '%0.3f [-]'           % self.kappa      )
        
        print(72*'-')
        even_print('compressible'   , '%s'                  % self.compressible )
        even_print('M_inf'          , '%0.4f [-]'           % self.M_inf      )
        even_print('Re'             , '%0.4f [-]'           % self.Re         )
        
        even_print('T_inf'          , '%0.4f [K]'           % self.T_inf      )
        even_print('T_tot'          , '%0.4f [K]'           % self.T_tot      )
        #even_print('Tw'             , '%0.4f [K]'           % self.Tw         )
        #even_print('Taw'            , '%0.4f [K]'           % self.Taw        )
        even_print('p_inf'          , '%0.1f [Pa]'          % self.p_inf      )
        even_print('p_tot'          , '%0.1f [Pa]'          % self.p_tot      )
        even_print('rho_inf'        , '%0.4f [kg/m³]'       % self.rho_inf    )
        even_print('rho_tot'        , '%0.4f [kg/m³]'       % self.rho_tot    )
        
        even_print('T_Suth_ref'     , '%0.2f [K]'           % self.T_Suth_ref )
        even_print('C_Suth'         , '%0.3e [kg/(m·s·√K)]' % self.C_Suth     )
        even_print('S_Suth'         , '%0.2f [K]'           % self.S_Suth     )
        
        even_print('mu_inf'         , '%0.5e [kg/(m·s)]'    % self.mu_inf     )
        even_print('nu_inf'         , '%0.5e [m²/s]'        % self.nu_inf     )
        even_print('k_inf'          , '%0.5e [W/(m·K)]'     % self.k_inf      )
        even_print('alpha'          , '%0.5e [m²/s]'        % self.alpha      )
        
        even_print('Pr'             , '%0.5f [-]'           % self.Pr         )
        #even_print('recovery factor', '%0.5f [-]'           % self.recov_fac  )
        
        even_print('a_inf'          , '%0.5f [m/s]'         % self.a_inf      )
        even_print('U_inf'          , '%0.5f [m/s]'         % self.U_inf      )
        even_print('uchar'          , '%0.5f [m/s]'         % self.uchar      )
        even_print('lchar'          , '%0.5e [m]'           % self.lchar      )
        even_print('tchar'          , '%0.5e [s]'           % self.tchar      )
        print(72*'-')
        
        return
