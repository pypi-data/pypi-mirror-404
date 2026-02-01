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


from abc import ABC, abstractmethod
from dataclasses import dataclass

import astropy.units as u
import numpy as np
from astropy.coordinates import EarthLocation
from astropy.time import Time


class Location(ABC):
    @abstractmethod
    def get_limb(self):
        raise NotImplementedError


@dataclass
class SimpleLocation(Location):
    """The SimpleLocation class can be used to represent the location of the detector and has
    a function defined to calculate the limb."""

    latitude: u.Quantity = 0 * u.deg
    longitude: u.Quantity = 0 * u.deg
    elevation: u.Quantity = 0 * u.m

    def __post_init__(self):
        self.det_loc = EarthLocation(
            lat=self.latitude,
            lon=self.longitude,
            height=self.elevation,
        )

    def get_limb(self):
        """The get_limb() function is used to calculate the limb given a detector location
        and elevation in meters

        Returns:
            float : Angle of the limb
        """
        radius_earth = 6371000 * u.m
        return (np.arcsin(radius_earth / (radius_earth + self.elevation)).value - np.pi / 2) * u.rad


@dataclass
class LatitudeRange(Location):
    """The LatitudeRange class represents the latitude range defined by a user.
    This class creates a list of simple locations that can be used to calculate
    the solar elevation angle."""

    latitude_start: u.Quantity = 0 * u.deg
    latitude_end: u.Quantity = 0 * u.deg
    longitude: u.Quantity = 0 * u.deg
    elevation: u.Quantity = 0 * u.m
    increment: u.Quantity = 1 * u.deg

    def __post_init__(self):
        self.latitudes = (
            np.arange(
                self.latitude_start.to("deg").value,
                self.latitude_end.to("deg").value + 1,
                self.increment.to("deg").value,
            )
            * u.deg
        )
        self.latitude_range = [
            SimpleLocation(latitude=lat, longitude=self.longitude, elevation=self.elevation) for lat in self.latitudes
        ]

    def get_limb(self):
        """The get_limb() function is used to calculate the limb given a detector location and elevation in meters

        Returns:
            float : Angle of the limb
        """
        return self.latitude_range[0].get_limb()

    def __len__(self):
        return len(self.latitude_range)

    def __str__(self) -> str:
        return str(self.__dict__)


# class DateRange:
#     """The DateRange class can generate a range of dates for a given set of input parameters.
#     If you do not supply an end_date, it will generate a set of times for one 24 hour period.
#     """

#     def __init__(
#         self,
#         start_date: str,
#         end_date: str = None,
#         format: str = "iso",
#         scale: str = "utc",
#         frequency: str = "H",
#     ) -> None:
#         self.start_date = Time(start_date, format=format, scale=scale).to_datetime()
#         if end_date is None:
#             self.end_date = (
#                 Time(start_date, format=format, scale=scale) + 23 * u.h
#             ).to_datetime()
#         else:
#             self.end_date = Time(end_date, format=format, scale=scale).to_datetime()

#         self.date_range = pd.date_range(
#             start=self.start_date, end=self.end_date, freq=frequency
#         ).tz_localize(tz=datetime.timezone.utc, ambiguous="NaT")

#         self.times = Time(self.date_range)

#     def __len__(self):
#         return len(self.date_range)


@dataclass
class Times:
    """The DateRange class can generate a range of dates for a given set of input parameters.
    If you do not supply an end_date, it will generate a set of times for one 24 hour period.
    """

    start_time: str = "2023-01-01T00:00:00"
    end_time: str = None
    format: str = "isot"
    scale: str = "utc"
    frequency: u.Quantity = 10 * u.min

    def __post_init__(
        self,
    ) -> None:

        self.start_time = Time(self.start_time, format=self.format, scale=self.scale)
        if self.end_time is None:
            self.end_time = self.start_time + 24 * u.h
        else:
            self.end_time = Time(self.end_time, format=self.format, scale=self.scale)

        self.duration = (self.end_time + 1 * u.min - self.start_time).to(u.min)
        time_range = np.arange(0, self.duration.value, self.frequency.to(u.min).value) * u.min

        self.times = self.start_time + time_range
        self.date_range = self.times.to_datetime()

    def set_start_time(self, start_time: str):
        self.start_time = Time(start_time, format=self.format, scale=self.scale)

    def set_end_time(self, end_time: str):
        self.end_time = Time(end_time, format=self.format, scale=self.scale)

    def __len__(self):
        return len(self.date_range)

    def __str__(self) -> str:
        return str(self.__dict__)
