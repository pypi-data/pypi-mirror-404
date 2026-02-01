import astropy.units as u
import pytest

from PASS.config.config import PassConfig
from PASS.solar_production.solar_production_classes import SolarArray


def test_tilt_angle(solar_array: SolarArray):
    """Test setting the tilt angle of the solar array

    Args:
        solar_array (SolarArray): Solar array object
    """
    solar_array.set_tilt_angle(45 * u.deg)
    assert solar_array.tilt_angle == 45 * u.deg
    solar_array.set_tilt_angle(0 * u.deg)
    assert solar_array.tilt_angle == 0 * u.deg


def test_power_production(config: PassConfig, solar_array: SolarArray):
    """Test the power production of the solar array

    Args:
        config (PassConfig): Configuration object that determines the solar irradiance
        solar_array (SolarArray): Solar array object
    """
    solar_irradiance = config.const.solar_irradiance
    solar_array.set_tilt_angle(0 * u.deg)
    power_production = solar_array.get_power_production(0 * u.deg, limb=-90 * u.deg, solar_power_input=solar_irradiance)
    assert (
        power_production
        == solar_array.panel_area
        * solar_array.solar_panel_efficiency
        * solar_irradiance
        * solar_array.number_of_panels_per_side
    )
    power_production = solar_array.get_power_production(
        90 * u.deg, limb=-90 * u.deg, solar_power_input=solar_irradiance
    )
    assert power_production.to(u.W / u.m**2).value == pytest.approx(0)
