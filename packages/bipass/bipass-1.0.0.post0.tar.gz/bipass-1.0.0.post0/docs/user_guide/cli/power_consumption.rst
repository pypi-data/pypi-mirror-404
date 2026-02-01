power-consumption
=================

Analyze instrument power usage over time.

.. click:: PASS.apps.power_consumption:power_consumption
   :prog: pass power-consumption
   :nested: full

Description
-----------

This command calculates the power consumption of the instrument over the specified
time range, based on the operating mode at each time step:

- **Daytime**: Sun above limb - lower power for thermal control
- **Nighttime**: Sun below limb, moon visible - moderate power
- **Observation**: Sun and moon below limb - full observation power
- **Survival**: Low battery - minimal power consumption

Configuration
-------------

Key configuration sections:

.. code-block:: toml

   [Instrument]
   daytime_power = "100W"
   nighttime_power = "200W"
   observation_power = "300W"
   survival_power = "50W"

   [Times]
   start_time = "2023-05-20 12:00:00"
   end_time = "2023-06-01 12:00:00"
   frequency = "1 hour"

Example
-------

.. code-block:: bash

   pass power-consumption my_config.toml

Output
------

Generates a plot showing power consumption over time, with different colors
or markers indicating the operating mode.
