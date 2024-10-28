import numpy as np
import time
import matplotlib.pyplot as plt
import random
import json
# get gekko package with:
#   pip install gekko
from gekko import GEKKO
# get limonata package with:
#   pip install limonata
from limonata.reactor import Reactor

# Connect to Arduino
a = Reactor()

# Make an MP4 animation?
make_mp4 = False
if make_mp4:
    import imageio  # required to make animation
    import os
    try:
        os.mkdir('./figures')
    except:
        pass

# Final time
tf = 10 # min
# number of data points (every 3 seconds)
n = tf * 20 + 1

# Percent Heater (0-100%)
QPs = np.zeros(n)
QHs = np.zeros(n)

# Temperatures (degC)
Fm = a.F * np.ones(n)
Tm = a.T * np.ones(n)
# Temperature setpoints
Fsp = Fm[0] * np.ones(n)
Tsp = Tm[0] * np.ones(n)

# Heater set point steps about every 150 sec
Fsp[3:] = 40.0
Tsp[40:] = 30.0
Fsp[80:] = 32.0
Tsp[120:] = 35.0
Fsp[160:] = 45.0

#########################################################
# Initialize Model
#########################################################
m = GEKKO(name='limonata-mpc',remote=False)

# with a local server
#m = GEKKO(name='limonata-mpc',server='http://127.0.0.1',remote=True)

# Control horizon, non-uniform time steps
m.time = [0,3,6,10,14,18,22,27,32,38,45,55,65, \
          75,90,110,130,150]

# Parameters from Estimation
K1 = m.FV(value=0.607)
K2 = m.FV(value=0.293)
K3 = m.FV(value=0.24)
tau12 = m.FV(value=192)
tau3 = m.FV(value=15)

# don't update parameters with optimizer
K1.STATUS = 0
K2.STATUS = 0
K3.STATUS = 0
tau12.STATUS = 0
tau3.STATUS = 0

# Manipulated variables
QP = m.MV(value=0,name='QP')
QP.STATUS = 1  # manipulated
QP.FSTATUS = 0 # not measured
QP.DMAX = 20.0
QP.DCOST = 0.1
QP.UPPER = 100.0
QP.LOWER = 0.0

QH = m.MV(value=0,name='QH')
QH.STATUS = 1  # manipulated
QH.FSTATUS = 0 # not measured
QH.DMAX = 30.0
QH.DCOST = 0.1
QH.UPPER = 100.0
QH.LOWER = 0.0

# State variables
TH1 = m.SV(value=Fm[0])
TH2 = m.SV(value=Tm[0])

# Controlled variables
FC = m.CV(value=Fm[0],name='FC')
FC.STATUS = 1     # drive to set point
FC.FSTATUS = 1    # receive measurement
FC.TAU = 40       # response speed (time constant)
FC.TR_INIT = 1    # reference trajectory
FC.TR_OPEN = 0

TC = m.CV(value=Tm[0],name='TC')
TC.STATUS = 1     # drive to set point
TC.FSTATUS = 1    # receive measurement
TC.TAU = 0        # response speed (time constant)
TC.TR_INIT = 0    # dead-band
TC.TR_OPEN = 1

Ta = m.Param(value=23.0) # degC

# Heat transfer between two heaters
DT = m.Intermediate(TH2-TH1)

# Empirical correlations
m.Equation(tau12 * TH1.dt() + (TH1-Ta) == K1*QP + K3*DT)
m.Equation(tau12 * TH2.dt() + (TH2-Ta) == K2*QH - K3*DT)
m.Equation(tau3 * FC.dt()  + FC == TH1)
m.Equation(tau3 * TC.dt()  + TC == TH2)

# Global Options
m.options.IMODE   = 6 # MPC
m.options.CV_TYPE = 1 # Objective type
m.options.NODES   = 3 # Collocation nodes
m.options.SOLVER  = 3 # IPOPT
m.options.COLDSTART = 1 # COLDSTART on first cycle
##################################################################
# Create plot
plt.figure(figsize=(10,7))
plt.ion()
plt.show()

# Main Loop
start_time = time.time()
prev_time = start_time
tm = np.zeros(n)

try:
    for i in range(1,n-1):
        # Sleep time
        sleep_max = 3.0
        sleep = sleep_max - (time.time() - prev_time)
        if sleep>=0.01:
            time.sleep(sleep-0.01)
        else:
            time.sleep(0.01)

        # Record time and change in time
        t = time.time()
        dt = t - prev_time
        prev_time = t
        tm[i] = t - start_time

        # Read temperatures in Celsius 
        Fm[i] = a.F
        Tm[i] = a.T

        # Insert measurements
        FC.MEAS = Fm[i]
        TC.MEAS = Tm[i]

        # Adjust setpoints
        db1 = 1.0 # dead-band
        FC.SPHI = Fsp[i] + db1
        FC.SPLO = Fsp[i] - db1

        db2 = 0.2
        TC.SPHI = Tsp[i] + db2
        TC.SPLO = Tsp[i] - db2

        # Adjust heaters with MPC
        m.solve() 

        if m.options.APPSTATUS == 1:
            # Retrieve new values
            QPs[i+1]  = QP.NEWVAL
            QHs[i+1]  = QH.NEWVAL
            # get additional solution information
            with open(m.path+'//results.json') as f:
                results = json.load(f)
        else:
            # Solution failed
            QPs[i+1]  = 0.0
            QHs[i+1]  = 0.0

        # Write new heater values (0-100)
        a.QP(QPs[i])
        a.QH(QHs[i])

        # Plot
        plt.clf()
        ax=plt.subplot(3,1,1)
        ax.grid()
        plt.plot(tm[0:i+1],Fsp[0:i+1]+db1,'k-',\
                 label=r'$F$ target',lw=3)
        plt.plot(tm[0:i+1],Fsp[0:i+1]-db1,'k-',\
                 label=None,lw=3)
        plt.plot(tm[0:i+1],Fm[0:i+1],'r.',label=r'$F$ measured')
        plt.plot(tm[i]+m.time,results['FC.bcv'],'r-',\
                 label=r'$F$ predicted',lw=3)
        plt.plot(tm[i]+m.time,results['FC.tr_hi'],'k--',\
                 label=r'$F$ trajectory')
        plt.plot(tm[i]+m.time,results['FC.tr_lo'],'k--')
        plt.ylabel('Flow rate (Lpm)')
        plt.legend(loc=2)
        ax=plt.subplot(3,1,2)
        ax.grid()        
        plt.plot(tm[0:i+1],Tsp[0:i+1]+db2,'k-',\
                 label=r'$T$ target',lw=3)
        plt.plot(tm[0:i+1],Tsp[0:i+1]-db2,'k-',\
                 label=None,lw=3)
        plt.plot(tm[0:i+1],Tm[0:i+1],'b.',label=r'$T$ measured')
        plt.plot(tm[i]+m.time,results['TC.bcv'],'b-',\
                 label=r'$T$ predict',lw=3)
        plt.plot(tm[i]+m.time,results['TC.tr_hi'],'k--',\
                 label=r'$T$ range')
        plt.plot(tm[i]+m.time,results['TC.tr_lo'],'k--')
        plt.ylabel('Temperature (degC)')
        plt.legend(loc=2)
        ax=plt.subplot(3,1,3)
        ax.grid()
        plt.plot([tm[i],tm[i]],[0,100],'k-',\
                 label='Current Time',lw=1)
        plt.plot(tm[0:i+1],QPs[0:i+1],'r.-',\
                 label=r'$Q_P$ history',lw=2)
        plt.plot(tm[i]+m.time,QP.value,'r-',\
                 label=r'$Q_P$ plan',lw=3)
        plt.plot(tm[0:i+1],QHs[0:i+1],'b.-',\
                 label=r'$Q_H$ history',lw=2)
        plt.plot(tm[i]+m.time,QH.value,'b-',
                 label=r'$Q_H$ plan',lw=3)
        plt.plot(tm[i]+m.time[1],QP.value[1],color='red',\
                 marker='.',markersize=15)
        plt.plot(tm[i]+m.time[1],QH.value[1],color='blue',\
                 marker='X',markersize=8)
        plt.ylabel('Heaters')
        plt.xlabel('Time (sec)')
        plt.legend(loc=2)
        plt.draw()
        plt.pause(0.05)
        if make_mp4:
            filename='./figures/plot_'+str(i+10000)+'.png'
            plt.savefig(filename)

    # Turn off heaters and close connection
    a.QP(0)
    a.QH(0)
    a.close()
    # Save figure
    plt.savefig('limonata_mpc.png')

    # generate mp4 from png figures in batches of 350
    if make_mp4:
        images = []
        iset = 0
        for i in range(1,n-1):
            filename='./figures/plot_'+str(i+10000)+'.png'
            images.append(imageio.imread(filename))
            if ((i+1)%350)==0:
                imageio.mimsave('results_'+str(iset)+'.mp4', images)
                iset += 1
                images = []
        if images!=[]:
            imageio.mimsave('results_'+str(iset)+'.mp4', images)

# Allow user to end loop with Ctrl-C           
except KeyboardInterrupt:
    # Turn off heaters and close connection
    a.QP(0)
    a.QH(0)
    a.close()
    print('Shutting down')
    plt.savefig('limonata_mpc.png')

# Make sure serial connection still closes when there's an error
except:           
    # Disconnect from Arduino
    a.QP(0)
    a.QH(0)
    a.close()
    print('Error: Shutting down')
    plt.savefig('limonata_mpc.png')
    raise