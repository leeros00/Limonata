from .limonata import Limonata, LimonataModel, diagnose
from .historian import Historian, Plotter
from .experiment import Experiment, runexperiment
from .labtime import clock, labtime, setnow
from .version import __version__

def setup(connected = True, speedup = 1):
    
    if connected:
        lab = Limonata
        if speedup != 1:
            raise ValueError('The real lab must run in real time.')
    else:
        lab = LimonataModel
        if speedup < 0:
            raise ValueError('speedup must be positive. '
                             'You passed speedup = {}'.format(speedup))
            
    labtime.set_rate(speedup)
    return lab