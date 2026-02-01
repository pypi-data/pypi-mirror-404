phase-space
===========

Perform phase space analysis of the power system.

.. click:: PASS.apps.phase_space:phase_space
   :prog: pass phase-space
   :nested: full

Description
-----------

This command performs a phase space analysis, exploring how power system
performance varies across multiple parameters simultaneously. This can reveal:

- Trade-offs between different design choices
- Regions of stable operation
- Parameter sensitivities

Example
-------

.. code-block:: bash

   pass phase-space my_config.toml

Output
------

Generates phase space plots showing parameter relationships.
