import pathlib as pl
from dataclasses import dataclass, field

from astropy import units as u

from ..general_framework.general_classes import LatitudeRange, SimpleLocation, Times
from ..general_framework.power_status import Status
from ..power_consumption.power_consumption_classes import BatteryBank, Instrument
from ..solar_production.solar_production_classes import SolarSkirt


@dataclass
class Constants:
    solar_irradiance: u.Quantity = u.Quantity("1360 W / m^2")
    radius_earth: u.Quantity = u.Quantity("6371000 m")


@dataclass
class Plots:
    plot_directory: pl.Path = pl.Path("./plots/")
    min_battery_cap: pl.Path = None
    net_power: pl.Path = None
    power_production_total: pl.Path = None
    single_trajectory: pl.Path = None
    multiple_trajectory: pl.Path = None
    optimal_tilt: pl.Path = None
    day_night_time_plot: pl.Path = None
    power_consumption: pl.Path = None

    def __post_init__(self):
        """Ensure the plot directory exists."""
        self.plot_directory.mkdir(parents=True, exist_ok=True)


class MinimumBatteryCap:
    set_cap_range: u.Quantity = u.Quantity(300, u.W * u.h)


class Optimal_tilt:
    frequency = None
    min_tilt = None
    max_tilt = None
    tilt_increment = None


@dataclass
class PassConfig:
    const: Constants = field(default_factory=Constants)
    instrument: Instrument = field(default_factory=Instrument)
    solar_power_system: SolarSkirt = field(default_factory=SolarSkirt)
    battery_bank: BatteryBank = field(default_factory=BatteryBank)
    single_location: SimpleLocation = field(default_factory=SimpleLocation)
    latitude_range: LatitudeRange = field(default_factory=LatitudeRange)
    date_range: Times = field(default_factory=Times)
    multiple_traj: dict = field(default_factory=dict)
    single_traj: dict = field(default=dict)
    status: Status = field(default_factory=Status)
    plots: Plots = field(default_factory=Plots)
    # min_battery_cap: MinimumBatteryCap = field(default_factory=MinimumBatteryCap)
    optimal_tilt: Optimal_tilt = field(default_factory=Optimal_tilt)
