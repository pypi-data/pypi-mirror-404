# The Clear BSD License
#
# Copyright (c) 2024 Julia Burton
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted (subject to the limitations in the disclaimer
# below) provided that the following conditions are met:
#
#      * Redistributions of source code must retain the above copyright notice,
#      this list of conditions and the following disclaimer.
#
#      * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.
#
#      * Neither the name of the copyright holder nor the names of its
#      contributors may be used to endorse or promote products derived from this
#      software without specific prior written permission.
#
# NO EXPRESS OR IMPLIED LICENSES TO ANY PARTY'S PATENT RIGHTS ARE GRANTED BY
# THIS LICENSE. THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND
# CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
# IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.axes_grid1 import make_axes_locatable
from tqdm import tqdm

from ..general_framework.general_classes import DateRange, LatitudeRange, Location, SimpleLocation
from ..visualization.plotting_funcs import animate_contour
from .solar_elevation_angle import get_solar_elevation
from .solar_production_classes import SolarArray


def compare_opt_title_angle(solar_array, date_range, coordinates, tilt_range):
    total_power = np.zeros(len(tilt_range))

    for i in tqdm(range(len(tilt_range)), desc="Loading..."):
        solar_array.tilt_angle = tilt_range[i]

        # Calculate the solar elevation angle over the whole input range

        solar_elevation_angles = np.zeros(len(date_range))

        for count, date in enumerate(date_range.date_range):
            solar_elevation_angles[count] = get_solar_elevation(date, coordinates)

        # Calculate the power production
        power_production = solar_array.get_power_production(solar_elevation_angles)

        total_power[i] = solar_array.get_total_power_produciton(power_production)

    return total_power, tilt_range


def plot_optimal(total_power, tilt_range, coordinates, date_range, ax, *args, **kwargs):
    optimal_tilt = tilt_range[np.argmax(total_power)]
    sub_optimal_tilt = tilt_range[np.argmin(total_power)]

    print(f"The optimal tilt is {optimal_tilt} with {np.amax(total_power)} \n")
    print(f"The least optimal tilt is {sub_optimal_tilt} with {np.amin(total_power)} \n")

    ax.set_title(
        f"Optimal tilt angle for over {date_range.start_date.strftime('%Y-%m-%d')}_{date_range.end_date.strftime('%Y-%m-%d')}"
    )
    ax.set_xlabel("Tilt of Panels in Degrees")
    ax.set_ylabel("Total Power in Watts")
    ax.plot(tilt_range, total_power, **kwargs)
    ax.scatter(optimal_tilt, np.amax(total_power), color="red")
    ax.annotate(
        f"{optimal_tilt,int(np.amax(total_power))}",
        (optimal_tilt, np.amax(total_power)),
    )
    ax.scatter(sub_optimal_tilt, np.amin(total_power), color="red")
    ax.annotate(
        f"{sub_optimal_tilt,int(np.amin(total_power))}",
        (sub_optimal_tilt, np.amin(total_power)),
    )


def compare_opt_title_angle_many_lat(
    solar_array,
    date_range,
    coordinates,
    tilt_range,
):
    total_power = np.zeros(len(tilt_range))

    for i in range(len(tilt_range)):
        solar_array.tilt_angle = tilt_range[i]

        # Calculate the solar elevation angle over the whole input range

        solar_elevation_angles = np.zeros(len(date_range))

        for count, date in enumerate(date_range.date_range):
            solar_elevation_angles[count] = get_solar_elevation(date, coordinates)

        # Calculate the power production
        power_production = solar_array.get_power_production(solar_elevation_angles)

        total_power[i] = solar_array.get_total_power_produciton(power_production)

    return total_power, tilt_range
