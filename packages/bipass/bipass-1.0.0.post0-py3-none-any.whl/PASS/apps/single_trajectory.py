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
"""Single trajectory power system simulation.

This module simulates power system performance along a single balloon flight
trajectory, calculating net power, battery state of charge, and identifying
potential power deficits.
"""

import astropy.coordinates as coord
import astropy.units as u
import click
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from astropy.constants import R_earth
from astropy.time import Time
from tqdm import tqdm

from ..config.load_config import load_config
from ..data import ensure_trajectories_extracted, get_trajectories_path
from ..general_framework.general_classes import SimpleLocation
from ..general_framework.power_system_capacitance import generate_battery_bank_capacitance
from ..solar_production.solar_elevation_angle import get_lunar_elevation, get_solar_elevation
from ..visualization.style import document_nw as doc


def get_limb(elevation):
    """Calculate the angle to the Earth's limb from a given elevation.

    Args:
        elevation (astropy.units.Quantity): Altitude above Earth's surface.

    Returns:
        astropy.units.Quantity: Angle to the limb below horizontal in radians.
    """
    return np.arcsin(R_earth / (R_earth + elevation)) - np.pi / 2 * u.rad


@click.command()
@click.argument("config_file")
def single_traj(config_file: str) -> None:
    """Power system performance on a single trajectory.

    Args:
        config_file (str): The path to the configuration file.
    """
    # Ensure bundled trajectory data is extracted
    ensure_trajectories_extracted()

    config = load_config(config_file)
    status = config.status
    battery_bank = config.battery_bank

    names = ["datetime", "lat", "long", "alt", "Ewind", "Nwind"]
    path = config.single_traj["trajectory_path"]
    file_name = config.single_traj["trajectory_file_name"]

    # Use bundled trajectories if path is "bundled"
    if path == "bundled":
        path = get_trajectories_path()

    print(f"Loading trajectory file {file_name}...")
    sim_traj = pd.read_csv(f"{path}/{file_name}", names=names, header=9)

    battery_bank_caps = []
    state_of_charges = []
    net_powers = []
    power_consumptions = []
    power_productions = []

    times = Time(pd.to_datetime(sim_traj["datetime"]))
    incriment = (times[1] - times[0]).to("hour")

    locations = coord.EarthLocation(
        lat=sim_traj["lat"] * u.deg,
        lon=sim_traj["long"] * u.deg,
        height=sim_traj["alt"] * u.m,
    )

    detector_frames = coord.AltAz(obstime=times, location=locations)

    # Get the solar elevation for the new date:
    solar_elevation = get_solar_elevation(
        times,
        locations,
        detector_frames,
    )

    # Get the lunar elevation:
    lunar_elevation = get_lunar_elevation(times, locations, detector_frames)

    limb = get_limb(sim_traj["alt"].to_numpy() * u.m).to("deg")

    # Get the power production for this day and time:
    solar_array = config.solar_power_system
    power_production = solar_array.get_power_production(solar_elevation, limb)

    for i in tqdm(range(len(times))):

        date = times[i]
        (
            net_power,
            _,
            power_consumption,
        ) = generate_battery_bank_capacitance(
            config,
            date,
            incriment,
            locations[i],
            angles=[solar_elevation[i], lunar_elevation[i], limb[i]],
            power_production=power_production[i],
        )

        battery_bank_caps.append(battery_bank.capacitance)
        state_of_charges.append(battery_bank.soc)
        net_powers.append(net_power.to_value())
        power_consumptions.append(-(power_consumption).to("W h").value)

    # status.write_states()
    times = times.to_datetime()
    fig, ax = doc.figure(2, 1)
    loadshedding = config.status.loadshedding_SoC

    ax[0].plot(times, net_powers, color="blue")
    # ax[0].plot(times, power_production, color="orange")

    ax[1].plot(times, state_of_charges, color="green")
    ax[1].axhline(loadshedding, color="red", label="loadshedding mode")
    ax[1].legend()

    ax[0].set_ylabel("Net Power Production in W")
    ax[1].set_ylabel("State of Charge %")

    plt.setp(ax[0].get_xticklabels(), rotation=20, ha="right", rotation_mode="anchor")

    plt.setp(ax[1].get_xticklabels(), rotation=20, ha="right", rotation_mode="anchor")

    plt.savefig(config.plots.single_trajectory)

    # plt.show()


if __name__ == "__main__":
    single_traj()
