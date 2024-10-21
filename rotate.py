#!/usr/bin/env python3
# Adapted from Jeff Roark GUI code Rotation2.py by Jerome Maire (2024-08-30) with choice of actions using user command line.
# To rotate left for 2 seconds:
#   ./rotate.py left2sec
# To rotate right:
#   ./rotate.py right
# To stop the dome:
#   ./rotate.py stop

import datetime
import argparse
import time

import serial
import serial.tools.list_ports
from serial.serialutil import SerialTimeoutException

from lib import *

CLI_rotation_commands = ['left2sec', 'right2sec', 'left', 'right', 'stop', 'get_az', 'test_auto_rot']
MAX_ROTATION_DURATION_SEC = 10
MIN_AZ_DIFF = 3

""" Auto move to a particular azimuth angle. """
# left 2 sec: -1, 360, 359
# right 2 sec: 361, 0
# "Right" increases the azimuth angle, "Left" decreases it.

def test_auto_rotate(ser):
    target_azimuth_angles = [5]
    initial_az = get_azimuth_angle(ser)
    target_az = target_azimuth_angles[0]
    print('Initial azimuth angle: {0}, target_angle = {1}'.format(initial_az, target_az))
    final_az = auto_rotate_to_azimuth(ser, target_az, initial_az)
    print(f'Az after auto: {final_az}')


def auto_rotate_to_azimuth(ser: serial.Serial, target_azimuth_angle, initial_azimuth_angle: float, tolerance=2):
    if (initial_azimuth_angle is None) or not (-2 <= initial_azimuth_angle <= 362):
        raise ValueError('last_azimuth_angle must be between 0 and 362')

    # Deal with bug in azimuth reporting code
    if initial_azimuth_angle in [-1, 361]:
        initial_azimuth_angle = 1

    # Determine which direction requires the less rotation
    az_diff_rot_right = (target_azimuth_angle - initial_azimuth_angle) % 360
    az_diff_rot_left = (initial_azimuth_angle - target_azimuth_angle) % 360
    if abs(az_diff_rot_right) < abs(az_diff_rot_left):
        next_direction = 'right'
        max_rotation_degrees = az_diff_rot_right
    else:
        next_direction = 'left'
        max_rotation_degrees = az_diff_rot_left
    def continue_rotation(current_azimuth_angle: float):
        """
        Rotate dome until:
         - the azimuth angle reported by the dome controller is within 2 degrees of requested value
         - rotation amount has exceeded the calculated rotation amount
         - rotation duration has exceeded MAX_ROTATION_DURATION_SEC
        """
        curr_time = datetime.datetime.now(datetime.timezone.utc)
        do_continue = abs((target_azimuth_angle - initial_azimuth_angle) % 360) < 2
        do_continue &= abs((current_azimuth_angle - initial_azimuth_angle) % 360) < tolerance
        do_continue &= (curr_time - start_time).total_seconds() < MAX_ROTATION_DURATION_SEC
        return do_continue

    start_time = datetime.datetime.now(datetime.timezone.utc)
    azimuth_angles = []
    current_azimuth_angle = initial_azimuth_angle
    while continue_rotation(current_azimuth_angle):
        # Wait until packets arrive
        while continue_rotation(current_azimuth_angle) and ser.in_waiting == 0:
            time.sleep(0.01)
        packet_data = ser.readline().decode('ascii')
        # An azimuth packet looks like "Azimuth = {NUM}". Ignore other packets
        if "az" not in packet_data.lower():
            continue
        # Ex: float("Azimuth = 19".lower().split("=")[1]) -> 19.0
        current_azimuth_angle = float(packet_data.lower().split("=")[1])
        azimuth_angles.append(current_azimuth_angle)
    stop_rotation(ser)
    if len(azimuth_angles) == 0:
        return None
    return azimuth_angles[-1]

def listen_for_az(ser, listen_duration_sec = 5):
    """Seconds to listen for azimuth angle"""
    azimuth_angles = []
    start_time = datetime.datetime.now(datetime.timezone.utc)

    def continue_listen():
        curr_time = datetime.datetime.now(datetime.timezone.utc)
        return (curr_time - start_time).total_seconds() < listen_duration_sec

    while continue_listen():
        # Wait until packets arrive
        while continue_listen() and ser.in_waiting == 0:
            time.sleep(0.01)
        packet_data = ser.readline().decode('ascii')
        # An azimuth packet looks like "Azimuth = {NUM}". Ignore other packets
        if "az" not in packet_data.lower():
            continue
        # Ex: float("Azimuth = 19".lower().split("=")[1]) -> 19.0
        last_azimuth_angle = float(packet_data.lower().split("=")[1])
        azimuth_angles.append(last_azimuth_angle)
    if len(azimuth_angles) == 0:
        return None
    print(azimuth_angles)
    return azimuth_angles[-1]


def get_azimuth_angle(ser: serial.Serial):
    rotate_left_nsec_and_stop(2)
    time.sleep(2)
    rotate_right_nsec_and_stop(2)
    last_azimuth_angle = listen_for_az(ser)
    return last_azimuth_angle



""" Command dome to rotate for a fixed amount of time. """


def rotate_left_nsec_and_stop(ser: serial.Serial, n: int):
    """
    Rotate the dome left (counter-clockwise) for n seconds.

    :param ser: open serial port connection to the dome controller.
    :param n: number of seconds to rotate the dome left.
    :raises SerialTimeoutException: if the command cannot be sent through the provided serial port
    :raises ValueError: invalid rotation duration
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
    :raises SerialTimeoutException: if the command cannot be sent through the provided serial port
    :raises ValueError: invalid rotation duration
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
    :raises SerialTimeoutException: if the command cannot be sent through the provided serial port
    """
    ser.write(str.encode('DLO'))


def start_rotate_right(ser: serial.Serial):
    """
    Command dome to start rotating RIGHT.

    NOTE: this rotation will continue indefinitely until you command the rotation to stop.
    :param ser: open serial connection to the dome controller.
    :raises SerialTimeoutException: if the command cannot be sent through the provided serial port
    """
    ser.write(str.encode('DRO'))


def stop_rotation(ser: serial.Serial):
    """
    Stop all dome rotation.

    :param ser: open serial connection to the dome controller.
    :raises SerialTimeoutException: if the command cannot be sent through the provided serial port.
    """
    ser.write(str.encode('DRo'))
    time.sleep(2)
    ser.write(str.encode('DLo'))


""" CLI routines"""


def do_rotation_command(ser: serial.Serial, cmd: str):
    """
    Sends the command 'cmd' to the dome controller.

    :param cmd: command to send to the dome controller. Must be listed in CLI_rotation_commands.
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
        elif cmd == 'get_az':
            curr_az_angle = get_azimuth_angle(ser)
            print(f'get_azimuth_angle returned {curr_az_angle}')
        elif cmd == 'test_auto_rot':
            test_auto_rotate(ser)
        else:
            raise ValueError(f"Unknown rotation command {cmd}")
    except SerialTimeoutException as ste:
        print(f'ROTATION FAILED! Error message: {ste}')
        raise ste

    "Azimuth = {NUM HERE}"

def rotation_cli_main():
    parser = argparse.ArgumentParser(description="Control the DOME rotation via command line.")
    parser.add_argument('command', choices=CLI_rotation_commands, help="Choose a command to send to the DOME.")
    args = parser.parse_args()

    if not args.command:
        raise ValueError(f"No command was specified")
    elif args.command not in CLI_rotation_commands:
        raise ValueError(f"Unknown rotation command {args.command}")
    else:
        # Open serial port (as specified in the config file) then do requested command.
        config = load_config()
        dome_controller_device_file = config['dome_controller_device_file']
        baudrate = config['baudrate']
        with serial.Serial(
                dome_controller_device_file,
                baudrate=baudrate,
                timeout=1,
                write_timeout=SERIAL_WRITE_TIMEOUT
        ) as ser:
            try:
                do_rotation_command(ser, args.command)
            except Exception as ex:
                stop_rotation(ser)
                raise ex


if __name__ == "__main__":
    rotation_cli_main()
