import pathlib

import matplotlib.pyplot as plt

from . import watermark

local_path = pathlib.Path(__file__).parent.resolve()

plt.style.use(str(local_path) + "/styles/presentation.mplstyle")
