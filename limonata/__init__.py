from .limonata import Limonata
from .labtime import clock, labtime, setnow

def setup(connected = True, speedup = 1):

    if connected:
        lab = Limonata
        if speedup != 1:
            raise ValueError('The real lab must run in real time')
    else:
        print('LimonataModel')
        if speedup < 0:
            raise ValueError('Speedup must be positive.')

    labtime.set_rate(speedup)

    return lab

