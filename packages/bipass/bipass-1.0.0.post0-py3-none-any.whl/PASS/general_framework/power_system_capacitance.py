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

import astropy.coordinates as coord
from astropy import units as u
from astropy.time import Time

from ..config.config import PassConfig
from ..power_consumption.power_consumption_classes import BatteryBank
from ..solar_production.solar_elevation_angle import get_lunar_elevation, get_solar_elevation
from ..solar_production.solar_production_classes import SolarArray
from .general_classes import SimpleLocation


def generate_battery_bank_capacitance(
    config: PassConfig,
    time: Time,
    increment: u.Quantity,
    coords: coord.AltAz,
    angles: list = None,
    power_production: u.Quantity = None,
    battery_bank: BatteryBank = None,
    trajectory_file: str = None,
):
    if angles is None:
        # Get the solar, lunar elevation for the new date:
        solar_elevation = get_solar_elevation(time, coords)
        lunar_elevation = get_lunar_elevation(time, coords)
        limb = coords.get_limb()
    else:
        solar_elevation = angles[0]
        lunar_elevation = angles[1]
        limb = angles[2]

    if power_production is None:
        # Get the power production for this day and time:
        solar_array = config.solar_power_system
        power_production = solar_array.get_power_production(solar_elevation, limb)

    # Update the status of the system
    status = config.status
    status.update_sys(
        time,
        coords,
        solar_elevation,
        lunar_elevation,
        limb,
    )

    # Get the power consumption for this day and time:
    instrument = config.instrument
    power_consumption = instrument.get_power_consumption(solar_elevation, lunar_elevation, limb)

    # Get the power in Watt hours:
    power_in_Wh = (power_production - power_consumption) * increment.to("hour")

    if battery_bank is None:
        battery_bank = config.battery_bank

    battery_bank.update_capacitance(power_in_Wh)

    net_power_per_increment = power_production - power_consumption

    status.update_fail(time, coords, battery_bank, instrument, trajectory_file)

    return (
        net_power_per_increment,
        power_production * increment.to("hour"),
        power_consumption * increment.to("hour"),
    )
