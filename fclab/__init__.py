"""
Created on Tues March 23  7 15:06:51 2022

@author: ltlee
"""

from .fclab import FCLab, FCLabModel, diagnose
from .historian import Historian, Plotter
from .experiment import Experiment, runexperiment
from .labtime import clock, labtime, setnow
from .version import __version__


def setup(connected=True, speedup=1):
    """Set up a lab session with simple switching between real and model lab

    The idea of this function is that you will do

    >>> lab = setup(connected=True)

    to obtain a FCLab class reference. If `connected=False` then you will
    receive a FCLabModel class reference. This allows you to switch between
    the model and the real lab in your code easily.

    The speedup option can only be used when `connected=False` and is the
    ratio by which the lab clock will be sped up relative to real time
    during the simulation.

    For example

    >>> lab = setup(connected=False, speedup=2)

    will run the lab clock at twice real time (which means that the whole
    simulation will take half the time it would if connected to a real device).
    """

    if connected:
        lab = FCLab
        if speedup != 1:
            raise ValueError('The real lab must run in real time')
    else:
        lab = FCLabModel
        if speedup < 0:
            raise ValueError('speedup must be positive. '
                             'You passed speedup={}'.format(speedup))

    labtime.set_rate(speedup)
    return lab
