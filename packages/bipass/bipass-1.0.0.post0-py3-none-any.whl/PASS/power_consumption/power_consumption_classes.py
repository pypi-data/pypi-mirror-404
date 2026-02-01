import astropy.units as u
import numpy as np


class BatteryBank:
    def __init__(
        self,
        starting_battery_capacity: u.Quantity = 0 * u.W * u.h,
        number_of_batteries: float = 0,
        nominal_battery_capacity: u.Quantity = 0 * u.W * u.h,
    ) -> None:
        self.number_of_batteries = number_of_batteries
        self.nominal_battery_capacity = nominal_battery_capacity
        self.starting_battery_capacity = starting_battery_capacity

    def calc_settings(self):
        # calculate parameters of the Battery bank
        self.max_capacitance = self.number_of_batteries * self.nominal_battery_capacity
        self.capacitance = self.max_capacitance
        self.soc = 100

    def get_individual_battery_load(self, power_consumption):
        individual_battery_load = power_consumption / self.number_of_batteries
        return individual_battery_load

    def update_capacitance(self, load: u.Quantity) -> None:
        self.capacitance = (
            np.min(
                [
                    (self.capacitance + load).to(u.W * u.h).value,
                    (self.max_capacitance).to(u.W * u.h).value,
                ]
            )
            * u.W
            * u.h
        )
        self.capacitance = np.max([self.capacitance.to(u.W * u.h).value, 0]) * u.W * u.h
        self.calc_soc()

    def calc_soc(self) -> None:
        self.soc = (self.capacitance / self.max_capacitance) * 100

    def get_soc(self) -> float:
        self.calc_soc()
        return self.soc

    def __str__(self) -> str:
        return str(self.__dict__)


class Instrument:
    def __init__(
        self,
        nighttime_power_consumption=0,
        observation_power_consumption=0,
        daytime_power_consumption=0,
        survival_power_consumption=0,
        loadshedding_flag=False,
    ) -> None:
        self.nighttime_power_consumption = nighttime_power_consumption
        self.observation_power_consumption = observation_power_consumption
        self.daytime_power_consumption = daytime_power_consumption
        self.survival_power_consumption = survival_power_consumption
        self.loadshedding_flag = loadshedding_flag

    def get_power_consumption(self, solar_elevation, moon_elevation, limb):
        if self.loadshedding_flag == True:
            power_consumption = self.survival_power_consumption

        else:
            if solar_elevation < limb:
                if moon_elevation < limb:
                    power_consumption = self.observation_power_consumption
                else:
                    power_consumption = self.nighttime_power_consumption
            else:
                power_consumption = self.daytime_power_consumption

        return power_consumption

    def get_power_consumption_array(
        self,
        solar_elevation: np.ndarray[float],
        moon_elevation: np.ndarray[float],
        loadshedding_flag: np.ndarray[bool],
        limb: float,
    ) -> np.ndarray[float]:

        power_consumption = np.where(
            solar_elevation < limb,
            self.nighttime_power_consumption,
            self.daytime_power_consumption,
        )
        power_consumption = np.where(
            np.logical_and(solar_elevation < limb, moon_elevation < limb),
            self.observation_power_consumption,
            power_consumption,
        )
        power_consumption = np.where(loadshedding_flag, self.survival_power_consumption, power_consumption)
        return power_consumption
