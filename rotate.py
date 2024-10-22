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

CLI_rotation_commands = ['left2sec', 'right2sec', 'left', 'right', 'stop', 'pos', 'test_auto_rot']
MAX_ROTATION_DURATION_SEC = 10
MIN_AZ_DIFF = 3

""" Auto move to a particular azimuth angle. """
# left 2 sec: -1, 360, 359
# right 2 sec: 361, 0
# "Right" increases the azimuth angle, "Left" decreases it.

def test_auto_rotate(ser):
    target_azimuth_angles = [30, 15, 45, 0]
    for target_az in target_azimuth_angles:
        initial_az = get_current_az_angle(ser)
        print('Initial azimuth angle: {0}, target_angle = {1}'.format(initial_az, target_az))
        final_az = auto_rotate_to_azimuth(ser, target_az)
        print(f'Az after auto: {final_az}')
    print('TEST DONE')


def auto_rotate_to_azimuth(ser: serial.Serial, target_azimuth_angle, tolerance=3):
    initial_azimuth_angle = get_current_az_angle(ser)
    if (initial_azimuth_angle is None) or not (-2 <= initial_azimuth_angle <= 362):
        raise ValueError('last_azimuth_angle must be between 0 and 362')

    # Deal with bug in azimuth reporting code
    if initial_azimuth_angle in [-1, 361]:
        initial_azimuth_angle = 1

    # Determine which direction requires the less rotation
    az_diff_rot_right = (target_azimuth_angle - initial_azimuth_angle) % 360
    az_diff_rot_left = (initial_azimuth_angle - target_azimuth_angle) % 360
    if abs(az_diff_rot_right) < abs(az_diff_rot_left):
        direction = 'right'
        max_rotation_degrees = az_diff_rot_right
    else:
        direction = 'left'
        max_rotation_degrees = az_diff_rot_left

    if max_rotation_degrees < tolerance:
        print(f'Target position within {tolerance} deg of target: diff = {max_rotation_degrees}')
        return initial_azimuth_angle
    # Start rotation
    print(f"STARTING DOME ROTATION {direction}")
    if direction == 'right':
        start_rotate_right(ser)
    elif direction == 'left':
        start_rotate_left(ser)
    # Wait until dome is at or close to target azimuth angle
    azimuth_angles = []
    current_azimuth_angle = initial_azimuth_angle

    def continue_rotation(current_azimuth_angle: float):
        """
        Rotate dome until:
         - the azimuth angle reported by the dome controller is within 2 degrees of requested value
         - rotation amount has exceeded the calculated rotation amount
         - rotation duration has exceeded MAX_ROTATION_DURATION_SEC
        """
        if direction == 'right':
            angular_diff = abs((target_azimuth_angle - current_azimuth_angle) % 360)
            angular_dist = abs((current_azimuth_angle - initial_azimuth_angle) % 360)
        else:
            angular_diff = abs((current_azimuth_angle - target_azimuth_angle) % 360)
            angular_dist = abs((initial_azimuth_angle - current_azimuth_angle) % 360)
        print(f"angular_diff = {angular_diff}, angular_dist = {angular_dist}")
        do_continue = not (angular_diff < tolerance)
        do_continue &= angular_dist < max_rotation_degrees
        return do_continue

    while continue_rotation(current_azimuth_angle):
        time.sleep(0.1)
        packet_data = ser.readline().decode('ascii')
        # An azimuth packet looks like "Azimuth = {NUM}". Ignore other packets
        if "az" not in packet_data.lower() and "rdp" not in packet_data.lower():
            continue
        # Ex: float("Azimuth = 19".lower().split("=")[1]) -> 19.0
        current_azimuth_angle = float(packet_data.lower().split("=")[1])
        print(f"Current azimuth angle: {current_azimuth_angle}")
        azimuth_angles.append(current_azimuth_angle)
    print('Stopping dome rotation')
    stop_rotation(ser, direction)
    # Must wait 3 seconds an observe no movement reports to verify that stop was successful.
    print("Verifying dome rotation has stopped...")
    time.sleep(2)
    time_since_stop = datetime.datetime.now(datetime.timezone.utc)
    # Clear movement reports during stop operation
    while ser.in_waiting > 0:
        packet_data = ser.readline().decode('ascii')
    time.sleep(2)
    # Should definitely have no movement packets here
    curr_time = datetime.datetime.now(datetime.timezone.utc)
    while (curr_time - time_since_stop).total_seconds() < 3:
        if ser.in_waiting != 0:
            packet_data = ser.readline().decode('ascii')
            # An azimuth packet looks like "Azimuth = {NUM}". Ignore other packets
            if "az" in packet_data.lower() or "rdp" in packet_data.lower():
                print(packet_data)
                print('WARNING: failed to stop dome rotation. Retrying...')
                stop_rotation(ser, direction)
                time_since_stop = datetime.datetime.now(datetime.timezone.utc)
        time.sleep(0.1)
        curr_time = datetime.datetime.now(datetime.timezone.utc)
    final_azimuth_angle = get_current_az_angle(ser)
    print('Dome rotation stopped')
    print(f"final azimuth angle: {final_azimuth_angle}")
    return final_azimuth_angle

def get_current_az_angle(ser: serial.Serial, listen_timeout = 10, return_on_first_az=True):
    time.sleep(2)
    ser.write(str.encode("RDP"))
    ser.flush()
    azimuth_angles = []
    start_time = datetime.datetime.now(datetime.timezone.utc)
    curr_time = datetime.datetime.now(datetime.timezone.utc)
    while (curr_time - start_time).total_seconds() < listen_timeout:
        curr_time = datetime.datetime.now(datetime.timezone.utc)
        if ser.in_waiting != 0:
            packet_data = ser.readline().decode('ascii')
            # An azimuth packet looks like "Azimuth = {NUM}". Ignore other packets
            if "az" not in packet_data.lower() and "rdp" not in packet_data.lower():
                continue
            # Ex: float("Azimuth = 19".lower().split("=")[1]) -> 19.0
            last_azimuth_angle = float(packet_data.lower().split("=")[1])
            azimuth_angles.append(last_azimuth_angle)
            if return_on_first_az:
                break
        time.sleep(0.1)
    if len(azimuth_angles) == 0:
        return None
    return azimuth_angles[-1]



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
    ser.flush()
    time.sleep(n)
    ser.write(str.encode('DLo'))
    ser.flush()


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
    ser.flush()
    time.sleep(n)
    ser.write(str.encode('DRo'))
    ser.flush()


""" Manually start & stop dome rotation """


def start_rotate_left(ser: serial.Serial):
    """
    Command dome to start rotating LEFT.

    NOTE: this rotation will continue indefinitely until you command the rotation to stop.
    :param ser: open serial connection to the dome controller.
    :raises SerialTimeoutException: if the command cannot be sent through the provided serial port
    """
    ser.write(str.encode('DLO'))
    ser.flush()


def start_rotate_right(ser: serial.Serial):
    """
    Command dome to start rotating RIGHT.

    NOTE: this rotation will continue indefinitely until you command the rotation to stop.
    :param ser: open serial connection to the dome controller.
    :raises SerialTimeoutException: if the command cannot be sent through the provided serial port
    """
    ser.write(str.encode('DRO'))
    ser.flush()


def stop_rotation(ser: serial.Serial, direction='both'):
    """
    Stop all dome rotation.

    :param ser: open serial connection to the dome controller.
    :param direction: either 'left', 'right', or 'both'
    :raises SerialTimeoutException: if the command cannot be sent through the provided serial port.
    """
    if direction == 'right':
        ser.write(str.encode('DRo'))
        ser.flush()
    elif direction == 'left':
        ser.write(str.encode('DLo'))
        ser.flush()
    else:
        ser.write(str.encode('DRo'))
        ser.flush()
        time.sleep(2)
        ser.write(str.encode('DLo'))
        ser.flush()


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
        elif cmd == 'pos':
            curr_az_angle = get_current_az_angle(ser)
            print(f'Current azimuth angle: {curr_az_angle}')
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
                time.sleep(2)
                stop_rotation(ser)
                raise ex


if __name__ == "__main__":
    rotation_cli_main()
