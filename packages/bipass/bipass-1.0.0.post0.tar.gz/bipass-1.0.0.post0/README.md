# Balloon Instrumentation Power system Analysis Simulation Framework (BI-PASS)

This software package provides a framework for design and simulation of Long Duration Balloon payloads.

### To install this software package:

1. Download the Git repository:

    ```git clone https://gitlab.com/power-system-analysis-group/power-system-simulation-framework.git```

2. Set up the conda environment:
   1. Download python version 3.12 via miniconda using ```https://docs.anaconda.com/miniconda/```
   2. Source the .bashrc via ```source ~/.bashrc```
   3. Check that the conda install has worked via ```conda --version```
   4. Once you have installed conda open the PASS package in the terminal and enter
        ```conda create --name pass python=3.12```


3. Install the package with pip:
   1. Enter the pass environment via ```conda activate pass```
   2. Pip install pass via the two commands below:

   For use only:

    ```pip install .```

    For code development:

    ```pip install -e .```

4. Add run, status, and plots folders for outputs:
   1. ```mkdir run```
   This is the folder in which you will build the config files for different power system configurations.

   2. ```mkdir status```
   This is the folder where status files for simulated trajectories will be stored.
   3. ```cd run```

   4. ```mkdir plots```
   This is the folder where all of your plots will go.  To change the name of the plot, go into the config file and edit the plot name for that script.





 ### To run the software:

 1. Open the package in the terminal

 2. Enter the pass environment via ```conda activate pass```

 3. Enter into the run folder via ```cd run```

 4. Generate a default config file via ```pass make-config config_name.toml```

 5. Reference all the possible functions via ```pass --help```

 6. Run a command via ```pass command-name config_name.toml```
