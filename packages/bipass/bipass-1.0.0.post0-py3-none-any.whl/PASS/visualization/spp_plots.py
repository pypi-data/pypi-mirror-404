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
from matplotlib import animation
from mpl_toolkits.axes_grid1 import make_axes_locatable

from ..general_framework.general_classes import DateRange, LatitudeRange, SimpleLocation
from ..solar_production.solar_elevation_angle import get_solar_elevation
from ..solar_production.solar_production_classes import SolarArray


def plot_const_lat_many_days(
    coords: SimpleLocation,
    dates: DateRange,
    solar_array: SolarArray,
    ax,
    *args,
    **kwargs,
) -> None:
    """Function to create a plot of the solar power production for a
    constant location over the course of several days

    Args:
        coords (SimpleLocation): Coordinates of the detector
        dates (DateRange): Range of dates to run the simulation for
        solar_array (SolarArray): Properties of the solar array
    """
    # Calculate the solar elevation angle over the whole input range
    solar_elevation_angles = np.zeros(len(dates))
    for count, date in enumerate(dates.date_range):
        solar_elevation_angles[count] = get_solar_elevation(date, coords)

    # Calculate the power production
    power_production = solar_array.get_power_production(solar_elevation_angles)

    # Create plot

    ax.set_title(
        f"Power production over {dates.start_date.strftime('%Y-%m-%d')} & {dates.end_date.strftime('%Y-%m-%d')}"
    )
    ax.set_xlabel("Date")
    ax.set_ylabel("Power in Watts")
    ax.plot(dates.date_range, power_production, **kwargs)
    plt.setp(ax.get_xticklabels(), rotation=20, ha="right", rotation_mode="anchor")
    plt.tight_layout()
