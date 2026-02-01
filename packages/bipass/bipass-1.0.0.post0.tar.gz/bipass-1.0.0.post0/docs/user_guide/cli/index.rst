Command Line Interface
======================

BI-PASS provides a command-line interface for running simulations and analyses.
After installation, the ``pass`` command is available with the following subcommands.

.. toctree::
   :maxdepth: 1

   make_config
   single_traj
   multiple_traj
   power_production
   power_consumption
   net_power_production
   optimal_tilt
   minimum_battery_cap
   phase_space
   plot_trajectory

Main Command
------------

.. click:: PASS.apps.cli:cli
   :prog: pass
   :nested: none

Quick Reference
---------------

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Command
     - Description
   * - ``pass make-config``
     - Generate a template configuration file
   * - ``pass single-traj``
     - Run simulation on a single trajectory
   * - ``pass multiple-traj``
     - Batch analysis across multiple trajectories
   * - ``pass power-production``
     - Analyze solar power generation
   * - ``pass power-consumption``
     - Analyze instrument power usage
   * - ``pass net-power-production``
     - Calculate net power (production minus consumption)
   * - ``pass optimal-tilt``
     - Find optimal solar array tilt angle
   * - ``pass minimum-battery-cap``
     - Determine minimum required battery capacity
   * - ``pass phase-space``
     - Phase space analysis
   * - ``pass plot-trajectory``
     - Visualize trajectory data
