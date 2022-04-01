# -*- coding: utf-8 -*-
"""
Created on Wed Mar 30 18:54:11 2022

@author: ltlee
"""
import datetime
import tornado
from .limonata import TCLab, TCLabModel
from .historian import Historian, Plotter
from .labtime import labtime, clock
from ipywidgets import Button, Label, FloatSlider, HBox, VBox, Checkbox, IntText

def actionbutton(description, action, disabled = True):
    button = Button(description = description, disabled = disabled)
    button.on_click(action)
    return button

def labelledvalue(label, value, units = ''):
    labelwidget = Label(value = label)
    valuewidget = Label(value = str(value))
    unitwidget = Label(value = units)
    box = HBox([labelwidget, valuewidget, unitwidget])
    return valuewidget, box

def slider(label, action = None, minvalue = 0, maxvalue = 100, disabled = True):
    sliderwidget = FloatSlider(description = label, min, minvalue, max = maxvalue)
    sliderwidget.disabled = disabled
    if action:
        sliderwidget.observe(action, names = 'value')
    return sliderwidget

class NotebookInteraction():
    def __init__(self):
        self.lab = None
        self.ui = None
    
    def update(self, t):
        raise NotImplementedError
        
    def connect(self, lab):
        self.lab = lab
        self.lab.connected = True
        
    def start(self):
        raise NotImplementedError
        
    def stop(self):
        raise NotImplementedError
        
    def disconnected(self):
        self.lab.connected = False

class SimpleInteraction(NotebookInteraction):
    def __init__(self):
        super().__init__()

        self.layout = (('pumpQ', 'valveQ', 'agitatorQ'),
                       ('F', 'T')) 
        
        self.pumpQ     = slider('pumpQ', self.action_pumpQ)
        self.valveQ    = slider('valveQ', self.action_valveQ)
        self.agitatorQ = slider('agitatorQ', self.action_agitatorQ)
        
        dc_objects = VBox([self.pumpQwidget, self.valveQwidget, self.agitatorQ])
        
        self.Fwidget, Fbox = labelledvalue('F:', 0, 'L/min')
        self.Twidget, Tbox = labelledvalue('T:', 0, '°C')
        
        sensors = VBox([Fbox, Tbox])
        
        self.ui = HBox([dc_objects, sensors])
        
    def update(self, t):
        self.Fwidget.value = '{:2.1f}'.format(self.lab.F)
        self.Twidget.value = '{:2.1f}'.format(self.lab.T)
        
    def connect(self, lab):
        super().connect(lab)
        self.sources = self.lab.sources
        
    def start(self):
        self.pumpQwidget.disabled     = False
        self.valveQwidget.disabled    = False
        self.agitatorQwidget.disabled = False
        
    def stop(self):
        self.pumpQwidget.disabled     = True
        self.valveQwidget.disabled    = True
        self.agitatorQwidget.disabled = True
        
    def action_pumpQ(self, change):
        self.lab.pumpQ(change['new'])
    
    def action_valveQ(self, change):
        self.lab.valveQ(change['new'])
    
    def action_agitatorQ(self, change):
        self.lab.agitatorQ(change['new'])

class NotebookUI:
    def __init__(self, Controller = SimpleInteraction):
        self.timer        = tornado.ioloop.PeriodicCallback(self.update, 1000)
        self.lab          = None
        self.plotter      = None
        self.historian    = None
        self.seconds      = 0
        self.firstsession = True
        
        self.usemodel = Checkbox(value = False, description = 'Use model')
        self.usemodel.observe(self.togglemodel, names = 'value')
        self.speedup  = slider('Speedup', minvalue = 1, maxvalue = 10)
        
        modelbox = HBox([self.usemodel, self.speedup])
        
        self.connect    = actionbutton('Connect', self.action_connect, False)
        self.start      = actionbutton('Start', self.action_start)
        self.stop       = actionbutton('Stop', self.action_stop)
        self.disconnect = actionbutton('Disconnect', self.action_disconnect)
        
        buttons = HBox([self.connect, self.start, self.stop, self.disconnect])
        
        self.timewidget, timebox       = labelledvalue('Timestamp:', 'No data')
        self.sessionwidget, sessionbox = labelledvalue('Session:', 'No data')
        
        statusbox = HBox([timebox, sessionbox])
        
        self.controller = Controller()
        
        self.gui = VBox([HBox([modelbox, buttons]), statusbox, self.controller.ui,])
        
        def update(self):
            self.timer.callback_time = 1000/self.speedup.value
            
            labtime.set_rate(self.speedup.value)
            
            self.timewidget.value = '{:.2f}'.format(labtime.time())
            self.controller.update(labtime.time())
            self.plotter.update(labtime.time())
        
        def togglemodel(self, change):
            self.speedup.disabled = not change['new']
            self.speedup.value = 1
            
        def action_start(self, widget):
            if not self.firstsession:
                self.historian.new_session()
            
            self.firstsession = False
            self.sessionwidget.value = str(self.historian.session)
            
            self.start.disabled = True
            self.stop.disabled = False
            self.disconnect.disabled = True
            
            self.controller.start()
            self.timer.start()
            labtime.reset()
            labtime.start()
            
        def action_stop(self, widget):
            self.timer.stop()
            
            labtime.stop()
            
            self.start.disabled = False
            self.stop.disabled = True
            self.disconnect.disabled = False
            self.controller.stop()
            
        def action_connect(self, widget):
            if self.usemodel.value:
                self.lab = LimonataModel()
            else:
                self.lab = Limonata()
            
            labtime.stop()
            labtime.reset()
            
            self.controller.connect(self.lab)
            self.historian = Historian(self.controller.sources)
            self.plotter   = Plotter(self.historian, twindow = 500, layout = self.controller.layout)
            
            self.usemodel.disabled   = True
            self.connect.disabled    = True
            self.start.disabled      = False
            self.disconnect.disabled = False
            
        def action_disconnect(self, widget):
            self.lab.close()
            
            self.controller.disconnect()
            
            self.usemodel.disabled   = False
            self.connect.disabled    = False
            self.disconnect.disabled = True
            self.start.disabled      = True