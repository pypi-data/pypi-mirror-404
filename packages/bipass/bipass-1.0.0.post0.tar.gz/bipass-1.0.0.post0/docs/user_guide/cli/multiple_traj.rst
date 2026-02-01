multiple-traj
=============

Run batch analysis across multiple trajectory files.

.. click:: PASS.apps.multiple_trajectory:multiple_traj
   :prog: pass multiple-traj
   :nested: full

Description
-----------

This command processes all trajectory files in a specified directory, running the
power system simulation on each one. This is useful for:

- Monte Carlo analysis of power system reliability
- Comparing performance across different launch dates
- Statistical analysis of mission success probability

Configuration
-------------

Specify the trajectory directory in your configuration:

.. code-block:: toml

   [multiple_trajectory]
   trajectory_path = "/data/Simulated_trajectories/2023"

Example
-------

.. code-block:: bash

   pass multiple-traj my_config.toml

Output
------

Generates aggregate statistics and plots showing power system performance
across all trajectories.
