Configuration Reference
=======================

BI-PASS uses TOML configuration files to define all simulation parameters. This page
documents all available configuration sections and options.

Generate a template configuration file with:

.. code-block:: bash

   pass make-config my_config.toml


Constants
---------

Physical constants used in calculations.

.. code-block:: toml

   [Constants]
   solar_irradiance = "1360 W/m^2"

``solar_irradiance``
   Solar power at the top of the atmosphere. Default: ``1360 W/m^2``


Status
------

Configuration for system state tracking and output files.

.. code-block:: toml

   [status]
   system_file = "status/system.csv"
   l1_file = "status/l1_failures.csv"
   l2_file = "status/l2_failures.csv"
   loadshedding_SoC = 30

``system_file``
   Output file for system state transitions (day/night/observation).

``l1_file``
   Output file for L1 (loadshedding) failure events.

``l2_file``
   Output file for L2 (complete discharge) failure events.

``loadshedding_SoC``
   State of charge threshold (%) below which the instrument enters survival mode.
   Default: ``30``


Times
-----

Simulation time range and resolution.

.. code-block:: toml

   [Times]
   start_time = "2023-05-20 12:00:00"
   end_time = "2023-06-01 12:00:00"
   format = "iso"
   scale = "utc"
   frequency = "24 hour"

``start_time``
   Simulation start time in the specified format.

``end_time``
   Simulation end time. If omitted, defaults to 24 hours after start.

``format``
   Time format: ``iso`` (YYYY-MM-DD HH:MM:SS) or ``isot`` (YYYY-MM-DDTHH:MM:SS).

``scale``
   Time scale. Use ``utc`` for most applications.

``frequency``
   Time step between calculations. Examples: ``1 hour``, ``10 min``, ``30 s``.


Location
--------

Geographic position of the balloon. Two options are available:

SimpleLocation
^^^^^^^^^^^^^^

A single fixed position:

.. code-block:: toml

   [Location.SimpleLocation]
   latitude = "-45deg"
   longitude = "169deg"
   elevation = "33km"

``latitude``
   Geographic latitude with unit (e.g., ``-45deg``, ``45.5deg``).

``longitude``
   Geographic longitude with unit.

``elevation``
   Altitude above sea level with unit.

LatitudeRange
^^^^^^^^^^^^^

A range of latitudes for analysis across different positions:

.. code-block:: toml

   [Location.LatitudeRange]
   latitude_start = "-80deg"
   latitude_end = "-45deg"
   longitude = "169deg"
   elevation = "33km"
   increment = "1deg"

``latitude_start``
   Starting latitude of the range.

``latitude_end``
   Ending latitude of the range.

``increment``
   Step size between latitude values.


Battery Bank
------------

Battery system configuration.

.. code-block:: toml

   [battery_bank]
   n_batteries = 6
   nominal_capacity_per_battery = "1800W h"
   starting_capacity = "11000W h"

``n_batteries``
   Number of batteries in the bank.

``nominal_capacity_per_battery``
   Capacity of each individual battery.

``starting_capacity``
   Initial total charge at simulation start.


Instrument
----------

Instrument power consumption in different operating modes.

.. code-block:: toml

   [Instrument]
   daytime_power = "100W"
   nighttime_power = "200W"
   observation_power = "300W"
   survival_power = "50W"

``daytime_power``
   Power consumption when the sun is above the limb.

``nighttime_power``
   Power consumption at night when the moon is visible.

``observation_power``
   Power consumption during observation (sun and moon both below limb).

``survival_power``
   Minimum power consumption in loadshedding mode.


Solar Power System
------------------

Solar array configuration. Define multiple arrays for a solar skirt setup.

.. code-block:: toml

   [solar_power_system.array1]
   n_panels = 3
   tilt_angle = "15deg"
   pointing_angle = "-45deg"
   panel_efficiency = 0.15
   panel_area = "0.54m^2"

   [solar_power_system.array2]
   n_panels = 3
   tilt_angle = "15deg"
   pointing_angle = "45deg"
   panel_efficiency = 0.15
   panel_area = "0.54m^2"

Each array (``array1``, ``array2``, etc.) has:

``n_panels``
   Number of panels in this array.

``tilt_angle``
   Angle of panel surface from vertical.

``pointing_angle``
   Azimuthal direction the panel faces.

``panel_efficiency``
   Conversion efficiency (0.0 to 1.0).

``panel_area``
   Area of each panel.


Optimal Tilt
------------

Parameters for tilt angle optimization.

.. code-block:: toml

   [optimal_tilt]
   frequency = "1 hour"
   min_tilt = 0
   max_tilt = 90
   tilt_increment = 1

``frequency``
   Time step for optimization calculations.

``min_tilt``
   Minimum tilt angle to evaluate (degrees).

``max_tilt``
   Maximum tilt angle to evaluate (degrees).

``tilt_increment``
   Step size for tilt angle search (degrees).


Minimum Battery Capacity
------------------------

Parameters for minimum battery capacity analysis.

.. code-block:: toml

   [minimum_battery_cap]
   set_cap_range = "300"

``set_cap_range``
   Range parameter for capacity analysis (Wh).


Trajectory
----------

Trajectory file locations for simulation.

Single Trajectory
^^^^^^^^^^^^^^^^^

.. code-block:: toml

   [single_trajectory]
   trajectory_path = "./data"
   trajectory_file_name = "simulated_traj_2023-04-01.csv"

``trajectory_path``
   Directory containing trajectory files.

``trajectory_file_name``
   Name of the trajectory CSV file.

Multiple Trajectories
^^^^^^^^^^^^^^^^^^^^^

.. code-block:: toml

   [multiple_trajectory]
   trajectory_path = "/data/Simulated_trajectories/2023"

``trajectory_path``
   Directory containing multiple trajectory files for batch analysis.


Plots
-----

Output file configuration for generated plots.

.. code-block:: toml

   [plots]
   plot_directory = "plots/"
   min_battery_cap = "pass_min_battery_cap.pdf"
   net_power = "pass_net_power.pdf"
   power_production_total = "pass_total_power_production.pdf"
   single_trajectory = "pass_single_traj_performance.pdf"
   multiple_trajectory = "pass_multi_traj_performance.pdf"
   optimal_tilt = "pass_optimal_tilt.pdf"
   day_night_time_plot = "pass_day_night_time_plot.pdf"
   power_consumption = "pass_power_consumption.pdf"

``plot_directory``
   Base directory for all output plots.

Other fields specify filenames for each analysis type.
