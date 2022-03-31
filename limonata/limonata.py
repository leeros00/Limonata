# -*- coding: utf-8 -*-
"""
Created on Wed Mar 30 16:50:30 2022

@author: ltlee
"""
from __future__ import print_function
import time
import os
import serial
import random
from serial.tools import list_ports
from .labtime import labtime
from .version import __version__

sep = ' '

arduinos = [('USB VID:PID=1650:0613', 'Arduino Uno'),
            ('USB VID:PID=1A86:7523', 'NHduino'),
            ('USB VID:PID=2341:8036', 'Arduino Leonardo'),
            ('USB VID:PID=2A03', 'Arduino.org device'),
            ('USB VID:PID', 'unknown device'),]

#_firmwareurl = 
_connected = False


def clip(val, lower = 0, upper = 100):
    return max(lower, min(val, upper))

def command(name, argument, lower = 0, upper = 100):
    return name + sep + str(clip(argument, lower, upper))

def find_arduino(port = ''):
    comports = [tuple for tuple in list_ports.comports() if port in tuple[0]]
    
    for port, desc, hwid, in comports:
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
    
    def __init__(self, port = '', debug = False):
        global _connected
        self.debug = debug()
        print("Limonata version", __version__)
        self.port, self.arduino = find_arduino(port)
        
        if self.port is None:
            raise RuntimeError('No Arduino device found')
        
        try:
            self.connect(baud = 115200)
        except AlreadyConnectedError:
            raise
        except:
            try:
                _connected = False
                self.sp.close()
                self.connect(baud = 9600)
                print('Could not connect at high speed, but succeeded at low speed.')
                print('This could be from using old Limonata firmware.')
                print('New Arduino Limonata firmware available at:')
                #print(_firmwareurl)
            except:
                raise RuntimeError('Failed to connect.')
            
        self.sp.readline().decode('UTF-8')
        self.version = self.send_and_receive('VER')
        
        if self.sp.isOpen():
            print(self.arduino, 'connected on port', self.port, 'at', self.baud, 'baud')
            print(self.version + '.')
        
        labtime.set_rate(1)
        labtime.start()
        self._pumpP     = 100.0
        self._valveP    = 200.0
        self._agitatorP = 100.0
        #self.pumpQ(0)
        self.valveQ(100) # Initialize open, right?
        #self.agitatorQ(0)
        self.sources = [('F', self.scan),
                        ('T', None),
                        ('pumpQ', None),
                        ('valveQ', None),
                        ('agitatorQ', None)]
        
        def __enter__(self):
            return self
        
        def __exit__(self, exc_type, exc_value, traceback):
            self.close()
            return
        
        def connect(self, baud):
            global _connected
            
            if _connected:
                raise AlreadyConnectedError('You already have an open connection')
            
            _connected = True
            
            self.sp = serial.Serial(port = self.port, baudrate = baud, timeout = 2)
            time.sleep(2)
            self.pumpQ(0) # The pump fails is it isn't connected
            self.baud = baud
            
        def close(self):
            global _connected
            
            self.pumpQ(0)
            self.valveQ(100)
            self.agitatorQ(0)
            
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
        
        def send_and_receive(self, msg, convert = str):
            self.send(msg)
            return convert(self.receive())
        
        def LED(self, val = 100):
            return self.send_and_receive(command('LED', val), float)
        
        @property
        def T(self):
            return self.send_and_receive('T', float)
        
        @property
        def F(self):
            return self.send_and_receive('F', float)
        
        # pumpP
        @property
        def pumpP(self):
            return self._pumpP
        
        @pumpP.setter
        def pumpP(self, val):
            self._pumpP = self.send_and_receive(command('pumpP', val, 0, 255), float)
        
        # valveP
        @property
        def valveP(self):
            return self._valveP
        
        @valveP.setter
        def valveP(self, val):
            self._valveP = self.send_and_receive(command('valveP', val, 0, 255), float)
        
        # agitatorP
        @property
        def agitatorP(self):
            return self._agitatorP
        
        @agitatorP.setter
        def agitatorP(self, val):
            self._agitatorP = self.send_and_receive(command('agitatorP', val, 0, 255), float)
        
        def pumpQ(self, val = None):
            if val is None:
                msg = 'pumpR'
            else:
                msg = 'pumpQ' + sep + str(clip(val))
            return self.send_and_receive(msg, float)
        
        def valveQ(self, val = None):
            if val is None:
                msg = 'valveR'
            else:
                msg = 'valveQ' + sep + str(clip(val))
            return self.send_and_receive(msg, float)
        
        def agitatorQ(self, val = None):
            if val is None:
                msg = 'agitatorR'
            else:
                msg = 'agitatorQ' + sep + str(clip(val))
            return self.send_and_receive(msg, float)
        
        def scan(self):
            T = self.T
            F = self.F
            
            pumpQ     = self.pumpQ
            valveQ    = self.valveQ
            agitatorQ = self.agitatorQ
            return T, F, pumpQ, valveQ, agitatorQ
        
        pumpU     = property(fget = pumpQ, fset = pumpQ, doc = "Pump Flow Duty value")
        valveU    = property(fget = valveQ, fset = valveQ, doc = "Valve Duty value")
        agitatorU = property(fget = agitatorQ, fset = agitatorQ, doc = "Agitator Duty value")
   
    # Finish LimonataModel another day
    class LimonataModel(object):
        
        def __init__(self, port = '', debug = False, synced = True):
            self.debug = debug
            self.synced  = synced
            print("Limonata version", __version__)
            labtime.start()
            print('Simulated Limonata')