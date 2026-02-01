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


import datetime

import numpy as np
import pandas as pd

# import pysolar as ps
from astropy import units as u
from astropy.coordinates import Latitude
from astropy.time import Time

from ..general_framework.general_classes import SimpleLocation

# from pysolar import constants


class SolarArray:
    """The SolarArray class is used to represent the solar array configuration of a payload."""

    def __init__(
        self,
        number_of_panels_per_side: int = 1,
        tilt_angle: u.Quantity = 0 * u.deg,
        pointing_angle: u.Quantity = 0 * u.deg,
        solar_panel_efficiency: float = 0.2,
        panel_area: u.Quantity = 1 * u.m**2,
    ) -> None:
        self.number_of_panels_per_side = number_of_panels_per_side
        self.tilt_angle = tilt_angle
        self.pointing_angle = pointing_angle
        self.solar_panel_efficiency = solar_panel_efficiency
        self.panel_area = panel_area.to(u.m**2).value

    def set_tilt_angle(self, tilt_angle: u.Quantity) -> None:
        """The set_tilt_angle() function is used to set the tilt angle of the solar array.

        Args:
            tilt_angle (u.Quantity): The tilt angle of the solar array in degrees
        """
        self.tilt_angle = tilt_angle
        self.normal_tilt = tilt_angle
        self.normal_tilt_rad = np.deg2rad(tilt_angle)

    def get_power_production(
        self,
        solar_elevation_angle: np.ndarray,
        limb: float,
        solar_power_input: u.Quantity = 1368 * u.W / u.m**2,
    ) -> np.ndarray:
        """The get_power_production() function generates the power production of the solar array system.  For both configurations, we assume calculate the power production for
        two arrays.  For a pointing configuraiton, the pointing angle remains at 0, so the 'second panel' does not generate any power.  For the solar skirt configuration, the offset
        angles of the sun in the horizontal direction is calculated and taken into account when generating the power for each panel.  It is assumed both panels are configured in the same
        way.

        Args:
            solar_elevation_angle (np.ndarray): Angle of the sun relative to horizontal.
            solar_power_input (float, optional): This is the solar power incident on the top of the atmosphere in Watts/meter^2. This number has been calculated by NASA and defaults to 1368.

        Returns:
            np.ndarray: Returns the power production of the solar array system for both configurations.
        """

        # calaulate the angular distance from the normal axis on the panels to the sun
        projection_angle = np.sin(solar_elevation_angle) * np.sin(self.tilt_angle) + np.cos(
            solar_elevation_angle
        ) * np.cos(self.tilt_angle) * np.cos(-self.pointing_angle)
        # Calculate the power production
        power_production = (
            self.solar_panel_efficiency
            * self.panel_area
            * self.number_of_panels_per_side
            * solar_power_input
            * projection_angle
        )

        power_production = np.where(
            solar_elevation_angle > limb,
            power_production,
            0,
        )
        power_production = np.where(power_production < 0, 0, power_production)
        return power_production

    def get_total_power_produciton(self, power_production: np.ndarray):
        total_power_production = np.sum(power_production)

        return total_power_production

    def __str__(self) -> str:
        return str(self.__dict__)


class SolarSkirt:
    def __init__(self):
        self.arrays = []

    def add_array(self, solar_array: SolarArray) -> None:
        """Function to add a new panel to the solar skirt

        Args:
            solar_array (SolarArray): Solar array to add to the configureation
        """
        self.arrays.append(solar_array)

    def get_power_production(self, solar_elevation_angle: np.ndarray, solar_power_input: float = 1368) -> np.ndarray:
        """Function to calculate the power output of the solar skirt for a set of given solar elevation angles

        Args:
            solar_elevation_angle (np.ndarray): solar elevation angles
            solar_power_input (float, optional): Power output by the sun in W/m^2. Defaults to 1368.

        Returns:
            np.ndarray: Array of the power produced by the solar array for all given input angles
        """

        if isinstance(solar_elevation_angle, u.Quantity):
            all_array_power = 0 * u.W
        else:
            all_array_power = np.zeros(len(solar_elevation_angle), dtype=u.Quantity) * u.W
        for array in self.arrays:
            all_array_power = all_array_power + array.get_power_production(solar_elevation_angle, solar_power_input)
        return all_array_power

    def set_tilt_angle(self, tilt_angle: float) -> None:
        for array in self.arrays:
            array.set_tilt_angle(tilt_angle)

    def __str__(self) -> str:
        return str(self.__dict__)
