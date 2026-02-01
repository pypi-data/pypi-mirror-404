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

import astropy.units as u
import click
import matplotlib.pyplot as plt
import numpy as np
from astropy.coordinates import EarthLocation, SkyCoord
from astropy.time import Time
from tqdm import tqdm

from ..config.load_config import load_config

# from ..solar_production.solar_production_classes import SolarArray
from ..general_framework.general_classes import Times
from ..solar_production.solar_elevation_angle import get_solar_elevation
from ..visualization.style import document as doc


def plot_power_vs_tilt(tilt_range, total_power_production, optimal_tilt):
    figure, ax = plt.subplots()
    ax.plot(tilt_range.to(u.deg).value, total_power_production)
    ax.axvline(optimal_tilt, color="red", label=f"Optimal Tilt: {optimal_tilt}")
    ax.set_xlabel("Tilt Angle")
    ax.set_ylabel("Total Power Production")
    ax.legend()
    plt.show()


def get_optmal_tilt(date_range, location, solar_array, tilt_range):
    total_power_production = np.zeros(len(tilt_range), dtype=u.Quantity)
    solar_elevation_angles = get_solar_elevation(date_range.times, location)

    for i in range(len(tilt_range)):

        solar_array.set_tilt_angle(tilt_range[i])
        pp = solar_array.get_power_production(solar_elevation_angles, location.get_limb())
        total_power_production[i] = np.sum(pp)

    return tilt_range[np.argmax(total_power_production)]


@click.command()
@click.argument("config_file")
def optimal_tilt(config_file: str) -> None:
    """Calculates the optimal tilt angle for a solar array.

    Args:
        config_file (str): The path to the configuration file.
    """
    print("Loading config file.")
    config = load_config(config_file)
    # Define location
    locations = config.latitude_range

    # Define time

    daily_freq = u.Quantity(config.date_range.frequency)
    dates = Times(
        config.date_range.start_time,
        config.date_range.end_time,
        frequency=24 * u.h,
    )

    date_ranges = []
    for date in dates.times:
        date_ranges.append(Times(date.isot, frequency=daily_freq))

    # List of tilt angles
    start_angle = u.Quantity(config.optimal_tilt["min_tilt"])
    end_angle = u.Quantity(config.optimal_tilt["max_tilt"])
    inc_angle = u.Quantity(config.optimal_tilt["tilt_increment"])
    tilt_range = np.arange(start_angle, end_angle, inc_angle) * u.deg
    solar_array = config.solar_power_system
    print("Calculating optimal tilts.")
    lat_tilts = []
    for loc in tqdm(range(len(locations.latitude_range))):
        location = locations.latitude_range[loc]
        opt_tilts = []

        for k, date_range in enumerate(date_ranges):
            opt_tilts.append(
                get_optmal_tilt(
                    date_range,
                    location,
                    solar_array,
                    tilt_range,
                )
                .to(u.deg)
                .value
            )
        lat_tilts.append(opt_tilts)

    print("Generating optimal tilt plot.")
    fig, ax = doc.figure(1, 1)
    for i, location in enumerate(locations.latitude_range):
        ax.plot(
            dates.date_range,
            lat_tilts[i],
            label=f"Latitude: {location.latitude}",
        )
    ax.set_xlabel("Date")
    ax.set_ylabel("Optimal Tilt Angle in Degrees")
    ax.legend()
    plt.setp(ax.get_xticklabels(), rotation=20, ha="right", rotation_mode="anchor")
    plt.tight_layout()

    plot_path = config.plots.optimal_tilt
    plt.savefig(plot_path)
