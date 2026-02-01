import numpy as np

'''
========================================================================
Utilities
========================================================================
'''

# ======================================================================

def even_print(label, output, **kwargs):
    '''
    print/return a fixed width message
    '''
    terminal_width = kwargs.get('terminal_width',72)
    s              = kwargs.get('s',False) ## return string
    
    ndots = (terminal_width-2) - len(label) - len(output)
    text = label+' '+ndots*'.'+' '+output
    if s:
        return text
    else:
        #sys.stdout.write(text)
        print(text)
        return

def format_time_string(tsec):
    '''
    format seconds as dd:hh:mm:ss
    '''
    m, s = divmod(abs(int(round(tsec))),60)
    h, m = divmod(m,60)
    d, h = divmod(h,24)
    d    = int(round(d))
    h    = int(round(h))
    m    = int(round(m))
    s    = int(round(s))
    if (d==0) and (h==0) and (m==0):
        s_out = f'{s:d}s'
    elif (d==0) and (h==0):
        s_out = f'{m:d}m:{s:02d}s'
    elif (d==0):
        s_out = f'{h:d}h:{m:02d}m:{s:02d}s'
    else:
        s_out = f'{d:d}d:{h:02d}h:{m:02d}m:{s:02d}s'
    if (tsec >= 0):
        return s_out
    else:
        return f'-{s_out}'

def format_nbytes(size):
    '''
    format a number of bytes to [B],[KB],[MB],[GB],[TB]
    '''
    if not isinstance(size,(int,float)):
        raise ValueError('arg should be of type int or float')
    if (size<1024):
        size_fmt, size_unit = size, '[B]'
    elif (size>1024) and (size<=1024**2):
        size_fmt, size_unit = size/1024, '[KB]'
    elif (size>1024**2) and (size<=1024**3):
        size_fmt, size_unit = size/1024**2, '[MB]'
    elif (size>1024**3) and (size<=1024**4):
        size_fmt, size_unit = size/1024**3, '[GB]'
    else:
        size_fmt, size_unit = size/1024**4, '[TB]'
    return size_fmt, size_unit

def step(a,b,x,order=3):
    '''
    Polynomial step function
    https://en.wikipedia.org/wiki/Smoothstep
    '''
    x = (x-a)/(b-a)
    if (order==1):
        y = -2*x**3 + 3*x**2
    elif (order==2):
        y = 6*x**5 - 15*x**4 + 10*x**3
    elif (order==3):
        y = -20*x**7 + 70*x**6 - 84*x**5 + 35*x**4
    else:
        raise NotImplementedError
    y = np.clip(y,0.,1.)
    return y
