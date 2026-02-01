single-traj
===========

Simulate power system performance along a single balloon flight trajectory.

.. click:: PASS.apps.single_trajectory:single_traj
   :prog: pass single-traj
   :nested: full

Description
-----------

This command reads a trajectory file (CSV format) and simulates the power system
behavior at each point along the flight path. It calculates:

- Solar power production based on position, time, and solar elevation
- Power consumption based on operating mode (day/night/observation)
- Net power balance
- Battery state of charge over time
- L1/L2 failure events

Trajectory File Format
----------------------

The trajectory CSV file should have the following columns (after a 9-line header):

1. ``datetime`` - Timestamp
2. ``lat`` - Latitude in degrees
3. ``long`` - Longitude in degrees
4. ``alt`` - Altitude in meters
5. ``Ewind`` - East wind component
6. ``Nwind`` - North wind component

Configuration
-------------

Specify the trajectory file in your configuration:

.. code-block:: toml

   [single_trajectory]
   trajectory_path = "./data"
   trajectory_file_name = "simulated_traj_2023-04-01.csv"

Example
-------

.. code-block:: bash

   pass single-traj my_config.toml

Output
------

Generates a plot showing:

- Net power production over time
- Battery state of charge percentage
- Loadshedding threshold indicator
