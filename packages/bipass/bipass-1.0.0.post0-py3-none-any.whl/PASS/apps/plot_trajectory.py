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
"""Trajectory visualization for balloon flight paths.

This module provides tools to visualize balloon trajectory data on a Mollweide
projection map, showing the flight path with color-coded time progression.
"""

import click
import matplotlib.cm as cm
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from ..config.load_config import load_config


def plot_trajectory_plotting_func(trajectory, ax):
    """Plot a balloon trajectory on a matplotlib axes.

    Reads trajectory data from a CSV file and plots it with color-coded markers
    showing time progression, with distinct markers for start and end points.

    Args:
        trajectory (str): Path to the trajectory CSV file.
        ax (matplotlib.axes.Axes): Matplotlib axes object to plot on (should
            have Mollweide projection).
    """
    trajectory = pd.read_csv(trajectory, header=9, names=["time", "x", "y", "A", "E", "N"])

    trajectory_dates = pd.to_datetime(trajectory["time"])

    ax.grid(True)
    colors = cm.jet(np.linspace(0, 1, len(trajectory["time"])))
    ax.scatter(
        np.deg2rad(trajectory["y"].to_numpy()),
        np.deg2rad(trajectory["x"].to_numpy()),
        c=colors,
        marker=">",
        s=10,
    )
    ax.scatter(
        np.deg2rad(trajectory["y"].to_numpy())[0],
        np.deg2rad(trajectory["x"].to_numpy())[0],
        c=colors[0],
        marker="*",
        s=100,
        label="Start",
    )
    ax.scatter(
        np.deg2rad(trajectory["y"].to_numpy())[-1],
        np.deg2rad(trajectory["x"].to_numpy())[-1],
        c=colors[-1],
        marker="s",
        s=100,
        label="End",
    )
    ax.legend()


@click.command()
@click.argument("config_file")
def plot_trajectory(config_file: str) -> None:
    """Plot balloon trajectory on a Mollweide projection map.

    Args:
        config_file (str): The path to the configuration file.
    """

    print("Loading trajectory file.")
    config = load_config(config_file)

    fig = plt.figure()
    ax = fig.add_subplot(111, projection="mollweide")

    trajctory_file_name = config.single_traj["trajectory_path"] + "/" + config.single_traj["trajectory_file_name"]
    print("Making trajectory plot.")
    plot_trajectory_plotting_func(trajectory=trajctory_file_name, ax=ax)
    plt.tight_layout()
    plt.savefig(f"{config.single_traj["trajectory_file_name"]}.pdf")
    # plt.show()

    print("Trajectory plot created.")


if __name__ == "__main__":
    plot_trajectory()
