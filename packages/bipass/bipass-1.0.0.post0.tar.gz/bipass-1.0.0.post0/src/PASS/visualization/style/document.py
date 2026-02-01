import pathlib

import astropy.time as t
import matplotlib as mpl
import matplotlib.axes
import matplotlib.pyplot as plt
from matplotlib.offsetbox import AnchoredText

from . import watermark


def figure(rows, cols, **fig_kwargs):
    local_path = pathlib.Path(__file__).parent.resolve()
    style = str(local_path) + "/styles/document.mplstyle"
    mpl.rcParams.update(mpl.rcParamsDefault)
    mpl.style.use(style)

    ## create figure with some arguments
    fig, ax = plt.subplots(rows, cols, **fig_kwargs)

    ## I'm presuming that you may want to have subplots somewhere down the line;
    ## for the sake of consistency, I'm thus making sure that "ax" is always a dict:
    if rows == 1 and cols == 1:
        # ax = {0: ax}
        watermark.add_watermark(ax)

    else:
        for a in ax:
            watermark.add_watermark(a)

    return fig, ax
