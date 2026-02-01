import pathlib as pl
import tomllib

from astropy import units as u

from ..general_framework.general_classes import LatitudeRange, SimpleLocation, Times
from ..general_framework.power_status import Status
from ..power_consumption.power_consumption_classes import BatteryBank, Instrument
from ..solar_production.solar_production_classes import SolarArray, SolarSkirt
from .config import MinimumBatteryCap, PassConfig, Plots


def read_config_file(file_path: str = "PASS_config.toml"):
    with open(file_path, "rb") as f:
        return tomllib.load(f)


def load_instrument(inst_conf_data: dict):
    instruments = [array_name for array_name in inst_conf_data.keys() if "instrument" in array_name]
    if len(instruments) >= 1:
        return [
            Instrument(
                daytime_power_consumption=u.Quantity(inst_conf_data[instrument]["daytime_power"]),
                nighttime_power_consumption=u.Quantity(inst_conf_data[instrument]["nighttime_power"]),
                observation_power_consumption=u.Quantity(inst_conf_data[instrument]["observation_power"]),
                survival_power_consumption=u.Quantity(inst_conf_data[instrument]["survival_power"]),
            )
            for instrument in instruments
        ]
    instrument = Instrument()
    instrument.daytime_power_consumption = u.Quantity(inst_conf_data["daytime_power"])
    instrument.nighttime_power_consumption = u.Quantity(inst_conf_data["nighttime_power"])
    instrument.observation_power_consumption = u.Quantity(inst_conf_data["observation_power"])
    instrument.survival_power_consumption = u.Quantity(inst_conf_data["survival_power"])
    return instrument


def load_solar_array(solar_conf: dict):
    arrays = [array_name for array_name in solar_conf.keys() if "array" in array_name]
    if len(arrays) == 1:
        solar_array = SolarArray()
        solar_array.number_of_panels_per_side = solar_conf[arrays[0]]["n_panels"]
        solar_array.tilt_angle = u.Quantity(solar_conf[arrays[0]]["tilt_angle"])
        solar_array.pointing_angle = u.Quantity(solar_conf[arrays[0]]["pointing_angle"])
        solar_array.solar_panel_efficiency = solar_conf[arrays[0]]["panel_efficiency"]
        solar_array.panel_area = u.Quantity(solar_conf[arrays[0]]["panel_area"])
        return solar_array

    solar_skirt = SolarSkirt()
    for array in arrays:
        solar_array = SolarArray()
        solar_array.number_of_panels_per_side = solar_conf[array]["n_panels"]
        solar_array.tilt_angle = u.Quantity(solar_conf[array]["tilt_angle"])
        solar_array.pointing_angle = u.Quantity(solar_conf[array]["pointing_angle"])
        solar_array.solar_panel_efficiency = solar_conf[array]["panel_efficiency"]
        solar_array.panel_area = u.Quantity(solar_conf[array]["panel_area"])
        solar_skirt.arrays.append(solar_array)
    return solar_skirt


def load_battery_bank(battery_conf: dict):
    battery_bank = BatteryBank()
    battery_bank.starting_battery_capacity = u.Quantity(battery_conf["starting_capacity"])
    battery_bank.nominal_battery_capacity = u.Quantity(battery_conf["nominal_capacity_per_battery"])
    battery_bank.number_of_batteries = battery_conf["n_batteries"]
    battery_bank.calc_settings()
    return battery_bank


def load_simple_location(location_conf: dict):
    if "SimpleLocation" in location_conf.keys():
        return SimpleLocation(
            latitude=u.Quantity(location_conf["SimpleLocation"]["latitude"]),
            longitude=u.Quantity(location_conf["SimpleLocation"]["longitude"]),
            elevation=u.Quantity(location_conf["SimpleLocation"]["elevation"]),
        )


def load_range_location(location_conf: dict):
    if "LatitudeRange" in location_conf.keys():
        location_conf = location_conf["LatitudeRange"]
        return LatitudeRange(
            latitude_start=u.Quantity(location_conf["latitude_start"]),
            latitude_end=u.Quantity(location_conf["latitude_end"]),
            longitude=u.Quantity(location_conf["longitude"]),
            elevation=u.Quantity(location_conf["elevation"]),
            increment=u.Quantity(location_conf["increment"]),
        )


def load_times(times_conf: dict):
    if "range1" not in times_conf.keys():
        return Times(
            start_time=times_conf["start_time"],
            end_time=times_conf["end_time"],
            format=times_conf["format"],
            scale=times_conf["scale"],
            frequency=u.Quantity(times_conf["frequency"]),
        )

    return [
        Times(
            start_time=times_conf[range]["start_time"],
            end_time=times_conf[range]["end_time"],
            format=times_conf[range]["format"],
            scale=times_conf[range]["scale"],
            frequency=u.Quantity(times_conf[range]["frequency"]),
        )
        for range in times_conf.keys()
    ]


def load_status(status_conf: dict):
    status = Status()
    status.sysfile = status_conf["system_file"]
    status.l1file = status_conf["l1_file"]
    status.l2file = status_conf["l2_file"]
    status.loadshedding_SoC = status_conf["loadshedding_SoC"]
    return status


# def load_min_battery_cap(min_battery_cap_conf: dict):
#     min_battery_cap = MinimumBatteryCap()
#     min_battery_cap.set_cap_range = u.Quantity(min_battery_cap_conf["set_cap_range"])
#     return min_battery_cap


def try_load_plots(plots_conf: dict, key: str):
    try:
        return pl.Path(plots_conf[key])
    except KeyError:
        return None


def load_plots(plots_conf: dict):
    plots = Plots()
    plots.plot_directory = pl.Path(plots_conf["plot_directory"])
    plots.min_battery_cap = plots.plot_directory / try_load_plots(plots_conf, "min_battery_cap")
    plots.net_power = plots.plot_directory / try_load_plots(plots_conf, "net_power")
    plots.power_production_total = plots.plot_directory / try_load_plots(plots_conf, "power_production_total")
    plots.single_trajectory = plots.plot_directory / try_load_plots(plots_conf, "single_trajectory")
    plots.multiple_trajectory = plots.plot_directory / try_load_plots(plots_conf, "multiple_trajectory")
    plots.optimal_tilt = plots.plot_directory / try_load_plots(plots_conf, "optimal_tilt")
    plots.day_night_time_plot = plots.plot_directory / try_load_plots(plots_conf, "day_night_time_plot")
    plots.power_consumption = plots.plot_directory / try_load_plots(plots_conf, "power_consumption")
    return plots


def load_config(file_path: str = "PASS_config.toml"):
    conf_data = read_config_file(file_path)
    config = PassConfig()
    config.instrument = load_instrument(conf_data["Instrument"])
    config.solar_power_system = load_solar_array(conf_data["solar_power_system"])
    config.battery_bank = load_battery_bank(conf_data["battery_bank"])
    config.single_location = load_simple_location(conf_data["Location"])
    config.latitude_range = load_range_location(conf_data["Location"])
    config.date_range = load_times(conf_data["Times"])
    config.multiple_traj = conf_data["multiple_trajectory"]
    config.single_traj = conf_data["single_trajectory"]
    config.optimal_tilt = conf_data["optimal_tilt"]
    config.status = load_status(conf_data["status"])
    config.plots = load_plots(conf_data["plots"])
    # config.min_battery_cap = load_min_battery_cap(conf_data["minimum_battery_cap"])
    return config
