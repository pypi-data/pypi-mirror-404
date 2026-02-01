BI-PASS Documentation
=====================

**BI-PASS** (Balloon Instrumentation Power system Analysis and Simulation Software)
is a Python framework for simulating power systems of long-duration balloon payloads.
It handles solar power production, battery capacity planning, power consumption
modeling, and trajectory-based performance simulation.

.. note::

   BI-PASS uses `Astropy <https://www.astropy.org/>`_ for unit handling and time
   management, ensuring physical quantities are always correctly represented.

Features
--------

- **Solar Power Production**: Model solar arrays with configurable tilt angles,
  pointing directions, and panel efficiency
- **Power Consumption**: Track instrument power usage across day/night/observation modes
- **Battery Management**: Simulate battery bank state of charge and capacity
- **Trajectory Analysis**: Evaluate power system performance along flight paths
- **Optimization Tools**: Find optimal solar array tilt angles and minimum battery capacity

BiPASS Overview
---------------

.. toctree::
   :maxdepth: 2
   :caption: BiPASS Overview

   use_cases/index

Getting Started
---------------

.. toctree::
   :maxdepth: 2
   :caption: Getting Started

   getting_started/index

User Guide
----------

.. toctree::
   :maxdepth: 2
   :caption: User Guide

   user_guide/index

API Reference
-------------

.. toctree::
   :maxdepth: 2
   :caption: API Reference

   api/index


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
