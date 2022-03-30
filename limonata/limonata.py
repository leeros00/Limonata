from __future__ import print_function
import time
import os
import serial
import random
from serial.tools import list_ports
from .labtime import labtime
from .version import __version__

sep = ' '

arduinos = [('USB VID:PID=16D0:0613', 'Arduino Uno'),
            ('USB VID:PID=1A86:7523', 'NHduino'),
            ('USB VID:PID=2341:8036', 'Arduino Leonardo'),
            ('USB VID:PID=2A03', 'Arduino.org device'),
            ('USB VID:PID', 'unknown device'),
            ]
			
_firmwareurl = https://github.com/leeros00/Limonata/tree/main/Limonata_alpha
_connected = False


def clip(val, lower = 0, upper = 100)
	"""Limit value to be between lower and upper limits"""
	return max(lower, min(val, upper)
	
def 