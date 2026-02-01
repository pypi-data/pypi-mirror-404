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

# from ..config.load_config import load_config
from pathlib import Path

import click
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from tqdm import tqdm


def main():

    # print("Loading config file.")
    # config = load_config(config_file)
    # status = config.status
    l1_file = "/home/julia/Desktop/PASS/power-system-simulation-framework/run/status/l1_file_old.csv"
    l2_file = "/home/julia/Desktop/PASS/power-system-simulation-framework/run/status/l2_file_old.csv"

    l1_data = pd.read_csv(
        f"{l1_file}",
        header=2,
        names=["failure_type", "time", "lat", "long", "state", "traj_file"],
    )

    l2_data = pd.read_csv(
        f"{l2_file}",
        header=2,
        names=["failure_type", "time", "lat", "long", "state", "traj_file"],
    )

    l1_times = pd.to_datetime(l1_data["time"])
    l1_times_counts = l1_times.value_counts().sort_index()

    l2_times = pd.to_datetime(l2_data["time"])
    l2_times_counts = l2_times.value_counts().sort_index()

    fig = plt.figure(figsize=(8, 6))
    ax = fig.add_subplot(211)
    ax.plot(l1_times_counts.index, l1_times_counts.values, markersize=2)
    ax.set_ylabel("Number of L1 failures")
    ax.set_title("Number of L1 failures per Datetime")

    ax2 = fig.add_subplot(212)
    ax2.scatter(l2_times_counts.index, l2_times_counts.values, marker="x")
    ax2.set_yticks((0, 1, 2, 3))
    ax2.set_ylabel("Number of L2 failures")
    ax2.set_xlabel("Datetime in UTC")
    ax2.set_title("Number of L2 failures per Datetime")

    plt.setp(ax.get_xticklabels(), rotation=20, ha="right", rotation_mode="anchor")
    plt.setp(ax2.get_xticklabels(), rotation=20, ha="right", rotation_mode="anchor")
    plt.tight_layout()

    plt.savefig("/home/julia/Desktop/PASS/power-system-simulation-framework/run/plots/pass_failures_per_datetime.pdf")


if __name__ == "__main__":

    main()
