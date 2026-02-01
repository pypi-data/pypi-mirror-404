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


import sys
from pathlib import Path

import click
import matplotlib.pyplot as plt
import numpy as np
from astropy import units as u
from tqdm import tqdm

from PASS.config.config import PassConfig
from PASS.config.load_config import load_config

from ..general_framework.general_classes import LatitudeRange, SimpleLocation, Times
from ..power_consumption.power_consumption_classes import Instrument
from ..solar_production.solar_elevation_angle import get_lunar_elevation, get_solar_elevation
from ..visualization.plotting_funcs import plot_contour
from ..visualization.style import document_nw as doc


@click.command()
@click.argument("config_file")
def power_consumption(config_file: str):
    """Calculate power consumption for a given instrument and battery bank over a set date range.

    Args:
        config_file (str): The path to the configuration file.
    """

    print("Loading config file.")
    # Define coordinates of the detector
    config = load_config(config_file)

    lat_range = config.latitude_range
    date_range = config.date_range
    instrument = config.instrument

    power_consumption = np.zeros((len(lat_range), len(date_range)), dtype=float)

    print("Calculating power consumptions for date and latitude ranges.")
    for j in tqdm(range(len(lat_range.latitude_range))):

        lat = lat_range.latitude_range[j]

        for i, date in enumerate(date_range.date_range):
            new_date = date.strftime("%Y-%m-%d")
            day_range = Times(start_time=new_date, frequency=20 * u.min)

            solar_elevation_angle = get_solar_elevation(day_range.times, lat)

            lunar_elevation_angle = get_lunar_elevation(day_range.times, lat)

            loadshedding = np.zeros_like(solar_elevation_angle.value, dtype=bool)
            limb = lat.get_limb()

            day_power = instrument.get_power_consumption_array(
                solar_elevation_angle, lunar_elevation_angle, loadshedding, limb
            )
            power_consumption[j, i] = ((np.sum(day_power) * 20 * u.min).to(u.W * u.h).value) / 1000

    print("Generating power conumption plot.")

    fig, ax = doc.figure(1, 1)
    plot_contour(
        fig,
        ax,
        date_range.date_range,
        lat_range.latitudes.to(u.deg).value,
        power_consumption,
        color_bar_label="Power Consumption in kWh",
    )
    ax.set_xlabel("Date Range in UTC")
    ax.set_ylabel("Latitudes in Deg")
    y_ticks = np.arange(lat_range.latitude_start.to_value(), lat_range.latitude_end.to_value() + 1, 10)

    ax.set_yticks(y_ticks, minor=False)
    plt.setp(ax.get_xticklabels(), rotation=20, ha="right", rotation_mode="anchor")
    plt.savefig(Path(config.plots.power_consumption))
    # plt.show()
    print("Power consumption plot generated.")
