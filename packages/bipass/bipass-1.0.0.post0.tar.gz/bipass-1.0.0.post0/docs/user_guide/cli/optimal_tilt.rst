optimal-tilt
============

Find the optimal solar array tilt angle for maximum power production.

.. click:: PASS.apps.optimal_tilt:optimal_tilt
   :prog: pass optimal-tilt
   :nested: full

Description
-----------

This command searches through a range of tilt angles to find the configuration
that maximizes total power production over the simulation period. This is useful
for:

- Designing new solar array configurations
- Optimizing for specific mission profiles
- Understanding sensitivity to tilt angle

The optimization considers:

- Solar elevation throughout the day and season
- Latitude of operation
- Panel pointing angle

Configuration
-------------

Key configuration sections:

.. code-block:: toml

   [optimal_tilt]
   frequency = "1 hour"
   min_tilt = 0
   max_tilt = 90
   tilt_increment = 1

   [Times]
   start_time = "2023-05-20 12:00:00"
   end_time = "2023-06-01 12:00:00"

   [Location.LatitudeRange]
   latitude_start = "-80deg"
   latitude_end = "-45deg"
   increment = "1deg"

``min_tilt``
   Minimum tilt angle to evaluate (degrees from vertical).

``max_tilt``
   Maximum tilt angle to evaluate.

``tilt_increment``
   Step size for the search (smaller = more precise but slower).

Example
-------

.. code-block:: bash

   pass optimal-tilt my_config.toml

Output
------

Generates a plot showing power production vs. tilt angle, with the optimal
value highlighted. Saved to ``[plots].optimal_tilt``.
