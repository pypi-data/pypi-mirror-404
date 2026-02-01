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
"""
This script is used to calculate the minimum battery capacitance needed to operate the instrument for a full night.

To do this, we calculate the power consumption of the instrument and the power production
of the solar array for the same day and search for the latitude where the two are equal. We
repeat this for a set of dates and take the average of the power produced throughout the day.
The value should not change over time, but occur at different latitudes.
"""

import astropy.units as u
import click
import matplotlib.pyplot as plt
import numpy as np
from tqdm import tqdm

from ..config.config import PassConfig
from ..config.load_config import load_config
from ..general_framework.general_classes import Times
from ..power_consumption.power_consumption_classes import Instrument
from ..solar_production.solar_elevation_angle import get_lunar_elevation, get_solar_elevation
from ..visualization.plotting_funcs import plot_min_cap
from ..visualization.style import document_nw as doc


@click.command()
@click.argument("config_file")
def minimum_battery_cap(config_file: str):
    """INCOMPLETE

    Args:
        config_file (str): _description_
    """
    config = load_config(config_file)

    # Load data from config file
    instrument = config.instrument

    if isinstance(instrument, list):
        for instr in instrument:
            calc_min_capacitance(config, instr)
    else:
        calc_min_capacitance(config, instrument)


def calc_min_capacitance(config: PassConfig, instrument: Instrument):
    """Calculate the minimum battery capacitance for a given instrument configuration.

    Iterates through latitude and date ranges to find conditions where power
    production and consumption are balanced, then calculates the required
    battery capacity to sustain operations through the night.

    Args:
        config (PassConfig): The PASS configuration object containing latitude
            range, date range, and solar power system settings.
        instrument (Instrument): The instrument configuration for power
            consumption calculations.
    """
    # Define data arrays
    minimum_capacitance = []
    cap_lat = []
    cap_day = []
    cap_day_hours = []

    # Loop through latitudes and dates
    for j in tqdm(range(len(config.latitude_range.latitude_range))):

        lat = config.latitude_range.latitude_range[j]

        for i, date in enumerate(config.date_range.date_range):

            # Create a new date and time range for a single day
            new_date = date.strftime("%Y-%m-%d")
            day_range = Times(new_date, frequency=5 * u.min)
            limb = lat.get_limb()

            # Get the solar and lunar elevation angles for the given day
            solar_elevation_angle = get_solar_elevation(day_range.times, lat)
            lunar_elevation_angle = get_lunar_elevation(day_range.times, lat)

            # Calculate the number of hours for any given day for the case of least power production
            single_day_hours = np.sum(np.where(solar_elevation_angle > lat.get_limb(), day_range.frequency, 0))

            # Calculate the power consumption and production for the given day
            power_consumption = 0
            for k, angle in enumerate(solar_elevation_angle):
                power_consumption = power_consumption + (
                    instrument.get_power_consumption(solar_elevation_angle[k], lunar_elevation_angle[k], limb)
                    * 24
                    * u.h
                )

            power_production = (
                config.solar_power_system.get_power_production(solar_elevation_angle, limb) * day_range.frequency
            )

            # calculate the difference between the power consumption and production
            daily_calc = (np.sum(power_consumption) - np.sum(power_production)).to(u.W * u.h)

            if np.abs(daily_calc) < config.min_battery_cap.set_cap_range * u.W * u.h:
                stored_power = np.cumsum(power_production - power_consumption)
                minimum_capacitance.append(np.max(stored_power.to(u.W * u.h).value))
                cap_day.append(date)
                cap_lat.append(lat.latitude.to(u.deg).value)
                cap_day_hours.append(single_day_hours.to(u.h).value)

    if len(minimum_capacitance) == 0:
        print(
            "Your Set Cap Range is too small.  Your net power production does not get within that value. Try setting it to a larger number in the config file. "
        )
    else:

        print(f"Your Minimum Capacitance is : {np.mean(minimum_capacitance) / 1000} kWh")
        print(
            f"The fewest daylight charging hours needed to still operate for a full night is {np.mean(cap_day_hours)} hours"
        )

        colors = minimum_capacitance / np.max(minimum_capacitance)
        fig, ax = doc.figure(1, 1)
        color_bar_label = "Capacitance in kWh"
        plot_min_cap(fig, ax, cap_day, cap_lat, colors, color_bar_label, 22)
        plt.setp(ax.get_xticklabels(), rotation=20, ha="right", rotation_mode="anchor")

        plt.show()
