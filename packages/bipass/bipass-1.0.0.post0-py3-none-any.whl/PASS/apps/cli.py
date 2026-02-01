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

import click

from . import (
    make_config,
    minimum_battery_capacitance,
    multiple_trajectory,
    net_power_production,
    optimal_tilt,
    phase_space,
    plot_trajectory,
    power_consumption,
    power_production,
    single_trajectory,
    traj_stats,
)


@click.group()
def cli():
    pass


cli.add_command(make_config.make_config)
cli.add_command(phase_space.phase_space)
cli.add_command(power_production.power_production)
cli.add_command(single_trajectory.single_traj)
cli.add_command(multiple_trajectory.multiple_traj)
cli.add_command(power_consumption.power_consumption)
cli.add_command(optimal_tilt.optimal_tilt)
cli.add_command(plot_trajectory.plot_trajectory)
cli.add_command(traj_stats.trajectory_stats)


# Needs fixing will push to release 2
# cli.add_command(minimum_battery_capacitance.minimum_battery_cap)
# cli.add_command(net_power_production.net_power_production)
