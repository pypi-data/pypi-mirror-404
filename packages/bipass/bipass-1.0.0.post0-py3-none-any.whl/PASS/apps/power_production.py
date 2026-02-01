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
"""Solar power production analysis for balloon payloads.

This module calculates and visualizes solar power production over the course
of a day for different latitudes, supporting both single solar arrays and
multi-panel solar skirt configurations.
"""

import sys
from pathlib import Path

import click
import matplotlib.pyplot as plt
from astropy import units as u

from ..config.load_config import load_config
from ..solar_production.solar_production_classes import SolarSkirt
from ..visualization.plotting_funcs import plot_power_produciton_many_lat_one_day
from ..visualization.style import document as doc


@click.command()
@click.argument("config_file")
def power_production(config_file: str):
    """Power production over the course of one day.

    Args:
        config_file (str): The path to the configuration file.
    """
    print("Loading config file.")
    config = load_config(config_file)
    date_range = config.date_range
    plot_path = Path(config.plots.plot_directory)
    increment = 1 * u.h
    print("Calculating power production values for the date and latitude ranges.")
    if isinstance(config.solar_power_system, SolarSkirt):
        fig, ax = doc.figure(1, 1)
        # ax.set_title("Total Skirt Power Production")

        plot_power_produciton_many_lat_one_day(
            config,
            date_range,
            config.solar_power_system,
            ax,
            fig,
            increment,
            label="Power in kWh",
        )
        plt.savefig(config.plots.power_production_total)
        for i, array in enumerate(config.solar_power_system.arrays):
            print(f"Processed Array {i+1}")
            fig, ax2 = doc.figure(1, 1)
            ax2.set_title(f"Solar Array {i+1} Power Production")
            plot_power_produciton_many_lat_one_day(
                config,
                date_range,
                array,
                ax2,
                fig,
                increment,
                label="Power in kWh",
            )
            plt.savefig(plot_path / f"array{i+1}_power_production.pdf")
    else:
        fig, ax = doc.figure(1, 1)
        # ax.set_title("Total Skirt Power Production")
        plot_power_produciton_many_lat_one_day(
            config,
            date_range,
            config.solar_power_system,
            ax,
            fig,
            increment,
            label="Power in kWh",
        )
        plt.savefig(config.plots.power_production_total)

    print("Power production plots generated.")

    # plt.show()


if __name__ == "__main__":
    config = load_config(sys.argv[1])
    power_production(config)
