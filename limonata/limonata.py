from __future__ import print_function
import time
import os
import random
import serial
from serial.tools import list_ports
from .labtime import labtime

sep = ' '  # command/value separator in Limonata firmware

arduinos = [('USB VID:PID=16D0:0613', 'Arduino Uno'),
            ('USB VID:PID=1A86:7523', 'NHduino'),
            ('USB VID:PID=2341:8036', 'Arduino Leonardo'),
            ('USB VID:PID=2A03', 'Arduino.org device'),
            ('USB VID:PID', 'unknown device'),
            ]

_connected = False


def clip(val, lower=0, upper=100):
    """Limit value to be between lower and upper limits"""
    return max(lower, min(val, upper))


def command(name, argument, lower=0, upper=100):
    """Construct command to TCLab-sketch."""
    return name + sep + str(clip(argument, lower, upper))


def find_arduino(port=''):
    """Locates Arduino and returns port and device."""
    comports = [tuple for tuple in list_ports.comports() if port in tuple[0]]
    for port, desc, hwid in comports:
        for identifier, arduino in arduinos:
            if hwid.startswith(identifier):
                return port, arduino
    print('--- Serial Ports ---')
    for port, desc, hwid in list_ports.comports():
        print(port, desc, hwid)
    return None, None


class AlreadyConnectedError(Exception):
    pass


class Limonata(object):

    def __init__(self, port='', debug=False):
        self.sp = None
        self.baud = None
        global _connected
        self.debug = debug
        print('Limonata version 0.0.0')
        self.port, self.arduino = find_arduino(port)
        if self.port is None:
            raise RuntimeError('No Arduino device found.')
        try:
            self.connect(baud=115200)
        except AlreadyConnectedError:
            raise
        except:
            try:
                _connected = False
                self.sp.close()
                self.connect(baud=9600)
                print('Could not connect at high speed, but succeeded at low speed.')
            except:
                raise RuntimeError('Failed to connect.')
        self.sp.readline().decode('UTF-8')
        self.version = self.send_and_receive('VER')
        if self.sp.isOpen():
            print(self.arduino, 'connected on port', self.port, 'at', self.baud, 'baud.')

        labtime.set_rate(1)
        labtime.start()
        self._P = 200.0
        self.Q(0)
        self.sources = [('F', self.scan), ('Q', None)]

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
        return

    def connect(self, baud):
        """Establish a connection to the arduino
        baud: baud rate"""
        global _connected

        if _connected:
            raise AlreadyConnectedError('You already have an open connection')

        _connected = True

        self.sp = serial.Serial(port=self.port, baudrate=baud, timeout=2)
        time.sleep(2)
        self.Q(0)  # fails if not connected
        self.baud = baud

    def close(self):
        global _connected

        self.Q(0)
        self.send_and_receive('X')
        self.sp.close()
        _connected = False

        print('Limonata disconnected successfully.')

        return

    def send(self, msg):
        self.sp.write((msg + '\r\n').encode())

        if self.debug:
            print('Sent: "' + msg + '"')

        self.sp.flush()

    def receive(self):
        msg = self.sp.readline().decode('UTF-8').replace('\r\n', '')

        if self.debug:
            print('Return: "' + msg + '"')

        return msg

    def send_and_receive(self, msg, convert=str):
        self.send(msg)

        return convert(self.receive())

    @property
    def F(self):
        return self.send_and_receive('F', float)

    @property
    def P(self):
        return self._P

    @P.setter
    def P(self, val):
        self._P = self.send_and_receive(command('P', val, 0, 255), float)

    def Q(self, val=None):
        if val is None:
            msg = 'R'
        else:
            msg = 'Q' + sep + str(clip(val))

        return self.send_and_receive(msg, float)

    def scan(self):
        F = self.F
        Q = self.Q()

        return F, Q

    # Maybe add properties like TCLab? probably not necessary...
