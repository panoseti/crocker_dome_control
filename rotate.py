#!/usr/bin/env python3
# Adapted from Jeff Roark GUI code Rotation2.py by Jerome Maire (2024-08-30) with choice of actions using user command line.
# To rotate left for 2 seconds:
#   ./rotate.py left2sec
# To rotate right:
#   ./rotate.py right
# To stop the dome:
#   ./rotate.py stop

import serial
import serial.tools.list_ports
import datetime
import argparse
import time
from serial.serialutil import SerialTimeoutException

from lib import *

available_rotation_commands = ['left2sec', 'right2sec', 'left', 'right', 'stop']


""" Command dome to rotate for a fixed amount of time. """


def rotate_left_nsec_and_stop(ser: serial.Serial, n: int):
    """
    Rotate the dome left (counter-clockwise) for n seconds.

    :param ser: open serial port connection to the dome controller.
    :param n: number of seconds to rotate the dome left.
    :raises SerialTimeoutException if the command cannot be sent through the provided serial port
    """
    if not 0 <= n < MAX_ROTATION_DURATION_SEC:
        raise ValueError('n was {0} must be between 0 and {1}'.format(n, MAX_ROTATION_DURATION_SEC))

    ser.write(str.encode('DLO'))
    time.sleep(n)
    ser.write(str.encode('DLo'))


def rotate_right_nsec_and_stop(ser: serial.Serial, n: int):
    """
    Rotate the dome right (clockwise) for n seconds.

    :param ser: open serial connection to the dome controller.
    :param n: number of seconds to rotate the dome left.
    :raises SerialTimeoutException if the command cannot be sent through the provided serial port
    """
    if not 0 <= n < MAX_ROTATION_DURATION_SEC:
        raise ValueError('n was {0} must be between 0 and {1}'.format(n, MAX_ROTATION_DURATION_SEC))
    ser.write(str.encode('DRO'))
    time.sleep(n)
    ser.write(str.encode('DRo'))


""" Manually start & stop dome rotation """


def start_rotate_left(ser: serial.Serial):
    """
    Command dome to start rotating LEFT.

    NOTE: this rotation will continue indefinitely until you command the rotation to stop.
    :param ser: open serial connection to the dome controller.
    :raise SerialTimeoutException if the command cannot be sent through the provided serial port
    """
    ser.write(str.encode('DLO'))


def start_rotate_right(ser: serial.Serial):
    """
    Command dome to start rotating RIGHT.

    NOTE: this rotation will continue indefinitely until you command the rotation to stop.
    :param ser: open serial connection to the dome controller.
    :raise SerialTimeoutException if the command cannot be sent through the provided serial port
    """
    ser.write(str.encode('DRO'))


def stop_rotation(ser: serial.Serial):
    """
    Stop all dome rotation.

    :param ser: open serial connection to the dome controller.
    :raise SerialTimeoutException if the command cannot be sent through the provided serial port.
    """
    ser.write(str.encode('DRo'))
    time.sleep(2)
    ser.write(str.encode('DLo'))


""" CLI routines"""


def do_rotation_command(ser: serial.Serial, cmd: str):
    """
    Sends the command 'cmd' to the dome controller.

    :param cmd: command to send to the dome controller. Must be listed in available_rotation_commands.
    """
    try:
        # 2-second dome rotation.
        if cmd == 'left2sec':
            rotate_left_nsec_and_stop(ser, 2)
        elif cmd == 'right2sec':
            rotate_right_nsec_and_stop(ser, 2)
        # Manually-controlled dome rotation
        elif cmd == 'left':
            start_rotate_left(ser)
        elif cmd == 'right':
            start_rotate_right(ser)
        elif cmd == 'stop':
            stop_rotation(ser)
        else:
            raise ValueError(f"Unknown rotation command {cmd}")
    except SerialTimeoutException as ste:
        print(f'ROTATION FAILED! Error message: {ste}')
        raise ste

def rotation_cli_main():
    parser = argparse.ArgumentParser(description="Control the DOME rotation via command line.")
    parser.add_argument('command', choices=available_rotation_commands, help="Choose a command to send to the DOME.")
    args = parser.parse_args()

    if not args.command:
        raise ValueError(f"No command was specified")
    elif args.command not in available_rotation_commands:
        raise ValueError(f"Unknown rotation command {args.command}")
    else:
        # Open serial port (as specified in the config file) then do requested command.
        config = load_config()
        dome_device_file = config['dome_controller_device']
        with serial.Serial(dome_device_file, baudrate=9600, timeout=1, write_timeout=SERIAL_WRITE_TIMEOUT) as ser:
            do_rotation_command(ser, args.command)


if __name__ == "__main__":
    rotation_cli_main()
