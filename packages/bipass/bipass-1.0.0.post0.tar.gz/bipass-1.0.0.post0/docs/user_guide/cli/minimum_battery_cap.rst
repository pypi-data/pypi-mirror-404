minimum-battery-cap
===================

Determine the minimum battery capacity required for mission success.

.. click:: PASS.apps.minimum_battery_capacitance:minimum_battery_cap
   :prog: pass minimum-battery-cap
   :nested: full

Description
-----------

This command calculates the minimum battery bank capacity needed to avoid
L1 or L2 failures during the mission. It analyzes the net power balance
over time to find:

- Maximum energy deficit during the mission
- Required capacity to maintain SoC above the loadshedding threshold
- Safety margins for the power system

This is essential for battery sizing during mission planning.

Configuration
-------------

Key configuration sections:

.. code-block:: toml

   [minimum_battery_cap]
   set_cap_range = "300"

   [battery_bank]
   n_batteries = 6
   nominal_capacity_per_battery = "1800W h"

   [status]
   loadshedding_SoC = 30

Example
-------

.. code-block:: bash

   pass minimum-battery-cap my_config.toml

Output
------

Generates a plot showing the relationship between battery capacity and
mission performance, saved to ``[plots].min_battery_cap``.
