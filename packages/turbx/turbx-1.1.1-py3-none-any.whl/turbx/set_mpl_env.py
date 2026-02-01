import matplotlib as mpl

'''
========================================================================
matplotlib environment initializer
========================================================================
'''

# ======================================================================

def set_mpl_env(**kwargs):
    '''
    Set matplotlib global presets
    '''
    fontsize = kwargs.get('fontsize',9)
    usetex   = kwargs.get('usetex',True)
    sfac     = kwargs.get('sfac',1) ## global scale factor
    
    fontsize *= sfac ## scale font size by global scale factor
    axesAndTickWidth = 0.5*sfac
    
    mpl.rcParams['text.usetex'] = usetex
    
    if usetex:
        preamble_opts = [
                        r'\usepackage{amsmath}',
                        r'\usepackage{amssymb}',
                        r'\usepackage{gensymb}',
                        #r'\usepackage{graphicx}', ## not supported
                        r'\usepackage{newtxtext}', ## Times
                        r'\usepackage{newtxmath}', ## Times Math
                        r'\usepackage{xfrac}',
                        ]
        mpl.rcParams['text.latex.preamble'] = '\n'.join(preamble_opts)
        
        mpl.rcParams['font.family'] = 'serif'
        #mpl.rcParams['font.serif']  = 'Computer Modern Roman'
        mpl.rcParams['font.serif']  = 'Times'
    
    else:
        pass
    
    mpl.rcParams['xtick.major.size']  = 2.5*sfac
    mpl.rcParams['xtick.major.width'] = axesAndTickWidth
    mpl.rcParams['xtick.minor.size']  = 1.5*sfac
    mpl.rcParams['xtick.minor.width'] = axesAndTickWidth
    mpl.rcParams['xtick.direction']   = 'in'
    
    mpl.rcParams['ytick.major.size']  = 2.5*sfac
    mpl.rcParams['ytick.major.width'] = axesAndTickWidth
    mpl.rcParams['ytick.minor.size']  = 1.5*sfac
    mpl.rcParams['ytick.minor.width'] = axesAndTickWidth
    mpl.rcParams['ytick.direction']   = 'in'
    
    mpl.rcParams['xtick.labelsize'] = fontsize
    mpl.rcParams['ytick.labelsize'] = fontsize
    
    mpl.rcParams['xtick.major.pad'] = 3.0*sfac
    mpl.rcParams['xtick.minor.pad'] = 3.0*sfac
    mpl.rcParams['ytick.major.pad'] = 3.0*sfac
    mpl.rcParams['ytick.minor.pad'] = 3.0*sfac
    
    mpl.rcParams['lines.linewidth']       = 1.0
    mpl.rcParams['lines.linestyle']       = 'solid'
    mpl.rcParams['lines.marker']          = 'None' #'o'
    mpl.rcParams['lines.markersize']      = 1.2
    mpl.rcParams['lines.markeredgewidth'] = 0.
    
    mpl.rcParams['axes.linewidth'] = axesAndTickWidth
    mpl.rcParams['axes.labelpad']  = 2.0
    mpl.rcParams['axes.titlesize'] = fontsize
    mpl.rcParams['axes.labelsize'] = fontsize
    mpl.rcParams['axes.formatter.use_mathtext'] = True
    
    mpl.rcParams['legend.fontsize']      = fontsize
    mpl.rcParams['legend.shadow']        = False
    mpl.rcParams['legend.borderpad']     = 0.3
    mpl.rcParams['legend.framealpha']    = 1.0
    mpl.rcParams['legend.edgecolor']     = 'inherit'
    mpl.rcParams['legend.handlelength']  = 1.5
    mpl.rcParams['legend.handletextpad'] = 0.3
    mpl.rcParams['legend.borderaxespad'] = 0.7
    mpl.rcParams['legend.columnspacing'] = 0.5
    mpl.rcParams['legend.fancybox']      = False
    return
