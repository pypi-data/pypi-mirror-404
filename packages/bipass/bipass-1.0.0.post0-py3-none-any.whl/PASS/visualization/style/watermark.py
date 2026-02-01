import astropy.time as t
import matplotlib.axes
from matplotlib.offsetbox import AnchoredText


def add_watermark(ax):
    text = rf"PASS v0.1 @ {t.Time.now().iso}"
    ax.annotate(
        text,
        xy=(0.0, 0.01),
        xycoords="axes fraction",
        alpha=0.4,
        fontsize="small",
        rotation=0,
        fontweight=550,
    )
