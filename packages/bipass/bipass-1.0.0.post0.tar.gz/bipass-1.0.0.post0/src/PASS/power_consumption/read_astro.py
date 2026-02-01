import csv

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

j_night = pd.read_csv("nights.csv").to_numpy()

t_night = pd.read_csv("lat_vs_time.csv").to_numpy()

lat = np.arange(-80, 0, 1)[::-1]

diff = []

for i in range(len(j_night)):
    diff.append(t_night[i] - j_night[i])


fig = plt.figure()
ax = fig.add_subplot(111)
ax.plot(lat, diff)
plt.show()
