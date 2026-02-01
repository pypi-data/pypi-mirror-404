power-production
================

Analyze solar power generation over time.

.. click:: PASS.apps.power_production:power_production
   :prog: pass power-production
   :nested: full

Description
-----------

This command calculates the power output from the configured solar array system
over the specified time range and location. It accounts for:

- Solar elevation angle throughout the day
- Panel tilt and pointing angles
- Panel efficiency and area
- Limb effects at altitude

The analysis shows how power production varies with time and can help optimize
solar array configuration.

Configuration
-------------

Key configuration sections:

.. code-block:: toml

   [Times]
   start_time = "2023-05-20 12:00:00"
   end_time = "2023-06-01 12:00:00"
   frequency = "1 hour"

   [Location.SimpleLocation]
   latitude = "-45deg"
   longitude = "169deg"
   elevation = "33km"

   [solar_power_system.array1]
   n_panels = 3
   tilt_angle = "15deg"
   pointing_angle = "-45deg"
   panel_efficiency = 0.15
   panel_area = "0.54m^2"

Example
-------

.. code-block:: bash

   pass power-production my_config.toml

Output
------

Generates a plot showing total power production over time, saved to the path
specified in ``[plots].power_production_total``.
