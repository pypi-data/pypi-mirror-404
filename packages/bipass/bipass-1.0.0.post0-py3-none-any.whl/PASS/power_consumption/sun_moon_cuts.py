import datetime

import attr
import numpy as np
from astropy import units as u
from astropy.coordinates import AltAz, EarthLocation, get_body
from astropy.time import Time

from ..general_framework.general_classes import SimpleLocation


def moon_phase_angle(time, ephemeris=None):
    sun = get_body("sun", time)
    moon = get_body("moon", time, ephemeris=ephemeris)
    elongation = sun.separation(moon)
    return np.arctan2(
        sun.distance * np.sin(elongation),
        moon.distance - sun.distance * np.cos(elongation),
    )


def moon_illumination(time, ephemeris=None):
    i = moon_phase_angle(time, ephemeris=ephemeris)
    k = (1 + np.cos(i)) / 2.0
    return k.value


def moon_cut(self, time: Time, detector_frame: AltAz) -> bool:
    return np.where(
        moon_illumination(time) < self.crit_moon_illumination,
        True,
        self.moon_alt_cut(time, detector_frame),
    )


def moon_alt_cut(time: datetime, location: SimpleLocation) -> float:
    moon_location = EarthLocation(
        lat=location.latitude,
        lon=location.longitude,
        height=location.elevation,
    )
    moon_time = Time(time)
    detector_frame = AltAz(obstime=moon_time, location=moon_location)
    moon_alt = get_body("moon", moon_time).transform_to(detector_frame).alt
    return moon_alt
