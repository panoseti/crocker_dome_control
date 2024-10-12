#!/usr/bin/env python

import argparse
import os
import sys
import time

import signal


from threading import Timer
import time

from datetime import datetime
import json
from pathlib import Path
import pandas as pd


dome_controller = {
    'device': '/dev/ttyUSB_DOME',

}
config_fname = 'crocker_control_config.json'

# Create
obs_plan_dir = Path('obs_plans')
os.makedirs(obs_plan_dir, exist_ok=True)

def load_config():
    with open(config_fname, 'r') as fp:
        return json.load(fp)

def interrupt_handler(sig, frame):
    if sig == signal.SIGINT:
        cleanup_and_exit()
    else:
        cleanup_and_exit()


def do_scheduled_movement():
    curr_time =  datetime.fromtimestamp(time.time())
    print("Started:", curr_time)


def sleep_until(target_time, verbose=False):
    current_time = time.time()
    remaining_time = target_time - current_time

    if remaining_time > 0:
        time.sleep(remaining_time)

def cleanup_and_exit():
    print('\nMAIN Exited')
    sys.exit(0)


def start(args):
    config = load_config()
    dome_controller_device = config['dome_controller_device']
    update_interval_seconds = config['update_interval_seconds']
    obs_plan_dir = config['obs_plan_dir']
    print('Started Updating')

    for i in range(1, 5):
        # Example usage
        target_time = time.time() + i  # Sleep until 5 seconds from now

        print('Scheduled: ', datetime.fromtimestamp(target_time), end='\r')
        sleep_until(target_time)
        print('Scheduled: ', datetime.fromtimestamp(target_time), end='\t')
        do_scheduled_movement()


if __name__ == '__main__':
    # Gracefully handle SIGINT
    signal.signal(signal.SIGINT, interrupt_handler)

    # create the top-level parser
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(required=False)

    # create parser for the init command
    parser_init = subparsers.add_parser('start',
                                        description='Start automatic dome rotation')
    parser_init.set_defaults(func=start)

    # Parse known args
    args, unknown = parser.parse_known_args()

    # If no subcommand was provided, insert the default
    if len(sys.argv) == 1:
        parser.print_help()
    else:
        # Parse arguments again with the default subcommand
        args = parser.parse_args()
        args.func(args)

    cleanup_and_exit()
