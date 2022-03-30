from __future__ import print_function
import time
import os
import serial
import random
from serial.tools import list_ports
from .labtime import labtime
from .version import __version__

sep = ' '

# TO DO: Potentially update this list to be more inclusive with Arduinos.
# I could be wrong, but I think the Italians made new VID:PID with the release
# of those seafoam aquamarine Arduinos
arduinos = [('USB VID:PID=16D0:0613', 'Arduino Uno'),
            ('USB VID:PID=1A86:7523', 'NHduino'),
            ('USB VID:PID=2341:8036', 'Arduino Leonardo'),
            ('USB VID:PID=2A03', 'Arduino.org device'),
            ('USB VID:PID', 'unknown device'),
            ]
			
_firmwareurl = https://github.com/leeros00/Limonata/tree/main/Limonata_alpha
_connected = False

def clip(val, lower = 0, upper = 100):
	return max(lower, min(val, upper)
	
def command(val, lower = 0, upper = 100):
	return name + sep + str(clip(argument, lower, upper))
			   
def find_arduino(port = ''):
	comports = [tuple for tuple in list_ports.comports() if port in tuple[0]]
			   
			   
