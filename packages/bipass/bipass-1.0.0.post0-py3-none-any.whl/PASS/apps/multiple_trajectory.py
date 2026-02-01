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

"""This script is used to verify the performance of a power system configuration over many trajectories.
 These trajectories are developed using MERRA-2 wind data.  This script will keep track of any failures
 and the latitudes at which these failures occur. There are two types of failures: Level 1 failure and
 Level 2 fialure.  Level 1 failure means that the system moves into load shedding mode and cannot take
 data.  Level 2 failure means that the battery bank has run out of power and can no longer sustain the
 payload. In this case, the payload flight is terminated meaning that the duration of this flight may
 not be for the allocated 100 days of the trajectory.
 """


import copy
import os
from pathlib import Path

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


# This function is used to calculate the limb of the Earth at a given elevation.
def get_limb(elevation):
    """Generates the angle of the limb from horizontal at any given elevation.

    Args:
        elevation (float): Elevation of the balloon in meters

    Returns:
        float: returnts the angle of the limb in radians
    """
    return np.arcsin(R_earth / (R_earth + elevation)) - np.pi / 2 * u.rad


# This function uses the data generated to calculate the number of L1 failures as well as the number of hours we are in L1 failure mode.
# The data is pulled from the L1_falure_run.csv.  Which file you use is configurable in the config file.
def L1_analysis(l1_file, increment, l1_lats, hours_time_in_l1):
    """This function uses the data generated to calculate the number of L1 failures as well as the Latitudes in which we fail.
    The data is pulled from the L1_falure_run.csv.  Which file you use is configurable in the config file.

    Args:
        l1_file (string): L2_failures.csv file.  Should be found in the run folder.
        increment (float): time increment of the trajectories.  This is a configurable quantity in the config file
        l1_lats (np array): All of the L2 fialure latitudes.  Generated when running the main.
        hours_time_in_l1 (np array): Total hours of a specific flight for which the payload is in L1 mode.
    Returns:
        array: hours_in_L1,
        array: hours_of_obs_in_l1,
        array: l1_lats,
        array: hours_per_flight
    """

    l1_data = pd.read_csv(
        f"{l1_file}",
        header=2,
        names=["failure_type", "time", "lat", "long", "state", "traj_file"],
    )

    length = len(l1_data["failure_type"])

    # Calculate the time increments
    hours_in_L1 = length * increment
    obs_in_l1 = []

    # Run a loop over the number of entries in the L1_failures_run.csv
    for i in range(len(l1_data["state"])):
        state = l1_data["state"][i]

        # This generates the time steps between each entry in the L1_failures.csv
        if i > 0:
            if Time(l1_data["time"][i - 1], format="isot") == Time(l1_data["time"][i], format="isot") - increment:
                l1_lats.append(l1_data["lat"][i])
        # Takes care of the first entry
        else:
            l1_lats.append(l1_data["lat"][i])
        # Tracks all the possible operation hours missed because we are in L1 mode
        if state == "Operation":
            obs_in_l1.append(1)

    # Calculate the total number of operational hours missed in L1 mode
    hours_of_obs_in_l1 = 0
    hours_of_obs_in_l1 = np.sum(obs_in_l1) * increment

    # Convert to values
    hours_per_flight = [hours_time_in_l1[0].to("h").value]

    # Caclulate the total number of hours in L1 per a single flight
    for i in range(len(hours_time_in_l1) - 1):
        hours_per_flight.append((hours_time_in_l1[i + 1] - hours_time_in_l1[i]).to("h").value)

    return hours_in_L1, hours_of_obs_in_l1, l1_lats, hours_per_flight


def L2_analysis(l2_file, increment, l2_lats, hours_per_flight_l2):
    """This function uses the data generated to calculate the number of L2 failures as well as the Latitudes in which we fail.
    The data is pulled from the L2_falure_run.csv.  Which file you use is configurable in the config file.

    Args:
        l2_file (_type_): L2_failures.csv file.  Should be found in the run folder.
        increment (_type_): time increment of the trajectories.  This is a configurable quantity in the config file
        l2_lats (_type_): All of the L2 fialure latitudes.  Generated when running the main.
        hours_per_flight_l2 (_type_): Total hours of a specific flight (could be different depending on when an L2 failure occurs)

    Returns:
        array: hours_in_L2,
        array: hours_of_obs_in_l2,
        array: l2_lats,
        array: hours_per_flight_l2
    """
    # Read in the L2_failures file
    try:
        l2_data = pd.read_csv(
            f"{l2_file}",
            header=1,
            names=["failure_type", "time", "lat", "long", "state", "traj_file"],
        )

    # If no L2 failures were found and the file is empty
    except pd.errors.ParserError:
        print("No L1 Failures")

        return 0 * u.h, 0 * u.h, [], []

    # Length of the file
    length = len(l2_data["failure_type"])

    # Time increment for the flight
    hours_in_L2 = length * increment
    obs_in_l2 = []

    # Find Lat and state of L2 failures
    for i in range(len(l2_data["state"])):
        state = l2_data["state"][i]
        l2_lats.append(l2_data["lat"][i])

        if state == "Operation":
            obs_in_l2.append(1)

    for k in range(len(hours_per_flight_l2)):
        hours_per_flight_l2[k] = ((hours_per_flight_l2[k]) * increment).to("day").value

    hours_of_obs_in_l2 = np.sum(obs_in_l2) * increment

    return hours_in_L2, hours_of_obs_in_l2, l2_lats, hours_per_flight_l2


@click.command()
@click.argument("config_file")
def multiple_traj(config_file: str) -> None:
    """Power system performance over multiple simulated trajectories.

    Args:
        config_file (str): The path to the configuration file.
    """
    # Ensure bundled trajectory data is extracted
    ensure_trajectories_extracted()

    print("Loading config file.")
    config = load_config(config_file)
    status = config.status

    names = ["datetime", "lat", "long", "alt", "Ewind", "Nwind"]

    # Use bundled trajectories if path is "bundled"
    traj_path = config.multiple_traj["trajectory_path"]
    if traj_path == "bundled":
        path = get_trajectories_path()
    else:
        path = Path(traj_path)

    plot_path = Path(config.plots.multiple_trajectory)

    traj_list = os.listdir(path)
    traj_list = np.sort(traj_list)

    # Limit number of trajectories if specified
    n_trajectories = config.multiple_traj.get("n_trajectories", 0)
    if n_trajectories > 0:
        n_trajectories = min(n_trajectories, len(traj_list))
        traj_list = traj_list[:n_trajectories]
        print(f"Processing {n_trajectories} trajectories.")
    lat_L2_failures = []
    lat_L1_failures = []
    hours_time_in_L1 = []
    hours_per_flight_l1 = []
    hours_per_flight_l2 = []

    traj_limit = u.Quantity(config.multiple_traj["trajectory_length"])

    traj_limit = traj_limit.to("hour")
    traj_limit = traj_limit * 2

    print("Loading trajectories.")

    for k in tqdm(range(len(traj_list))):
        battery_bank = copy.deepcopy(config.battery_bank)

        if not traj_list[k].endswith(".csv"):
            continue

        sim_traj = pd.read_csv(f"{path}/{traj_list[k]}", header=9, names=names)

        times = Time(pd.to_datetime(sim_traj["datetime"]))
        incriment = (times[1] - times[0]).to("h")

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
        index = 0
        for i, date in enumerate(times):
            index += 1
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
                battery_bank=battery_bank,
                trajectory_file=traj_list[k],
            )

            if battery_bank.soc == 0:

                hours_time_in_L1.append(status.get_time_in_L1(incriment))

                break

            if i > traj_limit.to_value():
                break

        hours_per_flight_l2.append(index)

        hours_time_in_L1.append(status.get_time_in_L1(incriment))
    print("Performing analysis.")
    status.write_states()
    incriment = 0.5 * u.h
    l1_file = config.status.l1file
    l2_file = config.status.l2file
    sys_file = config.status.sysfile

    # Initialize with defaults in case analysis fails
    total_hours_in_L1 = 0 * u.h
    total_hours_of_obs_in_l1 = 0 * u.h
    total_hours_in_L2 = 0 * u.h
    total_hours_of_obs_in_l2 = 0 * u.h

    try:

        (
            total_hours_in_L1,
            total_hours_of_obs_in_l1,
            lat_L1_failures,
            hours_per_flight_l1,
        ) = L1_analysis(
            l1_file,
            incriment,
            lat_L1_failures,
            hours_time_in_L1,
        )
    except:
        print("No L1 failures.")

    try:
        (
            total_hours_in_L2,
            total_hours_of_obs_in_l2,
            lat_L2_failures,
            hours_per_flight_l2,
        ) = L2_analysis(
            l2_file,
            incriment,
            lat_L2_failures,
            hours_per_flight_l2,
        )
    except:
        print("No L2 failures.")

    # obs_hours_in_L1.append(total_hours_of_obs_in_l1.to("h").value)
    # hours_in_l1_mode.append(total_hours_in_L1.to("h").value)

    # obs_hours_in_L2.append(total_hours_of_obs_in_l2.to("h").value)
    # hours_in_l2_mode.append(total_hours_in_L2.to("h").value)

    # if total_hours_in_L1 > 0:
    #     if total_hours_in_L2 > 0:

    fig, ax = plt.subplots(2, 2, figsize=(12, 8))
    bins = 35

    # L1 failure statistics (handle empty arrays)
    if len(hours_per_flight_l1) > 0:
        ax0_avg = np.mean(hours_per_flight_l1)
        ax0_std = np.std(hours_per_flight_l1)
    else:
        ax0_avg = 0
        ax0_std = 0
    ax1_std = np.std(total_hours_of_obs_in_l1) if total_hours_of_obs_in_l1 != 0 else 0

    if len(lat_L1_failures) > 0:
        ax2_avg = np.mean(lat_L1_failures)
        ax2_std = np.std(lat_L1_failures)
        ax2_max = np.max(lat_L1_failures)
    else:
        ax2_avg = 0
        ax2_std = 0
        ax2_max = 0

    # L2 failure statistics (handle empty arrays)
    if len(lat_L2_failures) > 0:
        ax3_avg = np.mean(lat_L2_failures)
        ax3_std = np.std(lat_L2_failures)
        ax3_max = np.max(lat_L2_failures)
    else:
        ax3_avg = 0
        ax3_std = 0
        ax3_max = 0

    if len(hours_per_flight_l2) > 0:
        ax4_avg = np.mean(hours_per_flight_l2)
        ax4_std = np.std(hours_per_flight_l2)
    else:
        ax4_avg = 0
        ax4_std = 0

    print("Generating plots")

    ax[0][0].hist(
        hours_per_flight_l1,
        bins=bins,
        label=f"AVG: {ax0_avg:.3f}\nSTD: {ax0_std:.3f}\nTotal Obs Hours in L1: {total_hours_of_obs_in_l1:.1f}",
    )
    ax[0][0].set_title("Hours in L1 mode")

    ax[0][1].hist(
        lat_L1_failures,
        bins=bins,
        label=f"AVG: {ax2_avg:.3f}\nSTD: {ax2_std:.3f}\n MAX: {ax2_max:.3f}",
    )
    ax[0][1].set_title("Latitudes at L1 failures")

    ax[1][1].hist(
        lat_L2_failures,
        bins=10,
        label=f"AVG: {ax3_avg:.3f}\nSTD: {ax3_std:.3f}\n MAX: {ax3_max:.3f}",
    )
    ax[1][1].set_title("Latitudes at L2 failures")

    ax[1][0].hist(
        hours_per_flight_l2,
        bins=bins,
        label=f"AVG: {ax4_avg:.3f}\nSTD: {ax4_std:.3f}",
    )
    ax[1][0].set_title("Length of Flights (Days)")

    ax[0][0].legend()
    ax[0][1].legend()
    ax[1][0].legend()
    ax[1][1].legend()

    plt.tight_layout()

    plot_path = config.plots.multiple_trajectory

    plt.savefig(plot_path)
    # plt.show()
    # else:
    #     print("No L2 failures.")

    # else:
    #     print("No L1 failures.")


if __name__ == "__main__":
    multiple_traj()
