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


from pathlib import Path

import click
import matplotlib.pyplot as plt
import numpy as np
from astropy import units as U
from mpl_toolkits.axes_grid1 import make_axes_locatable
from tqdm import tqdm

from PASS.solar_production.solar_elevation_angle import get_lunar_elevation, get_solar_elevation

from ..config.config import PassConfig
from ..config.load_config import load_config
from ..general_framework.general_classes import LatitudeRange, SimpleLocation, Times
from ..power_consumption.power_consumption_classes import BatteryBank, Instrument
from ..solar_production.solar_production_classes import SolarArray, SolarSkirt
from ..visualization.style import document as doc


@click.command()
@click.argument("config_file")
def net_power_production(config_file: str):
    """BROKEN This function generates the net power production for a given payload configuration over a set range of latitudes and dates.  The latitudes, dates, and payload config are set in the config file.

    Args:
        config_file (str): The path to the configuration file.
    """
    # Load config file
    config = load_config(config_file)
    date_range = config.date_range
    plot_path = Path(config.plots.plot_directory)

    # Define coordinates of the detector

    lat_range = config.latitude_range
    date_range = config.date_range

    net_power_produciton_daylight = np.zeros((len(lat_range), len(date_range)))
    net_power_production = np.zeros((len(lat_range), len(date_range)))

    # def an instrument:

    instrument_obs = config.instrument

    daytime_power_consumption = config.instrument.daytime_power_consumption

    instrument_daylight = Instrument(
        nighttime_power_consumption=daytime_power_consumption,
        observation_power_consumption=daytime_power_consumption,
        daytime_power_consumption=daytime_power_consumption,
        survival_power_consumption=daytime_power_consumption,
        loadshedding_flag=False,
    )

    # def a solar array:
    solar_array = config.solar_power_system

    for j in tqdm(range(len(lat_range.latitude_range))):

        lat = lat_range.latitude_range[j]
        for i, date in enumerate(date_range.date_range):
            new_date = date.strftime("%Y-%m-%d")
            day_range = Times(new_date, frequency=10 * U.min)

            for time in range(len(day_range.times)):

                solar_elevation_angle = get_solar_elevation(day_range.times[time], lat)
                lunar_elevation_angle = get_lunar_elevation(day_range.times[time], lat)
                loadshedding = np.zeros_like(solar_elevation_angle, dtype=bool)
                limb = lat.get_limb()

                # daily_power_consumption_day = instrument_daylight.get_power_consumption(
                #     solar_elevation_angle, lunar_elevation_angle, limb
                # )

                daily_power_consumption_obs = instrument_obs.get_power_consumption(
                    solar_elevation_angle,
                    lunar_elevation_angle,
                    limb,
                )

                daily_power_production = solar_array.get_power_production(solar_elevation_angle, limb) * 10 * U.min

                daily_power_production = np.where(
                    daily_power_production.to("W h") > config.battery_bank.starting_battery_capacity,
                    config.battery_bank.starting_battery_capacity,
                    daily_power_production,
                )

                net_power_production[j, i] = (
                    daily_power_production.to_value() - daily_power_consumption_obs.to_value() / 1000
                )

                # print(net_power_production[j, i])

                # if (
                #     np.sum(daily_power_production) - np.sum(daily_power_consumption_day)
                #     > 0
                # ):
                #     net_power_produciton_daylight[j, i] = None
                # else:
                #     net_power_produciton_daylight[j, i] = -300

                # net_power_produciton_obs[j, i] = (
                #     daily_power_production.to_value()
                #     - daily_power_consumption_obs.to_value() / 1000
                # )

    fig, ax = doc.figure(1, 1)
    ax.set_ylabel("Latitude in Degrees")
    ax.set_xlabel("Date in UTC")

    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="5%", pad=0.05)

    cmap = plt.get_cmap("GnBu")
    cmap.set_under("orange")
    # cmap.set_over("red")

    im = ax.contourf(
        date_range.date_range,
        lat_range.latitudes,
        net_power_production,
        500,
        cmap=cmap,
    )
    cax.cla()
    cbar = fig.colorbar(
        im,
        cax=cax,
        orientation="vertical",
    )
    # cbar.set_ticks([-2, -1, 0, 1, 2, 3, 4, 5, 6, 7])
    cbar.set_label("Net Energy Production Capability in kWh")

    cmap2 = plt.get_cmap("GnBu")

    # cmap2.set_under("red")

    # im2 = ax.contourf(
    #     date_range.date_range,
    #     lat_range.latitudes,
    #     net_power_produciton_daylight,
    #     100,
    #     cmap=cmap2,
    # )

    # ax.grid(False)

    plt.setp(ax.get_xticklabels(), rotation=20, ha="right", rotation_mode="anchor")

    plt.savefig(config.plots.net_power)

    # plt.show()
