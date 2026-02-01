Installation
============

Requirements
------------

BI-PASS requires Python 3.8 or later. The following dependencies will be installed
automatically:

- `astropy <https://www.astropy.org/>`_ - Unit handling, time management, and coordinates
- `numpy <https://numpy.org/>`_ - Numerical computations
- `pandas <https://pandas.pydata.org/>`_ - Data manipulation
- `matplotlib <https://matplotlib.org/>`_ - Plotting and visualization
- `click <https://click.palletsprojects.com/>`_ - Command-line interface
- `pysolar <https://pysolar.org/>`_ - Solar position calculations
- `tqdm <https://tqdm.github.io/>`_ - Progress bars

Installation from Source
------------------------

Clone the repository and install in development mode:

.. code-block:: bash

   git clone https://github.com/your-org/PASS.git
   cd PASS
   pip install -e .

This installs BI-PASS in "editable" mode, meaning changes to the source code are
immediately reflected without reinstalling.

Verifying Installation
----------------------

After installation, verify that BI-PASS is working correctly:

.. code-block:: bash

   # Check that the CLI is available
   pass --help

   # Generate a sample configuration file
   pass make-config my_config.toml

You should see the help output listing all available commands.
