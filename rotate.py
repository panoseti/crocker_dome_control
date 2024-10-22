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
MAX_ROTATION_DURATION_SEC = 20
MIN_AZ_DIFF = 3

""" Auto move to a particular azimuth angle. """
# left 2 sec: -1, 360, 359
# right 2 sec: 361, 0
# "Right" increases the azimuth angle, "Left" decreases it.

def test_auto_rotate(ser):
    target_azimuth_angles = [20, 0, 20, 0]
    for target_az in target_azimuth_angles:
        initial_az = get_curr_az(ser)
        print('Initial azimuth angle: {0}, target_angle = {1}'.format(initial_az, target_az))
        final_az = auto_rotate_to_azimuth(ser, target_az)
        print()
        time.sleep(2)
    print('TEST DONE')


def get_continue_rotation_fn(target_az, initial_az, rot_dir, angle_diff_thresh, max_angular_dist):
    """
    Returns a function that returns True only if the dome should continue rotating
    Rotate dome until:
     - the azimuth angle reported by the dome controller is within 2 degrees of requested value
     - rotation amount has exceeded the calculated rotation amount
    """
    def continue_rotation(curr_az: float) -> bool:
        if rot_dir == 'right':
            angular_diff = abs((target_az - curr_az) % 360)
            angular_dist = abs((curr_az - initial_az) % 360)
        else:
            angular_diff = abs((curr_az - target_az) % 360)
            angular_dist = abs((initial_az - curr_az) % 360)
        # print(f"angular_diff = {angular_diff}, angular_dist = {angular_dist}")
        do_continue = not (angular_diff < angle_diff_thresh)
        do_continue &= angular_dist < max_angular_dist
        return do_continue
    return continue_rotation

def read_az_packet(ser: serial.Serial):
    """Read one packet from the serial port ser.
    :return: azimuth angle if this is a az packet and None otherwise.
    """
    if ser.in_waiting > 0:
        time.sleep(0.2)  # Wait for all data to arrive?
        try:
            packet_data = ser.readline()
            packet_data = packet_data.decode("ascii")
        except UnicodeDecodeError as ude:
            print(f'FAILED to read packet!\n\tUnicodeDecodeError: {ude},\n\tpacket_data: {packet_data}')
            return None
        # An azimuth packet looks like "Azimuth = {NUM}". Ignore other packets
        if "az" in packet_data.lower() or "rdp" in packet_data.lower():
            curr_az = float(packet_data.lower().split("=")[1])
            return curr_az


def auto_rotate_to_azimuth(ser: serial.Serial, target_az, az_error_tol=3):
    """

    :param ser: Open serial port to the dome controller device.
    :param target_az: azimuth angle the dome should be rotated to.
    :param az_error_tol: max angular error between target_az and final azimuth angle.
    :return: final azimuth angle.
    """
    initial_az = get_curr_az(ser)
    if (initial_az is None) or not (-2 <= initial_az <= 362):
        raise ValueError('last_azimuth_angle must be between 0 and 362')
    if initial_az in [-1, 361]:  # Deal with bug in azimuth reporting code
        initial_az = 1

    # Determine which direction requires the less rotation
    az_diff_rot_right = (target_az - initial_az) % 360
    az_diff_rot_left = (initial_az - target_az) % 360
    if abs(az_diff_rot_right) < abs(az_diff_rot_left):
        rot_dir = 'right'
        angular_dist = az_diff_rot_right
    else:
        rot_dir = 'left'
        angular_dist = az_diff_rot_left
    # Do no rotation if current dome position is close enough to target_az
    if angular_dist < az_error_tol:
        print(f'Target position within {az_error_tol} deg of target: diff = {angular_dist}')
        return initial_az

    # Get boolean-valued function controlling when to stop dome rotation
    az_error_to_stop_fast_rotation = 5  # Distance to stop rapid dome rotation and switch to small steps for precise alignment.
    continue_rotation = get_continue_rotation_fn(
        target_az, initial_az, rot_dir, az_error_to_stop_fast_rotation, angular_dist
    )

    # Start rotation
    print(f"Starting dome rotation: {rot_dir.upper()} {angular_dist} degrees")
    rot_duration = max(2, (angular_dist - az_error_to_stop_fast_rotation) / 2)
    print('Rotating dome for {0} seconds'.format(rot_duration))
    if rot_dir == 'right':
        rotate_right_nsec_and_stop(ser, rot_duration)
        # start_rotate_right(ser)
    elif rot_dir == 'left':
        rotate_left_nsec_and_stop(ser, rot_duration)
        # start_rotate_left(ser)

    # Wait until dome is at or close to target azimuth angle
    az_angles = []
    curr_az = initial_az
    while continue_rotation(curr_az):
        if ser.in_waiting > 0:
            az_data = read_az_packet(ser)
            if az_data is not None:
                curr_az = az_data
                az_angles.append(curr_az)
                print(f"Current azimuth angle: {curr_az}")
        time.sleep(0.1)
    print('Stopping dome rotation')
    stop_rotation(ser, rot_dir)
    ser.reset_input_buffer()
    # Wait 4 seconds and observe no movement reports to verify that stop was successful.
    print("Verifying dome rotation has stopped...")
    time_since_stop = datetime.datetime.now(datetime.timezone.utc)
    curr_time = datetime.datetime.now(datetime.timezone.utc)
    while (curr_time - time_since_stop).total_seconds() < 4:
        while ser.in_waiting > 0:
            az_data = read_az_packet(ser)
            if az_data is not None:
                print('\tWARNING: failed to stop dome rotation. Retrying...')
                stop_rotation(ser, rot_dir)
                ser.reset_input_buffer()
                time_since_stop = datetime.datetime.now(datetime.timezone.utc)
                curr_az = az_data
                az_angles.append(curr_az)
                print(f"Current azimuth angle: {curr_az}")
        time.sleep(0.1)
        curr_time = datetime.datetime.now(datetime.timezone.utc)
    final_azimuth_angle = get_curr_az(ser)
    print('Dome rotation stopped')
    print(f"Final azimuth angle: {final_azimuth_angle}")
    return final_azimuth_angle

def get_curr_az(ser: serial.Serial, listen_timeout = 10, return_on_first_az=True):
    """Queries the dome controller and returns its current azimuth angle."""
    ser.write(str.encode("RDP"))
    az_angles = []
    start_time = datetime.datetime.now(datetime.timezone.utc)
    curr_time = datetime.datetime.now(datetime.timezone.utc)
    while (curr_time - start_time).total_seconds() < listen_timeout:
        curr_time = datetime.datetime.now(datetime.timezone.utc)
        if ser.in_waiting > 0:
            az_data = read_az_packet(ser)
            if az_data is not None:
                curr_az = az_data
                az_angles.append(curr_az)
                if return_on_first_az:
                    break
        time.sleep(0.1)
    if len(az_angles) == 0:
        return None
    return az_angles[-1]



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


def stop_rotation(ser: serial.Serial, direction='both'):
    """
    Stop all dome rotation.

    :param ser: open serial connection to the dome controller.
    :param direction: either 'left', 'right', or 'both'
    :raises SerialTimeoutException: if the command cannot be sent through the provided serial port.
    """
    if direction == 'right':
        ser.write(str.encode('DRo'))
        time.sleep(2)
    elif direction == 'left':
        ser.write(str.encode('DLo'))
        time.sleep(2)
    else:
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
        elif cmd == 'pos':
            curr_az_angle = get_curr_az(ser)
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
                time.sleep(2)
                do_rotation_command(ser, args.command)
            except Exception as ex:
                time.sleep(2)
                stop_rotation(ser)
                raise ex


if __name__ == "__main__":
    rotation_cli_main()
