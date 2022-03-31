# -*- coding: utf-8 -*-
"""
Created on Wed Mar 30 18:54:11 2022

@author: ltlee
"""
import datetime
import tornado
from .limonata import Limonata, LimonataModel
from .labtime import labtime, clock
from ipywidgets import Button, Label, FloatSlider, HBox, VBox, Checkbox, IntText

def actionbutton(description, action, disabled = True):
    button = Button(description = description, disabled = disabled)
    button.on_click(action)
    return button

def labelledvalue(label, value, units = ''):
    labelwidget = Label(value = label)
    #valuewidget = 