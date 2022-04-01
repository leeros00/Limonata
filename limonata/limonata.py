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

_firmwareurl = 'https://github.com/leeros00/Limonata/tree/main/Limonata_alpha'
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
        self.debug  = debug
        self.synced = synced
        print("Limonata version", __version__)
        labtime.start()
        print('Simulated Limonata')
############ TO DO: Change for Limonata ######################################
        self.Ta = 0
        self.TA = 21                  # ambient temperature
        self.tstart = labtime.time()  # start time
        self.tlast = self.tstart      # last update time
        self._pumpP = 200.0              # max power heater 1
        self._valveP = 255.0              # max power heater 2
        self._agitatorP = 100.0              # max power heater 2
        self._pumpQ = 0                  # initial heater 1
        self._valveQ = 0
        self._agitatorQ = 0                  # initial heater 2
        self._F = self.Ta            # temperature thermister 1
        self._T = self.TA            # temperature thermister 2
        self._H1 = self.Ta            # temperature heater 1
        self._H2 = self.Ta            # temperature heater 2
        self.maxstep = 0.2            # maximum time step for integration
        self.sources = [('F', self.scan),
                        ('T', None),
                        ('pumpQ', None),
                        ('valveQ', None),
                        ('agitatorQ', None),
                        ]
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
        return
    
    def close(self):
        self.pumpQ(0)
        self.valveQ(0)
        self.agitatorQ(0)
        print('Limonata Model disconnected successfully.')
        
    def LED(self, val = 100):
        self.update()
        return clip(val)
    
    @property
    def F(self):
        self.update()
        return self.measurement(self._F)
    
    @property
    def T(self):
        self.update()
        return self.measurement(self._T)
    
    @property
    def pumpP(self):
        self.update()
        return self._pumpP
    
    @pumpP.setter
    def pumpP(self, val):
        self.update()
        self._pumpP = clip(val, 0, 255)
        
    @property
    def valveP(self):
        self.update()
        return self._valveP
    
    @valveP.setter
    def valveP(self, val):
        self.update()
        self._valveP = clip(val, 0, 255)
        
    @property
    def agitatorP(self):
        self.update()
        return self._valveP
    
    @agitatorP.setter
    def agitatorP(self, val):
        self.update()
        self._agitatorP = clip(val, 0, 255)
        
    def pumpQ(self, val = None):
        self.update()
        if val is not None:
            self._pumpQ = clip(val)
        return self._pumpQ
    
    def valveQ(self, val = None):
        self.update()
        if val is not None:
            self._valveQ = clip(val)
        return self._valveQ
    
    def agitatorQ(self, val = None):
        self.update()
        if val is not None:
            self._agitatorQ = clip(val)
        return self._agitatorQ
    
    def scan(self):
        self.update()
        return (self.measurement(self._F),
                self.measurement(self._T),
                self._pumpQ,
                self._valveQ,
                self._agitatorQ)
    
    pumpU     = property(fget = pumpQ, fset = pumpQ, doc = "Pump value")
    valveU    = property(fget = valveQ, fset = valveQ, doc = "Valve value")
    agitatorU = property(fget = agitatorQ, fset = agitatorQ, doc = "Agitator value")
    
    def quantize(self, T):
        return max(-50, min(132.2, T - T % 0.3223))
    
    def measurement(self, T):
        return self.quantize(T + random.normalvariate(0, 0.043))
    
    def update(self, t = None):
        if t is None:
            if self.synced:
                self.tnow = labtime.time() - self.tstart
            else:
                return
        else:
            self.tnow = t
        
        teuler = self.tlast
        # TO DO: Ask Dr. Hedengren what this thing actually does
        while teuler < self.tnow:
            dt = min(self.maxstep, self.tnow - teuler)
            #DeltaTaH1 = self.Ta - self._H1
            #DeltaTaH2 = self.Ta - self._H2
            #DeltaT12 = self.H1 - self._H1
            #dF = self._P1*self._Q1/5720 + DeltaTaH1/20 - DeltaT12/100
            #dT = self._P2*self._Q2/5720 + DeltaTaH2/20 - DeltaT12/100
            #dT1 = (self._H1 - self._T1)/140
            #dT2 = (self._H2 - self._T2)/140
            
            #self._H1 += dt*dH1
            #self._H2 += dt*dH2
            #self._T1 += dt*dT1
            #self._T2 += dt*dT2
            
            teuler += dt
            
        self.tlast = self.tnow
        
def diagnose(port = ''):
    def countdown(t = 10):
        for i in reversed(range(t)):
            print('\r' + "Countdown: {0:d}  ".format(i), end='', flush=True)
            time.sleep(1)
        print()
        
    def heading(string):
        print()
        print(string)
        print('-'*len(string))
        
    heading('Checking connection')
    
    if port:
        print('Looking for Arduino on {} ...'.format(port))
    else:
        print('Looking for Arduino on any port...')
    comport, name = find_arduino(port = port)
    
    if comport is None:
        print('No known Arduino was found in the ports listed above.')
        return
    
    print(name, 'found on port', comport)
    
    heading('Testing Limonata object in debug mode')
    
    with Limonata(port = port, debug = True) as lab:
        print('Reading flow rate')
        print(lab.F)
        
    heading('Testing Limonata functions')
    
    with Limonata(port = port) as lab:
        print('Testing LED. Should turn on for 10 seconds.')
        lab.LED(100)
        countdown()
        
        print()
        print('Reading flow rate and temperatures')
        F = lab.F
        T = lab.T
        print('F = {} L/min, T = {} °C'.format(F, T))
        
        print()
        print('Writing fractional value to DC objects...')
        
        try:
            pumpQ = lab.pumpQ(0.5)
        except:
            pumpQ = -1.0
        print('We wrote pumpQ = 0.5, and read back pumpQ =', pumpQ)
        
        if pumpQ != 0.5:
            print("Your Limonata firmware version ({}) doesn't support"
              "fractional DC object values.".format(lab.version))
            print("You need to upgrade to at least version 1.4.0 for this:")
            print(_firmwareurl)
        
        print()
        print('We will now turn on the heaters, wait 30 seconds '
              'and see if the temperatures have gone up. ')
        lab.pumpQ(100)
        lab.valveQ(100)
        lab.agitatorQ(100)
        countdown(30)
        
        print()
        
        #def tempcheck(name, T_initial, T_final):
            #print('{} started a {} °C and went to {} °C'
                  #.format(name, T_initial, T_final))
            #if T_final - T_initial < 0.8:
                #print('The temperature went up less than expected.')
                #print('Check the heater power supply.')
        
        #T1_final = lab.T1
        #T2_final = lab.T2

        #tempcheck('T1', T1, T1_final)
        #tempcheck('T2', T2, T2_final)
        
        print()
        heading("Throughput check")
        print("This part checks how fast your unit is")
        print("We will read flow rate as fast as possible")
        
        start = time.time()
        n = 0
        while time.time() - start < 10:
            elapsed = time.time() - start + 0.0001  # avoid divide by zero
            F = lab.F
            n += 1
            print('\rTime elapsed: {:3.2f} s.'
                  ' Number of reads: {}.'
                  ' Sampling rate: {:2.2f} Hz'.format(elapsed, n, n/elapsed),
                  end = '')

        print()

    print()
    print('Diagnostics complete')