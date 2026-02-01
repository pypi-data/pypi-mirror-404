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


from dataclasses import dataclass
from pathlib import Path

from astropy.coordinates import EarthLocation
from astropy.time import Time

from ..power_consumption.power_consumption_classes import BatteryBank, Instrument


@dataclass
class State:
    name: str
    start_time: Time
    end_time: Time
    start_coords: EarthLocation
    end_coords: EarthLocation

    def get_duration(self):
        return self.end_time - self.start_time

    def __str__(self):
        return f"{self.name}, {self.start_time.isot}, {self.end_time.isot}, {self.get_duration().to('hour')}, {self.start_coords.lat.deg}, {self.start_coords.lon.deg}, {self.end_coords.lat.deg}, {self.end_coords.lon.deg}\n"


def update_state(new_state: State, state_list: State):
    if len(state_list) < 1:
        state_list.append(new_state)
    last_state = state_list[-1]
    if new_state.name == last_state.name:
        last_state.end_time = new_state.start_time
        last_state.end_coords = new_state.start_coords
    else:
        state_list.append(new_state)


@dataclass
class Failures:
    name: str
    time: Time
    coords: EarthLocation
    state: State
    trajectory: str

    def __str__(self):
        return f"{self.name},{self.time.isot},{self.coords.lat.deg},{self.coords.lon.deg},{self.state.name},{self.trajectory}\n"


class Status:
    def __init__(
        self,
        sys_file: str = None,
        l1_file: str = None,
        l2_file: str = None,
        loadshedding_SoC: float = 0.3,
    ) -> None:
        self.sysfile = sys_file
        self.l1file = l1_file
        self.l2file = l2_file
        self.loadshedding_SoC = loadshedding_SoC
        self.system_states = []
        self.l1_failure = []
        self.l2_failure = []

    def get_time_in_L1(self, increment):
        return len(self.l1_failure) * increment

    def update_sys(
        self,
        time: Time,
        location: EarthLocation,
        solar_elevation_angle: float,
        lunar_elevation_angle: float,
        limb: float,
    ):
        if solar_elevation_angle < limb:
            if lunar_elevation_angle < limb:
                new_state = State("Operation", time, time, location, location)
                update_state(new_state, self.system_states)
            else:
                new_state = State("Night", time, time, location, location)
                update_state(new_state, self.system_states)
        else:
            new_state = State("Day", time, time, location, location)
            update_state(new_state, self.system_states)

    def update_fail(
        self, time: Time, location: EarthLocation, battery: BatteryBank, instrument: Instrument, trajectory: str
    ):
        soc = battery.get_soc()
        if soc < self.loadshedding_SoC:
            new_state = Failures("L1-FAILURE", time, location, self.system_states[-1], trajectory)
            self.l1_failure.append(new_state)
            instrument.loadshedding_flag = True
            if soc == 0:
                new_state = Failures("L2-FAILURE", time, location, self.system_states[-1], trajectory)
                self.l2_failure.append(new_state)
        else:
            instrument.loadshedding_flag = False

    def write_header_failure(self, file):
        file.write("State , Time, Latitude in deg, Longitude in deg, System State, Trajectory File\n")

    def write_header_states(self, file):
        file.write(
            "State , Start time, End time, duration in h, Start Latitude in deg, Start Longitude in deg, End Latitude in deg, End Longitude in deg\n"
        )

    def write_states(self):
        # Ensure output directories exist
        for filepath in [self.sysfile, self.l1file, self.l2file]:
            if filepath:
                Path(filepath).parent.mkdir(parents=True, exist_ok=True)

        with open(self.sysfile, "w+") as file:
            file.write("System states\n")
            self.write_header_states(file)
            for state in self.system_states:
                file.write(str(state))

        with open(self.l1file, "w+") as file:
            file.write(f"L1 Failures\n")
            self.write_header_failure(file)
            for state in self.l1_failure:
                file.write(str(state))

        with open(self.l2file, "w+") as file:
            file.write("L2 Failures\n")
            self.write_header_failure(file)
            for state in self.l2_failure:
                file.write(str(state))
