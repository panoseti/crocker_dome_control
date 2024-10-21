"""
Utility routines for the dome control program.

"""
import os
from pathlib import Path
import json
import pandas as pd
import numpy as np

config_fname = 'crocker_control_config.json'



SERIAL_WRITE_TIMEOUT = 1

NUM_RETRY_ATTEMPTS = 10
RETRY_INTERVAL_SEC = 10

# Create


def load_config():
    with open(config_fname, 'r') as fp:
        return json.load(fp)

def validate_obs_plan(obs_plan_df: pd.DataFrame):
    """
    Check that obs_plan_df has the form we expect
    :param obs_plan_df:
    :return: None iff obs_plan_df passes all validation checks.
    """
    valid_params = {
        'columns': {'utc_timestamp', 'rotation_duration_sec', 'direction'},
        'directions': {'left', 'right'}
    }
    if set(obs_plan_df.columns) != valid_params['columns']:
        raise ValueError(f"obs_plan_df does not have the correct columns: {obs_plan_df.columns}")
    elif not np.all(obs_plan_df['rotation_duration_sec'] <= MAX_ROTATION_DURATION_SEC):
        raise ValueError("obs_plan_df contains rotation durations that exceed MAX_ROTATION_DURATION_SEC")
    elif np.any(obs_plan_df['rotation_duration_sec'] < 0):
        raise ValueError("obs_plan_df contains negative rotation durations")
    elif not set(obs_plan_df['direction'].unique()) == valid_params['directions']:
        invalid_directions = [d for d in obs_plan_df['direction'].unique() if d not in valid_params['directions']]
        raise ValueError(f"obs_plan_df contains invalid directions: {invalid_directions}. Must only be 'left' or 'right'")


def load_obs_plan(config):
    obs_plan_dir = Path(config['obs_plan_dir'])
    os.makedirs(obs_plan_dir, exist_ok=True)
    obs_plan_path = obs_plan_dir / config['obs_plan_file']

    obs_plan_loaded_df = pd.read_csv(obs_plan_path, index_col=0)
    obs_plan_loaded_df['utc_timestamp'] = pd.to_datetime(obs_plan_loaded_df['utc_timestamp'], utc=True)
    obs_plan_loaded_df = obs_plan_loaded_df.sort_values(by='utc_timestamp')
    validate_obs_plan(obs_plan_loaded_df)
    return obs_plan_loaded_df
