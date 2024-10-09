import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from limonata.reactor.reactor import Reactor

import numpy as np
import matplotlib.pyplot as plt
import time

def pid(sp,pv,pv_last,ierr,dt):
    # Parameters in terms of PID coefficients
    KP = 2.0#Kc
    KI = 5.0#Kc/tauI
    KD = 1.0#Kc*tauD
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
        reactor = Reactor()
        try:
            n = 600*3  # Number of second time points (30 min)
            tm = np.linspace(0,n-1,n) # Time values
            
            T_red_reactor = np.zeros(n)
            Q_red_heater = np.zeros(n)
            
            SP1 = np.ones(n)*29.0
            SP1[100:] = 32.0
            Q_red_heater_bias = 0.0
            ierr = 0.0
            for i in range(n):
                # record measurement
                T_red_reactor[i] = reactor.T_red_reactor

                # --------------------------------------------------
                # call PID controller function to change Q_red_heater[i]
                # --------------------------------------------------
                [Q_red_heater[i],P,ierr,D] = pid(SP1[i],T_red_reactor[i],T_red_reactor[max(0,i-1)],ierr,1.0)

                reactor.Q_red_heater(Q_red_heater[i])
                if i%20==0:
                    print(' Heater,   Temp,  Setpoint')
                print(f'{Q_red_heater[i]:7.2f},{T_red_reactor[i]:7.2f},{SP1[i]:7.2f}')
                # wait for 1 sec
                time.sleep(1)
            reactor.close()
            # Save data file
            data = np.vstack((tm,Q_red_heater,T_red_reactor,SP1)).T
            np.savetxt('PID_control.csv',data,delimiter=',',\
                    header='Time,Q_red_heater,T_red_reactor,SP1',comments='')

            # Create Figure
            plt.figure(figsize=(10,7))
            ax = plt.subplot(2,1,1)
            ax.grid()
            plt.plot(tm/60.0,SP1,'k-',label=r'$T_1$ SP')
            plt.plot(tm/60.0,T_red_reactor,'r.',label=r'$T_1$ PV')
            plt.ylabel(r'Temp ($^oC$)')
            plt.legend(loc=2)
            ax = plt.subplot(2,1,2)
            ax.grid()
            plt.plot(tm/60.0,Q_red_heater,'b-',label=r'$Q_1$')
            plt.ylabel(r'Heater (%)')
            plt.xlabel('Time (min)')
            plt.legend(loc=1)
            plt.savefig('PID_Control.png')
            plt.show()

        except Exception as e:
            self.fail(f"PID control failed with exception: {e}")

if __name__ == "__main__":
    unittest.main()