from .power_consumption_classes import BatteryBank


def get_battery_bank_capacitance(battery_bank_capacitance, power_consumption_wh, power_production_wh):
    if battery_bank_capacitance == BatteryBank.set_max_capacitance():
        battery_bank_capacitance = BatteryBank.set_max_capacitance()

    else:
        battery_bank_capacitance = battery_bank_capacitance + power_production_wh - power_consumption_wh

    return battery_bank_capacitance
