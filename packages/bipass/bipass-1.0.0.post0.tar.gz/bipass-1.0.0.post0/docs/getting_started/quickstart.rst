Quickstart
==========

This guide walks you through a basic BI-PASS workflow: creating a configuration,
customizing it for your mission, and running a simulation.

Step 1: Create a Configuration File
------------------------------------

BI-PASS uses TOML configuration files to define all simulation parameters. Generate
a template configuration:

.. code-block:: bash

   pass make-config my_mission.toml

This creates a file with default values that you can customize.

Step 2: Edit the Configuration
------------------------------

Open ``my_mission.toml`` in your editor and configure the key sections:

**Time Range**

Define the simulation time period:

.. code-block:: toml

   [Times]
   start_time = "2023-05-20 12:00:00"
   end_time = "2023-06-01 12:00:00"
   frequency = "1 hour"

**Location**

Set the balloon's location or latitude range:

.. code-block:: toml

   [Location.SimpleLocation]
   latitude = "-45deg"
   longitude = "169deg"
   elevation = "33km"

**Solar Array**

Configure your solar panel setup:

.. code-block:: toml

   [solar_power_system.array1]
   n_panels = 3
   tilt_angle = "15deg"
   pointing_angle = "-45deg"
   panel_efficiency = 0.15
   panel_area = "0.54m^2"

**Battery Bank**

Define your battery configuration:

.. code-block:: toml

   [battery_bank]
   n_batteries = 6
   nominal_capacity_per_battery = "1800W h"
   starting_capacity = "11000W h"

Step 3: Run a Simulation
------------------------

With your configuration ready, run a power production analysis:

.. code-block:: bash

   # Analyze solar power production
   pass power-production my_mission.toml

   # Or run a full trajectory simulation
   pass single-traj my_mission.toml

Step 4: View Results
--------------------

BI-PASS generates plots in the directory specified by ``[plots].plot_directory`` in
your configuration. Open the generated PDF files to visualize:

- Power production over time
- Battery state of charge
- Net power balance
- Day/night periods

Next Steps
----------

- See :doc:`concepts` for detailed explanations of BI-PASS terminology
- Explore the :doc:`../user_guide/configuration` reference for all options
- Check the :doc:`../user_guide/cli/index` for all available commands
