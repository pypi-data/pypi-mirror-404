import pathlib

import astropy.units as u
import pytest

from PASS.config.load_config import load_config
from PASS.solar_production.solar_production_classes import SolarArray


@pytest.fixture
def config():
    path = pathlib.Path(__file__).parent.resolve()
    config_file = f"{path}/test-config.toml"
    return load_config(config_file)


@pytest.fixture
def solar_array():
    return SolarArray(
        number_of_panels_per_side=2,
        panel_area=1 * u.m**2,
        tilt_angle=0 * u.deg,
        pointing_angle=0 * u.deg,
        solar_panel_efficiency=0.2,
    )
