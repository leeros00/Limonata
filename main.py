import numpy as np
import pandas as pd
import limonata
import time
import pyqtgraph as pg
from pyqtgraph.Qt import QtWidgets, QtCore  # Updated to use QtWidgets

# generate step test data on Arduino
filename = 'limonata_dyn_data1.csv'

# heater steps
Qd = np.zeros(601)
Qd[10:200] = 80
Qd[200:400] = 20
Qd[400:] = 50

# Connect to Arduino
a = limonata.ReactorModel()
fid = open(filename, 'w')
fid.write('Time,H1,T1\n')
fid.close()

# Create PyQtGraph application
app = QtWidgets.QApplication([])  # Updated to use QtWidgets.QApplication
win = pg.GraphicsLayoutWidget(show=True)
win.setWindowTitle('Real-time Plotting')

# Create two plots: one for heater, one for temperature
heater_plot = win.addPlot(title="Heater Output (%)")
heater_curve = heater_plot.plot(pen='b')

win.nextRow()  # Move to the next row in the grid layout

temp_plot = win.addPlot(title="Temperature (degC)")
temp_curve = temp_plot.plot(pen='r')

# Set axes labels
heater_plot.setLabel('left', 'Heater (%)')
heater_plot.setLabel('bottom', 'Time (s)')
temp_plot.setLabel('left', 'Temperature (degC)')
temp_plot.setLabel('bottom', 'Time (s)')

# Initialize data containers for real-time updating
time_vals = []
heater_vals = []
temp_vals = []

# PyQtGraph timer for real-time updates
timer = QtCore.QTimer()

def update_plot():
    i = len(time_vals)
    if i >= 601:
        timer.stop()
        a.close()  # Close the connection when finished
        return
    
    # Set heater value and get temperature
    a.Q1(Qd[i])
    time_vals.append(i)
    heater_vals.append(Qd[i])
    temp_vals.append(a.T1)

    # Update the curves with new data
    heater_curve.setData(time_vals, heater_vals)
    temp_curve.setData(time_vals, temp_vals)

    # Write data to CSV
    with open(filename, 'a') as fid:
        fid.write(f'{i},{Qd[i]},{a.T1}\n')

    # Print to console
    print(f'Time: {i}, H1: {Qd[i]}, T1: {a.T1}')

# Set timer to update the plot every second
timer.timeout.connect(update_plot)
timer.start(1000)  # 1000 ms = 1 second

# Start the PyQtGraph application
app.exec_()  # Updated to use app.exec_()
