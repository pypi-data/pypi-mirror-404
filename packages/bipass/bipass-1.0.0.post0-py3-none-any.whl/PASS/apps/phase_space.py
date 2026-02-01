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

import astropy.units as u
import click
import matplotlib.pyplot as plt
import numpy as np
from tqdm import tqdm

from ..config.load_config import load_config
from ..general_framework.general_classes import Times
from ..solar_production.solar_elevation_angle import get_lunar_elevation, get_solar_elevation
from ..visualization.plotting_funcs import plot_contour_phase_space
from ..visualization.style import document as doc


@click.command()
@click.argument("config_file")
def phase_space(config_file: str) -> None:
    """Phase space of the amount of day, night, and astronomical night over a range of latitudes and dates.

    Args:
        config_file (str): The path to the configuration file.
    """

    print("Loading Config File.")
    config = load_config(config_file)

    latitudes = config.latitude_range
    times = config.date_range
    day_freq = u.Quantity(config.date_range.frequency)

    # Define arrays to hold the data
    day_time = np.zeros((len(latitudes), len(times)), dtype=float)
    astro_time = np.zeros((len(latitudes), len(times)), dtype=float)
    night_time = np.zeros((len(latitudes), len(times)), dtype=float)

    print("Generating day and astronomical hours.")

    for j in tqdm(range(len(latitudes.latitude_range))):
        loc = latitudes.latitude_range[j]
        limb = loc.get_limb()
        for i, date in enumerate(times.times):

            # Get the solar and lunar elevation angles
            day_times = Times(start_time=date, frequency=day_freq)
            solar_elevation_angle = get_solar_elevation(day_times.times, loc)
            lunar_elevation_angle = get_lunar_elevation(day_times.times, loc)

            # Determine the amount of day, night, and astronomical night
            night = np.sum(np.where(solar_elevation_angle < limb, 1, 0))
            day = np.sum(np.where(solar_elevation_angle > limb, 1, 0))
            astro = np.sum(
                np.where(
                    np.logical_and(solar_elevation_angle < limb, lunar_elevation_angle < limb),
                    1,
                    0,
                )
            )

            # Save number of hours of day, night, and astronomical night
            day_time[j][i] = (day * day_freq).to("hour").value
            night_time[j][i] = (night * day_freq).to("hour").value
            astro_time[j][i] = (astro * day_freq).to("hour").value

    print("Making Phase-Space plots.")
    # Plot the data
    fig, ax = doc.figure(2, 1)
    levels = np.linspace(0, 24, 100)
    ticks = np.round((np.linspace(0, 24, 5, endpoint=True)), 1)

    # Plot amount of daytime
    plot_contour_phase_space(
        fig,
        ax[0],
        times.date_range,
        latitudes.latitudes.value,
        day_time,
        color_bar_label="Hours of Daylight",
        fontsize=10,
        levels=levels,
        ticks=ticks,
    )
    ax[0].set_ylabel("Latitudes in Degrees", fontsize=10)
    ax[0].tick_params(labelbottom=False)

    y_ticks = np.arange(latitudes.latitude_start.to_value(), latitudes.latitude_end.to_value() + 1, 10)

    ax[0].set_yticks(y_ticks, minor=False)

    # Plot amount of astronomical night
    plot_contour_phase_space(
        fig,
        ax[1],
        times.date_range,
        latitudes.latitudes.value,
        astro_time,
        color_bar_label="Hours of Moonless Astronomical night",
        fontsize=10,
        levels=levels,
        ticks=ticks,
    )
    ax[1].set_xlabel("Datetime in UTC", fontsize=10)
    ax[1].set_ylabel("Latitudes in Degrees", fontsize=10)
    ax[1].set_yticks(y_ticks, minor=False)

    # Plot configuration and save
    plt.setp(ax[1].get_xticklabels(), rotation=20, ha="right", rotation_mode="anchor")
    plt.tight_layout()
    plot_path = Path(config.plots.day_night_time_plot)

    plt.savefig(plot_path)
    print("Phase space plots generated.")
    # plt.show()


if __name__ == "__main__":
    config = load_config(sys.argv[1])
    phase_space(config)
