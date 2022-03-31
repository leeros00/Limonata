# -*- coding: utf-8 -*-
"""
Created on Wed Mar 30 18:29:43 2022

@author: ltlee
"""
import time as time

class Labtime():
    
    def __init__(self):
        self._realtime = time.time()
        self._labtime  = 0
        self._rate     = 1
        self._running  = True
        self.lastsleep = 0
        
    @property
    def running(self):
        return self._running
    
    def time(self):
        if self.running:
            elapsed = time.time() - self._realtime
            return self._labtime + self._rate*elapsed
        else:
            return self._labtime
    
    def set_rate(self, rate = 1):
        if rate <= 0:
            raise ValueError("Labtime rates must positive.")
        self._labtime  = self.time()
        self._realtime = time.time()
        self._rate     = rate
        
    def get_rate(self):
        return self._rate
    
    def sleep(self, delay):
        self.lastsleep = delay
        
        if self._running:
            time.sleep(delay/self._rate)
        else:
            raise RuntimeWarning("Sleep is not valid when labtime is stopped.")
    
    def stop(self):
        self._labtime = self.time()
        self._realtime = time.time()
        self._running = False
        
    def start(self):
        self._realtime = time.time()
        self._running = True
        
    def reset(self, val = 0):
        self._labtime = val
        self._realtime = time.time()
        
labtime = Labtime()
    
def setnow(tnow = 0):
        labtime.reset(tnow)
        
def clock(period, step = 1, tol = float('inf'), adaptive = True):
    start = labtime.time()
    now = 0
        
    while round(now, 0) <= period:
        yield round(now, 2)
        if round(now) >= period:
            break
        
        elapsed = labtime.time() - (start + now)
        rate = labtime.get_rate()
            
        if (rate != 1) and adaptive:
            if elapsed > step:
                labtime.set_rate(0.8*rate*step/elapsed)
            elif (elapsed < 0.5*step) & (rate < 50):
                labtime.set_rate(1.25*rate)
        else:
            if elapsed > step + tol:
                message = ('Labtime clock lost synchronization with real time. '
                           'Step size was {} s, but {:.f} s elapsed '
                           '({:.2f} too long). Consider increasing step.')
                raise RuntimeError(message.format(step, elapsed, elapsed - step))
        labtime.sleep(step - (labtime.time() - start) % step)
        now = labtime.time() - start