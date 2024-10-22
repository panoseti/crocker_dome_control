# Crocker Dome Control Script
Simple code for automatically controlling the Crocker dome 

# Setup
Install the `conda` package manager if it is not already, then run the following commands to setup the conda environment for this code.
```bash
conda create -n crocker_dome_control
conda install pyserial pandas numpy matplotlib seaborn jupyter
```
Before using any of the scripts, make sure to activate this new environment with `conda activate crocker_dome_control`

# Example Usage
The `gotoaz` command can be used to rotates the dome to a target azimuth position:
```bash
./rotate gotoaz -val 15  # Rotate dome so its azimuth is 15 degrees
```

TODO: make calls to gotoaz automatic and scheduled with an observing plan document.

# Obs Plan format
TODO

# Crocker Control Config JSON File
```json
{
    "update_interval_seconds": 600,
    "baudrate": 9600,
    "dome_controller_device_file": "/dev/ttyUSB_DOME",
    "obs_plan_dir": "obs_plans",
    "obs_plan_file": "SAMPLE_obsplan.csv"
}
```

