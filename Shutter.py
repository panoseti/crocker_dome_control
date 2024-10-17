#!/usr/bin/env python3

import serial
import serial.tools.list_ports
import datetime
import threading
import multiprocessing
import os


raise NotImplementedError('Automatic Shutter Control Not Implemented')



dome_device_file = '/dev/ttyUSB_DOME'


# Open serial port
ser = serial.Serial(dome_device_file, baudrate=9600, timeout=1)

def BatLabel():
    ser = serial.Serial(dome_device_file, baudrate=9600, timeout=1)
    ser.write(str.encode('RBV'))
    print ("Battery")
    ser.close()

def LOLabel():
    ser = serial.Serial(dome_device_file, baudrate=9600, timeout=1)
    ser.write(str.encode('LO'))
    print ("Lights On")
    ser.close()
   
    
def LoLabel():
    ser = serial.Serial(dome_device_file, baudrate=9600, timeout=1)
    ser.write(str.encode('Lo'))
    print ("Lights Off")
    ser.close()
    
def USOLabel():
    ser = serial.Serial(dome_device_file, baudrate=9600, timeout=1)
    ser.write(str.encode('USO'))
    print ("Upper Shutter Open")
    ser.close()
    
def USCLabel():
    ser = serial.Serial(dome_device_file, baudrate=9600, timeout=1)
    ser.write(str.encode('USC'))
    print ("Upper Shutter Close")
    ser.close()

def LSOLabel():
    ser = serial.Serial(dome_device_file, baudrate=9600, timeout=1)
    ser.write(str.encode('LSO'))
    print ("Lower Shutter Open")
    ser.close()

def LSCLabel():
    ser = serial.Serial(dome_device_file, baudrate=9600, timeout=1)
    ser.write(str.encode('LSC'))
    print ("Lower Shutter Close")
    ser.close()
    
def FLOLabel():
    ser = serial.Serial(dome_device_file, baudrate=9600, timeout=1)
    ser.write(str.encode('FLO'))
    print ("Floor Lights On")
    ser.close()

def FLoLabel():
    ser = serial.Serial(dome_device_file, baudrate=9600, timeout=1)
    ser.write(str.encode('FLo'))
    print ("Floor Lights Off")
    ser.close()    

def SFOLabel():
    ser = serial.Serial(dome_device_file, baudrate=9600, timeout=1)
    ser.write(str.encode('SFO'))
    print ("Seeing Fan On")
    ser.close()

def SFoLabel():
    ser = serial.Serial(dome_device_file, baudrate=9600, timeout=1)
    ser.write(str.encode('SFo'))
    print ("Seeing Fan Off")
    ser.close()

if __name__ == '__main__':
    from tkinter import *
    # import customtkinter
    from tkinter import ttk

    root = Tk()
    root.title('DOME')
    shutterLabel = Label(root, text="NOTICE", padx=50, pady=0).grid(row=0, column=0, columnspan=2)
    shutterLabel2 = Label(root, text="2 sec delay per selection", padx=0, pady=0).grid(row=1, column=0, columnspan=2)

    BatButton = Button(root, text=  "  Shutter Battery    ", padx=50,pady=20, command=BatLabel).grid(row=3, column=0, columnspan=2)

    LOButton = Button(root, text=  "  Dome Lights On    ", padx=60,pady=20, command=LOLabel).grid(row=4, column=0)
    LoButton = Button(root, text=  "  Dome Lights Off   ", padx=60,pady=20, command=LoLabel).grid(row=4, column=1)
    FLOButton = Button(root, text= "  Floor Lights On   ", padx=65,pady=20, command=FLOLabel).grid(row=6, column=0)
    FLoButton = Button(root, text= "  Floor Lights Off  ", padx=65,pady=20, command=FLoLabel).grid(row=6, column=1)
    SFOButton = Button(root, text= "  Seeing Fan On     ", padx=65,pady=20, command=SFOLabel).grid(row=8, column=0)
    SFoButton = Button(root, text= "  Seeing Fan Off    ", padx=65,pady=20, command=SFoLabel).grid(row=8, column=1)


    USOButton = Button(root, text= "Upper Shutter Open  ", padx=50,pady=20, command=USOLabel).grid(row=10, column=0)
    USCButton = Button(root, text= "Upper Shutter Close ", padx=50,pady=20, command=USCLabel).grid(row=10, column=1)
    LSOButton = Button(root, text= "Lower Shutter Open  ", padx=50,pady=20, command=LSOLabel).grid(row=12, column=0)
    LSCButton = Button(root, text= "Lower Shutter Close ", padx=50,pady=20, command=LSCLabel).grid(row=12, column=1)



    root.mainloop()
