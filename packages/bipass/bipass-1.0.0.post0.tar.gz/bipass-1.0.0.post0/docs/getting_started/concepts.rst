Core Concepts
=============

This page explains the key concepts and terminology used in BI-PASS.

Limb Angle
----------

The **limb angle** is the angle between the horizontal plane at the balloon's
altitude and the line of sight to Earth's horizon. At high altitudes (e.g., 33 km),
the horizon appears below horizontal, so the limb angle is negative.

The limb angle determines when the sun rises and sets from the balloon's perspective.
At stratospheric altitudes, the balloon can "see" the sun even when ground observers
are in darkness.

.. note::

   BI-PASS calculates the limb angle automatically based on the balloon's elevation
   using the formula: ``limb = arcsin(R_earth / (R_earth + elevation)) - π/2``

Solar Elevation Angle
---------------------

The **solar elevation angle** is the angle of the sun above the horizontal plane.
It varies throughout the day and year based on:

- Time of day
- Date (season)
- Latitude
- Altitude (affects the reference horizon via the limb angle)

When the solar elevation is above the limb angle, the sun is visible and solar
panels can generate power.

Solar Array Configuration
-------------------------

BI-PASS models solar arrays with several parameters:

**Tilt Angle**
   The angle of the panel surface relative to vertical. A tilt of 0° means the
   panel faces straight out horizontally; 90° means it faces straight up.

**Pointing Angle**
   The azimuthal direction the panel faces, measured from the forward direction
   of the payload. Multiple panels at different pointing angles form a "solar skirt."

**Solar Skirt**
   A configuration where multiple solar arrays are arranged around the payload
   at different pointing angles (e.g., -135°, -45°, 45°, 135°). This ensures
   power generation regardless of the balloon's orientation.

Power States
------------

The instrument power consumption depends on the current operating state:

**Daytime**
   Sun is above the limb angle. Typically lower power consumption as heating
   is not required.

**Nighttime**
   Sun is below the limb but moon may be visible. Moderate power consumption
   for heating and standby operations.

**Observation**
   Both sun and moon are below the limb. This is the prime observation period
   for astronomical instruments, potentially requiring higher power for
   active data collection.

**Survival (Loadshedding)**
   Battery state of charge has dropped below the loadshedding threshold.
   Minimum power consumption to preserve battery life.

Failure Modes
-------------

BI-PASS tracks two failure modes during simulations:

**L1 Failure (Loadshedding)**
   The battery state of charge drops below the configured threshold
   (``loadshedding_SoC``). The instrument enters survival mode with reduced
   power consumption. This is recoverable once the batteries recharge.

**L2 Failure (Complete Discharge)**
   The battery state of charge reaches 0%. This represents a critical failure
   where the instrument cannot operate.

State of Charge (SoC)
---------------------

The **state of charge** is the current battery capacity as a percentage of
maximum capacity:

.. code-block:: text

   SoC = (current_capacity / max_capacity) × 100%

BI-PASS tracks SoC throughout simulations to identify when loadshedding occurs
and whether the power system can sustain the mission.

Net Power
---------

**Net power** is the difference between power production and consumption:

.. code-block:: text

   Net Power = Power Production - Power Consumption

- Positive net power charges the batteries
- Negative net power discharges the batteries

The integral of net power over time determines the battery state of charge.
