import os
import types

import h5py

# ======================================================================

def ztmd_loader(fn,names):
    '''
    Disk-to-RAM loader for ZTMD files
    - Return blank object with datasets attached
    -----
    - 0D & 1D datasets are always read
    - Coordinate datasets are always read
    - 2D datasets must be explicitly requested
    '''
    
    if not os.path.isfile(fn):
        raise FileNotFoundError(fn)
    
    obj = types.SimpleNamespace() ## blank object
    
    with h5py.File(fn,'r') as hf:
        
        ## 0D: Attach top-level attributes
        for k,v in hf.attrs.items():
            setattr(obj,k,v)
        
        ## 1D: Attach contents of group dims/
        if 'dims' in hf:
            for dsn in hf['dims']:
                ds = hf[f'dims/{dsn}']
                setattr(obj, dsn, ds[()])
        
        ## 1D: Attach contents of group data_1Dx/
        if 'data_1Dx' in hf:
            for dsn in hf['data_1Dx']:
                ds = hf[f'data_1Dx/{dsn}']
                setattr(obj, dsn, ds[()])
        
        ## 2D : Attach contents of group data/
        if 'data' in hf:
            for dsn in hf['data']:
                if dsn in names: ## only load if explicitly asked for
                    ds = hf[f'data/{dsn}']
                    setattr(obj, dsn, ds[()].T)
    
    return obj
