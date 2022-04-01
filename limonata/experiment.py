from .limonata import Limonata, LimonataModel
from .historian import Historian, Plotter
from .labtime import labtime, clock

class Experiment:
	
    def __init__(self, connected = True, plot = True, twindow = 200, time = 500, dbfile = ':memory:', speedup = 1, synced = True, tol = 0.5):
        if (speedup != 1 or not synced) and connected:
            raise ValueError('The real Limonata can only run in real time.')
        
        self.connected = connected
        self.plot      = plot
        self.twindow   = twindow
        self.time      = time
        self.dbfile    = dbfile
        self.speedup   = speedup
        self.synced    = synced
        self.tol       = tol
        
        if synced:
            labtime.set_rate(speedup)
        
        self.lab       = None
        self.historian = None
        self.plotter   = None
    
    def __enter__(self):
        if self.connected:
            self.lab = Limonata()
        else:
            self.lab = LimonataModel(synced = self.synced)
        
        self.historian = Historian(self.lab.sources, dbfile = self.dbfile)
        
        if self.plot:
            self.plotter = Plotter(self.historian, twindow = self.twindow)
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        self.lab.close()
        self.historian.close()
        
    def clock(self):
        if self.synced:
            times = clock(self.time, tol = self.tol)
        else:
            times = range(self.time)
        
        for t in times:
            if self.plot:
                self.plotter.update(t)
            else:
                self.historian.update(t)
            if not self.synced:
                self.lab.update(t)
                
def runexperiment(function, *args, **kwargs):
    with Experiment(*args, **kwargs) as experiment:
        for t in experiment.clock():
            function(t, experiment.lab)
    return experiment
    