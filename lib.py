"""
Utility routines for the dome control program.

"""
import os
from pathlib import Path
import json

config_fname = 'crocker_control_config.json'
MAX_ROTATION_DURATION_SEC = 10
SERIAL_WRITE_TIMEOUT = 1

# Create
obs_plan_dir = Path('obs_plans')
os.makedirs(obs_plan_dir, exist_ok=True)

def load_config():
    with open(config_fname, 'r') as fp:
        return json.load(fp)