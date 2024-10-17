#!/usr/bin/env python3

import time
import serial

raise NotImplementedError('Serial Monitor Integration Not Implemented')

domeData=serial.Serial('/dev/ttyUSB_DOME', baudrate=9600, timeout=1)
time.sleep(1)

while True:
    while domeData.in_waiting==0:
        pass
    dataPacket=domeData.readline().decode('ascii')
    print(dataPacket)
    
