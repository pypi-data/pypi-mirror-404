import pathlib

import matplotlib as mpl
import matplotlib.pyplot as plt


def figure(rows, cols, **fig_kwargs):
    local_path = pathlib.Path(__file__).parent.resolve()
    style = str(local_path) + "/styles/document.mplstyle"
    mpl.rcParams.update(mpl.rcParamsDefault)
    mpl.style.use(style)

    ## create figure with some arguments
    return plt.subplots(rows, cols, **fig_kwargs)
