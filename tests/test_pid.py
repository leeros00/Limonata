import sys
import os

import limonata.reactor
import limonata.reactor.reactor

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
import numpy as np
import matplotlib.pyplot as plt
import limonata
import time


# process model
Kp = 0.9
taup = 175.0
thetap = 15.0

# -----------------------------
# Calculate Kc,tauI,tauD (IMC Aggressive)
# -----------------------------
tauc = max(0.1*taup,0.8*thetap)
Kc = (1/Kp)*(taup+0.5*thetap)/(tauc+0.5*thetap)
tauI = taup + 0.5*thetap
tauD = taup*thetap / (2*taup+thetap)

print('Kc: ' + str(Kc))
print('tauI: ' + str(tauI))
print('tauD: ' + str(tauD))

def pid(sp,pv,pv_last,ierr,dt):
    # Parameters in terms of PID coefficients
    KP = Kc
    KI = Kc/tauI
    KD = Kc*tauD
    # ubias for controller (initial heater)
    op0 = 0
    # upper and lower bounds on heater level
    ophi = 100
    oplo = 0
    # calculate the error
    error = sp-pv
    # calculate the integral error
    ierr = ierr + KI * error * dt
    # calculate the measurement derivative
    dpv = (pv - pv_last) / dt
    # calculate the PID output
    P = KP * error
    I = ierr
    D = -KD * dpv
    op = op0 + P + I + D
    # implement anti-reset windup
    if op < oplo or op > ophi:
        I = I - KI * error * dt
        # clip output
        op = max(oplo,min(ophi,op))
    # return the controller output and PID terms
    return [op,P,I,D]





class TestLimonataRed(unittest.TestCase):
    def test_pid_temperature_control(self) -> None:
        #reactor = Reactor()
        try:



            #------------------------
            # PID Controller Function
            #------------------------
            # sp = setpoint
            # pv = current temperature
            # pv_last = prior temperature
            # ierr = integral error
            # dt = time increment between measurements
            # outputs ---------------
            # op = output of the PID controller
            # P = proportional contribution
            # I = integral contribution
            # D = derivative contribution

            n = 600  # Number of second time points (10 min)
            tm = np.linspace(0,n-1,n) # Time values
            lab = limonata.reactor.reactor.Reactor()
            T = np.zeros(n)
            Q = np.zeros(n)
            # step setpoint from 23.0 to 60.0 degC
            SP1 = np.ones(n)*23.0
            SP1[10:] = 60.0
            Q_bias = 0.0
            ierr = 0.0
            for i in range(n):
                # record measurement
                T[i] = lab.T

                # --------------------------------------------------
                # call PID controller function to change Q[i]
                # --------------------------------------------------
                [Q[i],P,ierr,D] = pid(SP1[i],T[i],T[max(0,i-1)],ierr,1.0)

                lab.Q(Q[i])
                if i%20==0:
                    print(' Heater,   Temp,  Setpoint')
                print(f'{Q[i]:7.2f},{T[i]:7.2f},{SP1[i]:7.2f}')
                # wait for 1 sec
                time.sleep(1)
            lab.close()
            # Save data file
            data = np.vstack((tm,Q,T,SP1)).T
            np.savetxt('PID_control.csv',data,delimiter=',',\
                    header='Time,Q,T,SP1',comments='')

            # Create Figure
            plt.figure(figsize=(10,7))
            ax = plt.subplot(2,1,1)
            ax.grid()
            plt.plot(tm/60.0,SP1,'k-',label=r'$T_1$ SP')
            plt.plot(tm/60.0,T,'r.',label=r'$T_1$ PV')
            plt.ylabel(r'Temp ($^oC$)')
            plt.legend(loc=2)
            ax = plt.subplot(2,1,2)
            ax.grid()
            plt.plot(tm/60.0,Q,'b-',label=r'$Q_1$')
            plt.ylabel(r'Heater (%)')
            plt.xlabel('Time (min)')
            plt.legend(loc=1)
            plt.savefig('PID_Control.png')
            plt.show()

        except Exception as e:
            self.fail(f"PID control failed with exception: {e}")

if __name__ == "__main__":
    unittest.main()