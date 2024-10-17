"""
Utility routines for the dome control program.

"""
import os
from pathlib import Path
import json
import pandas as pd
import numpy as np

config_fname = 'crocker_control_config.json'


MAX_ROTATION_DURATION_SEC = 10
SERIAL_WRITE_TIMEOUT = 1

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
    if set(obs_plan_df.columns) != {'utc_timestamp', 'rotation_duration_sec', 'direction'}:
        raise ValueError(f"obs_plan_df does not have the correct columns: {obs_plan_df.columns}")
    elif not np.all(obs_plan_df['rotation_duration_sec'] <= MAX_ROTATION_DURATION_SEC):
        raise ValueError("obs_plan_df contains rotation durations that exceed MAX_ROTATION_DURATION_SEC")
    elif not np.all(obs_plan_df['rotation_duration_sec'] < 0):
        raise ValueError("obs_plan_df contains negative rotation durations")
    elif not set(obs_plan_df['direction'].unique()) == {'left', 'right'}:
        raise ValueError("obs_plan_df contains invalid directions. Must only be 'left' or 'right'")


def load_obs_plan(obs_plan_path):
    obs_plan_loaded_df = pd.read_csv(obs_plan_path, index_col=0)
    obs_plan_loaded_df['utc_timestamp'] = pd.to_datetime(obs_plan_loaded_df['utc_timestamp'], utc=True)
    validate_obs_plan(obs_plan_loaded_df)
    return obs_plan_loaded_df
