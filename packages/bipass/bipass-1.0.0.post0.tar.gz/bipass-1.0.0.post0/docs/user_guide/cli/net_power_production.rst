net-power-production
====================

Calculate net power (production minus consumption) over time.

.. click:: PASS.apps.net_power_production:net_power_production
   :prog: pass net-power-production
   :nested: full

Description
-----------

This command combines the power production and consumption analyses to calculate
the net power balance:

.. code-block:: text

   Net Power = Solar Production - Instrument Consumption

Positive values indicate battery charging; negative values indicate discharging.

This analysis is essential for understanding whether the power system can sustain
the mission and when power deficits may occur.

Configuration
-------------

Requires configuration for both production and consumption:

.. code-block:: toml

   [Times]
   start_time = "2023-05-20 12:00:00"
   end_time = "2023-06-01 12:00:00"
   frequency = "1 hour"

   [solar_power_system.array1]
   n_panels = 3
   tilt_angle = "15deg"
   pointing_angle = "-45deg"
   panel_efficiency = 0.15
   panel_area = "0.54m^2"

   [Instrument]
   daytime_power = "100W"
   nighttime_power = "200W"
   observation_power = "300W"
   survival_power = "50W"

Example
-------

.. code-block:: bash

   pass net-power-production my_config.toml

Output
------

Generates a plot showing net power over time, saved to the path specified in
``[plots].net_power``.
