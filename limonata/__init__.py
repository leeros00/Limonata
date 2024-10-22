from .reactor import Reactor, ReactorModel  # , diagnose

# from .historian import Historian, Plotter
# from .experiment import Experiment, runexperiment
from .timer import timer  # , setnow, clock
# from .version import __version__


def setup(connected=True, speedup=1):
    """Set up a reactor session with simple switching between real and model reactor

    The idea of this function is that you will do

    >>> reactor = setup(connected=True)

    to obtain a reactor class reference. If `connected=False` then you will
    receive a ReactorModel class reference. This allows you to switch between
    the model and the real reactor in your code easily.

    The speedup option can only be used when `connected=False` and is the
    ratio by which the reactor clock will be sped up relative to real time
    during the simulation.

    For example

    >>> reactor = setup(connected=False, speedup=2)

    will run the reactor clock at twice real time (which means that the whole
    simulation will take half the time it would if connected to a real device).
    """

    if connected:
        reactor = Reactor
        if speedup != 1:
            raise ValueError("The real reactor must run in real time")
    else:
        reactor = ReactorModel
        if speedup < 0:
            raise ValueError(
                "speedup must be positive. " "You passed speedup={}".format(speedup)
            )

    timer.set_rate(speedup)
    return reactor
