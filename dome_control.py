#!/usr/bin/env python
"""
Command-line interface for starting and stopping automatic Crocker Dome movements.
"""

import argparse
import os
import sys
import time
import json
from pathlib import Path
import signal
import time

import datetime
import pandas as pd
import numpy as np
import serial
import serial.tools.list_ports

from lib import *
from rotate import rotate_left_nsec_and_stop, rotate_right_nsec_and_stop, stop_rotation

def interrupt_handler(sig, frame):
    if sig == signal.SIGINT:
        cleanup_and_exit()
    else:
        cleanup_and_exit()

def do_scheduled_rotation(action, device_file):
    """
    Sends the rotation ``action`` to the dome controller ``device_file``

    :param action: row from the obs_plan_df DataFrame describing the movement parameters.
    :param device_file:
    :return: True if successful, False otherwise.
    """
    next_direction = action['direction']
    next_rotation_duration = action['rotation_duration_sec']
    now = datetime.datetime.now(datetime.timezone.utc)
    print(f"\tRotating {next_direction.upper():>7} for {next_rotation_duration:>3}s @\t{now}\n")
    try:
        with serial.Serial(device_file, baudrate=9600, timeout=1, write_timeout=SERIAL_WRITE_TIMEOUT) as ser:
            if next_direction.lower() == 'left':
                rotate_left_nsec_and_stop(ser, next_rotation_duration)
            if next_direction.lower() == 'right':
                rotate_right_nsec_and_stop(ser, next_rotation_duration)
        return True
    except SERIAL_WRITE_TIMEOUT:
        return False


def sleep_until_scheduled_time(scheduled_time: datetime.datetime):
    """
    Sleep the current thread until the scheduled_time. Scheduling error is typically around 5ms.

    :param scheduled_time: UTC datetime object of time to sleep until
    :return: False if the sleep deadline has passed; True otherwise
    """
    now = datetime.datetime.now(datetime.timezone.utc)
    seconds_until_scheduled_time = (scheduled_time - now).total_seconds()
    if seconds_until_scheduled_time < 0:  # in case of an unexpectedly long delay and action deadline has passed
        print(f'WARNING: MOVE DEADLINE PASSED BY {seconds_until_scheduled_time}')
        return False
    print(f'\tSleeping {seconds_until_scheduled_time:>12.5}s until \t{scheduled_time}')
    time.sleep(seconds_until_scheduled_time)
    return True

def start(args):
    config = load_config()
    dome_controller_device_file = config['dome_controller_device_file']
    # update_interval_seconds = config['update_interval_seconds']

    obs_plan_dir = Path(config['obs_plan_dir'])
    os.makedirs(obs_plan_dir, exist_ok=True)
    obs_plan_df = load_obs_plan(obs_plan_dir / config['obs_plan_file'])

    print('Started Updating')
    now = datetime.datetime.now(datetime.timezone.utc)
    obs_plan_df = obs_plan_df.sort_values(by='utc_timestamp')
    scheduled_after_now = obs_plan_df[obs_plan_df['utc_timestamp'] >= now]

    try:
        if len(scheduled_after_now) > 0:
            for idx in scheduled_after_now.index:
                next_action = scheduled_after_now.loc[idx]
                scheduled_time = next_action['utc_timestamp']

                print(f'Movement {idx + 1:>7} of {len(obs_plan_df)}:')
                valid_sleep = sleep_until_scheduled_time(scheduled_time)
                if not valid_sleep:
                    continue
                do_scheduled_rotation(next_action, dome_controller_device_file)



            print('All movements completed')
        else:
            print('No scheduled actions after the current time')
    finally:
        cleanup_and_exit()



def cleanup_and_exit():
    print('\nExited')


if __name__ == '__main__':
    # Gracefully handle SIGINT
    signal.signal(signal.SIGINT, interrupt_handler)

    # create the top-level parser
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(required=False)

    # create parser for the init command
    parser_init = subparsers.add_parser('start', description='Start automatic dome rotation')
    parser_init.add_argument()
    parser_init.set_defaults(func=start)

    args, unknown = parser.parse_known_args()

    # If no subcommand was provided, insert the default
    if len(sys.argv) == 1:
        parser.print_help()
    else:
        # Parse arguments again with the default subcommand
        args = parser.parse_args()
        args.func(args)

    cleanup_and_exit()
