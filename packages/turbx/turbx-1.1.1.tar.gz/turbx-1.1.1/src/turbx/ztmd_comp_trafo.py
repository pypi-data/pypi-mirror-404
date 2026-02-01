import sys
import timeit

import numpy as np
from tqdm import tqdm

from .bl import (
    calc_d1,
    calc_d2,
    calc_d3,
    calc_d99_1d,
    calc_dRC,
    calc_I2,
    calc_I3,
)
from .compressible_transform import (
    comp_transform_GFM,
    comp_transform_TL,
    comp_transform_VD,
    comp_transform_VIPL,
)
from .utils import even_print, format_time_string

'''
========================================================================
Compressibility transformations
========================================================================
'''

# ======================================================================

def _calc_VDII(self, **kwargs):
    '''
    Transform [cf,Reθ] to 'incompressible' analog according to Van Driest (1956)
    - Fc (compressibility factor on cf)
    - Reδ2 = (μe/μw)·Reθ
    - cfi = Fc·cf
    Often referred to as 'Van Driest II' compressibility transform
    -----
    - Van Driest (1956) 'The Problem of Aerodynamic Heating'
      https://web.stanford.edu/~jurzay/ME356_files/vandriest_aeroheating.pdf
    - White (2006) 'Viscous Fluid Flow' 7-7 and 7-8 (p.547-556)
    '''
    
    verbose   = kwargs.get('verbose',True)
    adiabatic = kwargs.get('adiabatic',False) ## compute Fc as special case of adiabatic
    
    if verbose: print('\n'+'ztmd.calc_VDII()'+'\n'+72*'-')
    t_start_func = timeit.default_timer()
    
    if verbose: even_print('adiabatic',str(adiabatic))
    
    T_wall   = np.copy( self['data_1Dx/T_wall'][()]   )
    T_edge   = np.copy( self['data_1Dx/T_edge'][()]   )
    #rho_edge = np.copy( self['data_1Dx/rho_edge'][()] )
    #u_edge   = np.copy( self['data_1Dx/u_edge'][()]   )
    
    cf       = np.copy( self['data_1Dx/cf'][()]       )
    #tau_wall = np.copy( self['data_1Dx/tau_wall'][()] )
    
    if adiabatic:
        Fc = np.copy( ((T_wall / T_edge)-1.) / (np.arcsin( (1.-(T_edge/T_wall))**0.5 ))**2 )
    else:
        Taw = self.Taw
        A  = np.copy( (Taw/T_edge + T_wall/T_edge - 2) / np.sqrt( (Taw/T_edge + T_wall/T_edge)**2 - 4*T_wall/T_edge ) )
        B  = np.copy( (Taw/T_edge - T_wall/T_edge    ) / np.sqrt( (Taw/T_edge + T_wall/T_edge)**2 - 4*T_wall/T_edge ) )
        Fc = np.copy( (Taw/T_edge - 1. ) / ( np.arcsin(A) + np.arcsin(B) )**2 )
    
    cf_inc = np.copy( Fc * cf )
    
    # ===
    
    if ('data_1Dx/cf_inc' in self): del self['data_1Dx/cf_inc']
    self.create_dataset('data_1Dx/cf_inc', data=cf_inc, chunks=None)
    if verbose: even_print('data_1Dx/cf_inc','%s'%str(cf_inc.shape))
    
    if ('data_1Dx/Fc' in self): del self['data_1Dx/Fc']
    self.create_dataset('data_1Dx/Fc', data=Fc, chunks=None)
    if verbose: even_print('data_1Dx/Fc','%s'%str(Fc.shape))
    
    self.get_header(verbose=False)
    if verbose: print(72*'-')
    if verbose: print('total time : ztmd.calc_VDII() : %s'%format_time_string((timeit.default_timer() - t_start_func)))
    if verbose: print(72*'-')
    
    return

def _calc_comp_trafo(self, schemes=['VD','VIPL','TL','GFM'], **kwargs):
    '''
    Calculate compressible transformations of data (ZTMD wrapper)
    -----
    'VD'   : Van Driest (1951) ........... https://doi.org/10.2514/8.1895
    'VIPL' : Volpiani et al. (2020) ...... https://doi.org/10.1103/PhysRevFluids.5.052602
    'TL'   : Trettel & Larsson (2016) .... https://doi.org/10.1063/1.4942022
    'GFM'  : Griffin, Fu & Moin (2021) ... https://doi.org/10.1073/pnas.2111144118
    '''
    verbose = kwargs.get('verbose',True)
    
    if verbose: print('\n'+'ztmd.calc_comp_trafo()'+'\n'+72*'-')
    t_start_func = timeit.default_timer()
    
    if 'VD' in schemes:
        u_VD   = np.full((self.nx,self.ny),np.nan,dtype=np.float64)
        
        d1_VD  = np.full((self.nx,),np.nan,dtype=np.float64)
        d2_VD  = np.full((self.nx,),np.nan,dtype=np.float64)
        d3_VD  = np.full((self.nx,),np.nan,dtype=np.float64)
        dRC_VD = np.full((self.nx,),np.nan,dtype=np.float64)
        d99_VD = np.full((self.nx,),np.nan,dtype=np.float64)
        I2_VD  = np.full((self.nx,),np.nan,dtype=np.float64)
        I3_VD  = np.full((self.nx,),np.nan,dtype=np.float64)
        H12_VD = np.full((self.nx,),np.nan,dtype=np.float64)
        H32_VD = np.full((self.nx,),np.nan,dtype=np.float64)
        u_edge_VD = np.full((self.nx,),np.nan,dtype=np.float64)
        u_99_VD   = np.full((self.nx,),np.nan,dtype=np.float64)
    
    if 'VIPL' in schemes:
        u_VIPL   = np.full((self.nx,self.ny),np.nan,dtype=np.float64)
        y_VIPL   = np.full((self.nx,self.ny),np.nan,dtype=np.float64)
        
        d1_VIPL  = np.full((self.nx,),np.nan,dtype=np.float64)
        d2_VIPL  = np.full((self.nx,),np.nan,dtype=np.float64)
        d3_VIPL  = np.full((self.nx,),np.nan,dtype=np.float64)
        dRC_VIPL = np.full((self.nx,),np.nan,dtype=np.float64)
        d99_VIPL = np.full((self.nx,),np.nan,dtype=np.float64)
        I2_VIPL  = np.full((self.nx,),np.nan,dtype=np.float64)
        I3_VIPL  = np.full((self.nx,),np.nan,dtype=np.float64)
        H12_VIPL = np.full((self.nx,),np.nan,dtype=np.float64)
        H32_VIPL = np.full((self.nx,),np.nan,dtype=np.float64)
        u_edge_VIPL = np.full((self.nx,),np.nan,dtype=np.float64)
        u_99_VIPL   = np.full((self.nx,),np.nan,dtype=np.float64)
    
    if 'TL' in schemes:
        u_TL      = np.full((self.nx,self.ny),np.nan,dtype=np.float64)
        u_plus_TL = np.full((self.nx,self.ny),np.nan,dtype=np.float64)
        y_TL      = np.full((self.nx,self.ny),np.nan,dtype=np.float64)
        y_plus_TL = np.full((self.nx,self.ny),np.nan,dtype=np.float64)
        
        d1_TL  = np.full((self.nx,),np.nan,dtype=np.float64)
        d2_TL  = np.full((self.nx,),np.nan,dtype=np.float64)
        d3_TL  = np.full((self.nx,),np.nan,dtype=np.float64)
        dRC_TL = np.full((self.nx,),np.nan,dtype=np.float64)
        d99_TL = np.full((self.nx,),np.nan,dtype=np.float64)
        I2_TL  = np.full((self.nx,),np.nan,dtype=np.float64)
        I3_TL  = np.full((self.nx,),np.nan,dtype=np.float64)
        H12_TL = np.full((self.nx,),np.nan,dtype=np.float64)
        H32_TL = np.full((self.nx,),np.nan,dtype=np.float64)
        u_edge_TL = np.full((self.nx,),np.nan,dtype=np.float64)
        u_99_TL   = np.full((self.nx,),np.nan,dtype=np.float64)
    
    if 'GFM' in schemes:
        u_GFM      = np.full((self.nx,self.ny),np.nan,dtype=np.float64)
        u_plus_GFM = np.full((self.nx,self.ny),np.nan,dtype=np.float64)
        y_GFM      = np.full((self.nx,self.ny),np.nan,dtype=np.float64)
        y_plus_GFM = np.full((self.nx,self.ny),np.nan,dtype=np.float64)
        
        d1_GFM  = np.full((self.nx,),np.nan,dtype=np.float64)
        d2_GFM  = np.full((self.nx,),np.nan,dtype=np.float64)
        d3_GFM  = np.full((self.nx,),np.nan,dtype=np.float64)
        dRC_GFM = np.full((self.nx,),np.nan,dtype=np.float64)
        d99_GFM = np.full((self.nx,),np.nan,dtype=np.float64)
        I2_GFM  = np.full((self.nx,),np.nan,dtype=np.float64)
        I3_GFM  = np.full((self.nx,),np.nan,dtype=np.float64)
        H12_GFM = np.full((self.nx,),np.nan,dtype=np.float64)
        H32_GFM = np.full((self.nx,),np.nan,dtype=np.float64)
        u_edge_GFM = np.full((self.nx,),np.nan,dtype=np.float64)
        u_99_GFM   = np.full((self.nx,),np.nan,dtype=np.float64)
    
    ## Read data
    u    = np.copy( self['data/u'][()].T    )
    u_Fv = np.copy( self['data/u_Fv'][()].T )
    rho  = np.copy( self['data/rho'][()].T  )
    mu   = np.copy( self['data/mu'][()].T   )
    
    u_tau  = np.copy( self['data_1Dx/u_tau'][()]  )
    j_edge = np.copy( self['data_1Dx/j_edge'][()] )
    
    ddy_rho   = np.copy( self['data/ddy_rho'][()].T   )
    ddy_mu    = np.copy( self['data/ddy_mu'][()].T    )
    ddy_u_Fv  = np.copy( self['data/ddy_u_Fv'][()].T  )
    r_uII_vII = np.copy( self['data/r_uII_vII'][()].T )
    
    if verbose:
        progress_bar = tqdm(
            total=self.nx,
            ncols=100,
            desc='calc_comp_trafo()',
            leave=False,
            file=sys.stdout,
            )
    
    ## Main loop
    for i in range(self.nx):
        
        je = j_edge[i]
        
        if 'VD' in schemes:
            u_VD_ = comp_transform_VD(u[i,:], rho[i,:])
            u_VD[i,:] = u_VD_
            y_VD_     = self.y
            
            d1_VD[i]  = calc_d1(y_VD_, u_VD_, j_edge=je)
            d2_VD[i]  = calc_d2(y_VD_, u_VD_, j_edge=je)
            d3_VD[i]  = calc_d3(y_VD_, u_VD_, j_edge=je)
            dRC_VD[i] = calc_dRC(y_VD_, u_VD_, u_tau=u_tau[i], j_edge=je)
            I2_VD[i]  = calc_I2(y_VD_, u_VD_, u_tau=u_tau[i], j_edge=je)
            I3_VD[i]  = calc_I3(y_VD_, u_VD_, u_tau=u_tau[i], j_edge=je)
            H12_VD[i] = d1_VD[i] / d2_VD[i]
            H32_VD[i] = d3_VD[i] / d2_VD[i]
            
            d99_VD[i] = calc_d99_1d(y=y_VD_, u=u_VD_, j_edge=je, interp_kind='cubic')
            u_edge_VD[i] = u_VD[i,je]
            u_99_VD[i] = 0.99*u_VD[i,je]
        
        if 'VIPL' in schemes:
            u_VIPL_, y_VIPL_ = comp_transform_VIPL(self.y, u[i,:], rho[i,:], mu[i,:])
            u_VIPL[i,:] = u_VIPL_
            y_VIPL[i,:] = y_VIPL_
            
            d1_VIPL[i]  = calc_d1(y_VIPL_, u_VIPL_, j_edge=je)
            d2_VIPL[i]  = calc_d2(y_VIPL_, u_VIPL_, j_edge=je)
            d3_VIPL[i]  = calc_d3(y_VIPL_, u_VIPL_, j_edge=je)
            dRC_VIPL[i] = calc_dRC(y_VIPL_, u_VIPL_, u_tau=u_tau[i], j_edge=je)
            I2_VIPL[i]  = calc_I2(y_VIPL_, u_VIPL_, u_tau=u_tau[i], j_edge=je)
            I3_VIPL[i]  = calc_I3(y_VIPL_, u_VIPL_, u_tau=u_tau[i], j_edge=je)
            H12_VIPL[i] = d1_VIPL[i] / d2_VIPL[i]
            H32_VIPL[i] = d3_VIPL[i] / d2_VIPL[i]
            
            d99_VIPL[i] = calc_d99_1d(y=y_VIPL_, u=u_VIPL_, j_edge=je, interp_kind='cubic')
            u_edge_VIPL[i] = u_VIPL_[je]
            u_99_VIPL[i] = 0.99*u_VIPL[i,je]
        
        if 'TL' in schemes: ## Trettel & Larsson
            u_TL_, y_TL_, u_plus_TL_, y_plus_TL_ = comp_transform_TL(
                                                        y=self.y,
                                                        u=u[i,:],
                                                        utau=u_tau[i],
                                                        rho=rho[i,:],
                                                        mu=mu[i,:],
                                                        ddy_mu=ddy_mu[i,:],
                                                        ddy_rho=ddy_rho[i,:],
                                                        )
            
            u_TL[i,:]      = u_TL_
            u_plus_TL[i,:] = u_plus_TL_
            y_TL[i,:]      = y_TL_
            y_plus_TL[i,:] = y_plus_TL_
            
            d1_TL[i]  = calc_d1(y_TL_, u_TL_, j_edge=je)
            d2_TL[i]  = calc_d2(y_TL_, u_TL_, j_edge=je)
            d3_TL[i]  = calc_d3(y_TL_, u_TL_, j_edge=je)
            dRC_TL[i] = calc_dRC(y_TL_, u_TL_, u_tau=u_tau[i], j_edge=je)
            I2_TL[i]  = calc_I2(y_TL_, u_TL_, u_tau=u_tau[i], j_edge=je)
            I3_TL[i]  = calc_I3(y_TL_, u_TL_, u_tau=u_tau[i], j_edge=je)
            H12_TL[i] = d1_TL[i] / d2_TL[i]
            H32_TL[i] = d3_TL[i] / d2_TL[i]
            
            d99_TL[i] = calc_d99_1d(y=y_TL_, u=u_TL_, j_edge=je, interp_kind='cubic')
            u_edge_TL[i] = u_TL_[je]
            u_99_TL[i] = 0.99*u_TL[i,je]
        
        if 'GFM' in schemes: ## Griffin, Fu & Moin
            u_GFM_, y_GFM_, u_plus_GFM_, y_plus_GFM_ = comp_transform_GFM(
                                                            y=self.y,
                                                            uFv=u_Fv[i,:],
                                                            rho=rho[i,:],
                                                            mu=mu[i,:],
                                                            r_uII_vII=r_uII_vII[i,:],
                                                            utau=u_tau[i],
                                                            ddy_u_Fv=ddy_u_Fv[i,:],
                                                            )
            
            u_GFM[i,:]      = u_GFM_
            u_plus_GFM[i,:] = u_plus_GFM_
            y_GFM[i,:]      = y_GFM_
            y_plus_GFM[i,:] = y_plus_GFM_
            
            d1_GFM[i]  = calc_d1(y_GFM_, u_GFM_, j_edge=je)
            d2_GFM[i]  = calc_d2(y_GFM_, u_GFM_, j_edge=je)
            d3_GFM[i]  = calc_d3(y_GFM_, u_GFM_, j_edge=je)
            dRC_GFM[i] = calc_dRC(y_GFM_, u_GFM_, u_tau=u_tau[i], j_edge=je)
            I2_GFM[i]  = calc_I2(y_GFM_, u_GFM_, u_tau=u_tau[i], j_edge=je)
            I3_GFM[i]  = calc_I3(y_GFM_, u_GFM_, u_tau=u_tau[i], j_edge=je)
            H12_GFM[i] = d1_GFM[i] / d2_GFM[i]
            H32_GFM[i] = d3_GFM[i] / d2_GFM[i]
            
            d99_GFM[i] = calc_d99_1d(y=y_GFM_, u=u_GFM_, j_edge=je, interp_kind='cubic')
            u_edge_GFM[i] = u_GFM_[je]
            u_99_GFM[i] = 0.99*u_GFM[i,je]
        
        if verbose: progress_bar.update()
    if verbose: progress_bar.close()
    
    # ===
    
    ## Helper func for writing 1D datasets to data_1Dx/
    def _write_1D(name, arr):
        if name in self: ## Delete if exists
            del self[name]
        self.create_dataset(f'data_1Dx/{name}', data=arr, chunks=None) ## Write
        if verbose:
            even_print(f'data_1Dx/{name}', str(arr.shape))
    
    ## Helper func for writing 2D datasets to data/
    def _write_2D(name, arr):
        if name in self: ## Delete if exists
            del self[name]
        self.create_dataset(f'data/{name}', data=arr.T, chunks=None) ## Write
        if verbose:
            even_print(f'data/{name}', str(arr.shape))
    
    if 'VD' in schemes: ## van-Driest
        _write_2D('u_VD',u_VD)
        
        _write_1D('u_edge_VD' , u_edge_VD )
        _write_1D('u_99_VD'   , u_99_VD   )
        
        _write_1D('d1_VD'  , d1_VD  )
        _write_1D('d2_VD'  , d2_VD  )
        _write_1D('d3_VD'  , d3_VD  )
        _write_1D('dRC_VD' , dRC_VD )
        _write_1D('d99_VD' , d99_VD )
        _write_1D('I2_VD'  , I2_VD  )
        _write_1D('I3_VD'  , I3_VD  )
        _write_1D('H12_VD' , H12_VD )
        _write_1D('H32_VD' , H32_VD )
    
    if 'VIPL' in schemes: ## Volpiani et al.
        _write_2D('u_VIPL',u_VIPL)
        _write_2D('y_VIPL',y_VIPL)
        
        _write_1D('u_edge_VIPL' , u_edge_VIPL )
        _write_1D('u_99_VIPL'   , u_99_VIPL   )
        
        _write_1D('d1_VIPL'  , d1_VIPL  )
        _write_1D('d2_VIPL'  , d2_VIPL  )
        _write_1D('d3_VIPL'  , d3_VIPL  )
        _write_1D('dRC_VIPL' , dRC_VIPL )
        _write_1D('d99_VIPL' , d99_VIPL )
        _write_1D('I2_VIPL'  , I2_VIPL  )
        _write_1D('I3_VIPL'  , I3_VIPL  )
        _write_1D('H12_VIPL' , H12_VIPL )
        _write_1D('H32_VIPL' , H32_VIPL )
    
    if 'TL' in schemes: ## Trettel & Larsson
        _write_2D('u_TL'      , u_TL      )
        _write_2D('u_plus_TL' , u_plus_TL )
        _write_2D('y_TL'      , y_TL      )
        _write_2D('y_plus_TL' , y_plus_TL )
        
        _write_1D('u_edge_TL' , u_edge_TL )
        _write_1D('u_99_TL'   , u_99_TL   )
        
        _write_1D('d1_TL'  , d1_TL  )
        _write_1D('d2_TL'  , d2_TL  )
        _write_1D('d3_TL'  , d3_TL  )
        _write_1D('dRC_TL' , dRC_TL )
        _write_1D('d99_TL' , d99_TL )
        _write_1D('I2_TL'  , I2_TL  )
        _write_1D('I3_TL'  , I3_TL  )
        _write_1D('H12_TL' , H12_TL )
        _write_1D('H32_TL' , H32_TL )
    
    if 'GFM' in schemes: ## Griffin,Fu & Moin
        _write_2D('u_GFM'      , u_GFM      )
        _write_2D('u_plus_GFM' , u_plus_GFM )
        _write_2D('y_GFM'      , y_GFM      )
        _write_2D('y_plus_GFM' , y_plus_GFM )
        
        _write_1D('u_edge_GFM' , u_edge_GFM )
        _write_1D('u_99_GFM'   , u_99_GFM   )
        
        _write_1D('d1_GFM'  , d1_GFM  )
        _write_1D('d2_GFM'  , d2_GFM  )
        _write_1D('d3_GFM'  , d3_GFM  )
        _write_1D('dRC_GFM' , dRC_GFM )
        _write_1D('d99_GFM' , d99_GFM )
        _write_1D('I2_GFM'  , I2_GFM  )
        _write_1D('I3_GFM'  , I3_GFM  )
        _write_1D('H12_GFM' , H12_GFM )
        _write_1D('H32_GFM' , H32_GFM )
    
    self.get_header(verbose=False)
    if verbose: print(72*'-')
    if verbose: print('total time : ztmd.calc_comp_trafo() : %s'%format_time_string((timeit.default_timer() - t_start_func)))
    if verbose: print(72*'-')
    return
