import matplotlib.pyplot as plt
import numpy as np

# ======================================================================

def fig_ax_grid(
            width_in=5.31,
            aspect_fig=3.0,
            sfac=1.0,
            nx=1,
            ny=1,
            ax_aspect=1.5,
            ax_x_in = 2.0,
            x1in=0.52,
            x2in=0.04,
            y1in=0.10,
            y2in=0.30,
            center_x=False,
            skip=None,
            dpi=150):
    '''
    Figure & Axis maker for grid of axes
    '''
    
    figsize = (width_in*sfac, width_in*sfac/aspect_fig)
    fig     = plt.figure(figsize=figsize, dpi=dpi/sfac)
    fig_x_in, fig_y_in = fig.get_size_inches()
    np.testing.assert_allclose(fig_x_in/fig_y_in, aspect_fig, rtol=1e-5)
    
    ## Scale by global scale factor
    x1in    *= sfac
    x2in    *= sfac
    y1in    *= sfac
    y2in    *= sfac
    ax_x_in *= sfac
    
    ax_y_in = ax_x_in/ax_aspect
    
    ## Make axes
    axs = []
    axi = 0
    for j in range(ny):
        for i in range(nx):
            axi += 1
            if center_x:
                ws_x_in = fig_x_in - nx*ax_x_in ## Total [x] whitespace [in]
                x0 = ( (i+1)*(ws_x_in/(nx+1)) + i*ax_x_in ) / fig_x_in
            else:
                x0 = x1in/fig_x_in + i*(1/nx) - i*x2in/fig_x_in
            y0 = ( fig_y_in - (j+1)*ax_y_in - (j+1)*y1in - j*y2in ) / fig_y_in
            dx = ax_x_in/fig_x_in
            dy = ax_y_in/fig_y_in
            if skip is None or axi not in skip:
                axs.append( fig.add_axes([x0,y0,dx,dy]) )
    
    return fig,axs
