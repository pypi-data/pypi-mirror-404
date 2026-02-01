make-config
===========

Generate a template TOML configuration file.

.. click:: PASS.apps.make_config:make_config
   :prog: pass make-config
   :nested: full

Usage
-----

Create a new configuration file:

.. code-block:: bash

   pass make-config my_mission.toml

This copies the default configuration template to the specified path. You can then
edit this file to customize the simulation parameters.

Example
-------

.. code-block:: bash

   # Create a config file in the current directory
   pass make-config config.toml

   # Create a config file in a subdirectory
   pass make-config simulations/antarctic_flight.toml
