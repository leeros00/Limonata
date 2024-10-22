from __future__ import print_function
import time
import random
import serial  # type: ignore
from serial.tools import list_ports  # type: ignore
from limonata.timer import timer
from limonata.version import __version__

from typing import Callable, Any

sep: str = " "  # command/value separator in Reactor firmware

arduinos: list[tuple[str, str]] = [
    ("USB VID:PID=16D0:0613", "Arduino Uno"),
    ("USB VID:PID=1A86:7523", "NHduino"),
    ("USB VID:PID=2341:8036", "Arduino Leonardo"),
    ("USB VID:PID=2A03", "Arduino.org device"),
    ("USB VID:PID", "unknown device"),
]

_connected: bool = False


def clip(val: float, lower: float = 0, upper: float = 100) -> float:
    """Limit value to be between lower and upper limits"""
    return max(lower, min(val, upper))


def command(name: str, argument: float, lower: float = 0, upper: float = 100) -> str:
    """Construct command to the firmware."""
    return name + sep + str(clip(argument, lower, upper))


def find_arduino(port: str = "") -> tuple[str | None, str | None]:
    """Locates Arduino and returns port and device."""
    comports: list[tuple[str, str, str]] = [
        tuple for tuple in list_ports.comports() if port in tuple[0]
    ]
    for port, desc, hwid in comports:
        for identifier, arduino in arduinos:
            if hwid.startswith(identifier):
                return port, arduino
    print("--- Serial Ports ---")
    for port, desc, hwid in list_ports.comports():
        print(port, desc, hwid)
    return None, None


class AlreadyConnectedError(Exception):
    pass


class Reactor:
    def __init__(self, port: str = "", debug: bool = False):
        global _connected
        self.debug: bool = debug
        print("Reactor version", __version__)
        self.port, self.arduino = find_arduino(port)
        if self.port is None:
            raise RuntimeError("No Arduino device found.")

        try:
            self.connect(baud=115200)
        except AlreadyConnectedError:
            raise
        except Exception as e:
            print(f"Error occurred: {e}")
            try:
                _connected = False
                self.sp.close()
                self.connect(baud=9600)
                print("Could not connect at high speed, but succeeded at low speed.")
            except Exception as e:
                print(f"Failed to connect: {e}")
                raise RuntimeError("Failed to connect.")

        self.sp.readline().decode("UTF-8")
        self.version: str = self.send_and_receive("VER")
        if self.sp.isOpen():
            print(
                self.arduino, "connected on port", self.port, "at", self.baud, "baud."
            )
            print(self.version + ".")
        timer.set_rate(1)
        timer.start()
        self._P1: float = 200.0
        self._P2: float = 100.0
        self.Q2(0)
        self.sources: list[tuple[str, Callable | None]] = [
            ("T1", self.scan),
            ("T2", None),
            ("Q1", None),
            ("Q2", None),
        ]

    def __enter__(self) -> "Reactor":
        return self

    def __exit__(
        self, exc_type: type | None, exc_value: Exception | None, traceback
    ) -> None:
        self.close()

    def connect(self, baud: int) -> None:
        """Establish a connection to the Arduino

        baud: baud rate"""
        global _connected

        if _connected:
            raise AlreadyConnectedError("You already have an open connection")

        _connected = True
        self.sp = serial.Serial(port=self.port, baudrate=baud, timeout=2)
        time.sleep(2)
        self.Q1(0)  # fails if not connected
        self.baud: int = baud

    def close(self) -> None:
        """Shut down Reactor device and close serial connection."""
        global _connected

        self.Q1(0)
        self.Q2(0)
        self.send_and_receive("X")
        self.sp.close()
        _connected = False
        print("Reactor disconnected successfully.")

    def send(self, msg: str) -> None:
        """Send a string message to the Reactor firmware."""
        self.sp.write((msg + "\r\n").encode())
        if self.debug:
            print('Sent: "' + msg + '"')
        self.sp.flush()

    def receive(self) -> str:
        """Return a string message received from the Reactor firmware."""
        msg: str = self.sp.readline().decode("UTF-8").replace("\r\n", "")
        if self.debug:
            print('Return: "' + msg + '"')
        return msg

    def send_and_receive(self, msg: str, convert: type = str) -> Any:
        """Send a string message and return the response"""
        self.send(msg)
        return convert(self.receive())

    def LED(self, val: float = 100) -> float:
        """Flash Reactor LED at a specified brightness for 10 seconds."""
        return self.send_and_receive(command("LED", val), float)

    @property
    def T1(self) -> float:
        """Return a float denoting Reactor temperature T1 in degrees C."""
        return self.send_and_receive("T1", float)

    @property
    def T2(self) -> float:
        """Return a float denoting Reactor temperature T2 in degrees C."""
        return self.send_and_receive("T2", float)

    @property
    def P1(self) -> float:
        """Return a float denoting maximum power of heater 1 in pwm."""
        return self._P1

    @P1.setter
    def P1(self, val: float) -> None:
        """Set maximum power of heater 1 in pwm, range 0 to 255."""
        self._P1 = self.send_and_receive(command("P1", val, 0, 255), float)

    @property
    def P2(self) -> float:
        """Return a float denoting maximum power of heater 2 in pwm."""
        return self._P2

    @P2.setter
    def P2(self, val: float) -> None:
        """Set maximum power of heater 2 in pwm, range 0 to 255."""
        self._P2 = self.send_and_receive(command("P2", val, 0, 255), float)

    def Q1(self, val: float | None = None) -> float:
        """Get or set Reactor heater power Q1

        val: Value of heater power, range is limited to 0-100

        return clipped value."""
        if val is None:
            msg = "R1"
        else:
            msg = "Q1" + sep + str(clip(val))
        return self.send_and_receive(msg, float)

    def Q2(self, val: float | None = None) -> float:
        """Get or set Reactor heater power Q2

        val: Value of heater power, range is limited to 0-100

        return clipped value."""
        if val is None:
            msg = "R2"
        else:
            msg = "Q2" + sep + str(clip(val))
        return self.send_and_receive(msg, float)

    def scan(self) -> tuple[float, float, float, float]:
        T1: float = self.T1
        T2: float = self.T2
        Q1: float = self.Q1()
        Q2: float = self.Q2()
        return T1, T2, Q1, Q2

    U1 = property(
        fget=lambda self: self.Q1(),
        fset=lambda self, val: self.Q1(val),
        doc="Heater 1 value",
    )

    U2 = property(
        fget=lambda self: self.Q2(),
        fset=lambda self, val: self.Q2(val),
        doc="Heater 2 value",
    )


class ReactorModel:
    def __init__(self, port: str = "", debug: bool = False, synced: bool = True):
        self.debug: bool = debug
        self.synced: bool = synced
        print("Reactor version", __version__)
        timer.start()
        print("Simulated Reactor")
        self.Ta: float = 21  # ambient temperature
        self.tstart: float = timer.time()  # start time
        self.tlast: float = self.tstart  # last update time
        self._P1: float = 200.0  # max power heater 1
        self._P2: float = 100.0  # max power heater 2
        self._Q1: float = 0  # initial heater 1
        self._Q2: float = 0  # initial heater 2
        self._T1: float = self.Ta  # temperature thermistor 1
        self._T2: float = self.Ta  # temperature thermistor 2
        self._H1: float = self.Ta  # temperature heater 1
        self._H2: float = self.Ta  # temperature heater 2
        self.maxstep: float = 0.2  # maximum time step for integration
        self.sources: list[tuple[str, Callable | None]] = [
            ("T1", self.scan),
            ("T2", None),
            ("Q1", None),
            ("Q2", None),
        ]

    def __enter__(self) -> "ReactorModel":
        return self

    def __exit__(
        self, exc_type: type | None, exc_value: Exception | None, traceback
    ) -> None:
        self.close()

    def close(self) -> None:
        """Simulate shutting down Reactor device."""
        self.Q1(0)
        self.Q2(0)
        print("Reactor Model disconnected successfully.")

    def LED(self, val: float = 100) -> float:
        """Simulate flashing Reactor LED

        val : specified brightness (default 100)."""
        self.update()
        return clip(val)

    @property
    def T1(self) -> float:
        """Return a float denoting Reactor temperature T1 in degrees C."""
        self.update()
        return self.measurement(self._T1)

    @property
    def T2(self) -> float:
        """Return a float denoting Reactor temperature T2 in degrees C."""
        self.update()
        return self.measurement(self._T2)

    @property
    def P1(self) -> float:
        """Return a float denoting maximum power of heater 1 in pwm."""
        self.update()
        return self._P1

    @P1.setter
    def P1(self, val: float) -> None:
        """Set maximum power of heater 1 in pwm, range 0 to 255."""
        self.update()
        self._P1 = clip(val, 0, 255)

    @property
    def P2(self) -> float:
        """Return a float denoting maximum power of heater 2 in pwm."""
        self.update()
        return self._P2

    @P2.setter
    def P2(self, val: float) -> None:
        """Set maximum power of heater 2 in pwm, range 0 to 255."""
        self.update()
        self._P2 = clip(val, 0, 255)

    def Q1(self, val: float | None = None) -> float:
        """Get or set ReactorModel heater power Q1

        val: Value of heater power, range is limited to 0-100

        return clipped value."""
        self.update()
        if val is not None:
            self._Q1 = clip(val)
        return self._Q1

    def Q2(self, val: float | None = None) -> float:
        """Get or set ReactorModel heater power Q2

        val: Value of heater power, range is limited to 0-100

        return clipped value."""
        self.update()
        if val is not None:
            self._Q2 = clip(val)
        return self._Q2

    def scan(self) -> tuple[float, float, float, float]:
        self.update()
        return (
            self.measurement(self._T1),
            self.measurement(self._T2),
            self._Q1,
            self._Q2,
        )

    U1 = property(
        fget=lambda self: self.Q1(),
        fset=lambda self, val: self.Q1(val),
        doc="Heater 1 value",
    )

    U2 = property(
        fget=lambda self: self.Q2(),
        fset=lambda self, val: self.Q2(val),
        doc="Heater 2 value",
    )

    def quantize(self, T: float) -> float:
        """Quantize model temperatures to mimic Arduino A/D conversion."""
        return max(-50, min(132.2, T - T % 0.3223))

    def measurement(self, T: float) -> float:
        return self.quantize(T + random.normalvariate(0, 0.043))

    def update(self, t: float | None = None) -> None:
        if t is None:
            if self.synced:
                self.tnow: float = timer.time() - self.tstart
            else:
                return
        else:
            self.tnow = t

        teuler: float = self.tlast

        while teuler < self.tnow:
            dt: float = min(self.maxstep, self.tnow - teuler)
            DeltaTaH1: float = self.Ta - self._H1
            DeltaTaH2: float = self.Ta - self._H2
            DeltaT12: float = self._H1 - self._H2
            dH1: float = self._P1 * self._Q1 / 5720 + DeltaTaH1 / 20 - DeltaT12 / 100
            dH2: float = self._P2 * self._Q2 / 5720 + DeltaTaH2 / 20 + DeltaT12 / 100
            dT1: float = (self._H1 - self._T1) / 140
            dT2: float = (self._H2 - self._T2) / 140

            self._H1 += dt * dH1
            self._H2 += dt * dH2
            self._T1 += dt * dT1
            self._T2 += dt * dT2
            teuler += dt

        self.tlast = self.tnow


def diagnose(port: str = "") -> None:
    def countdown(t: int = 10) -> None:
        for i in reversed(range(t)):
            print("\r" + "Countdown: {0:d}  ".format(i), end="", flush=True)
            time.sleep(1)
        print()

    def heading(string: str) -> None:
        print()
        print(string)
        print("-" * len(string))

    heading("Checking connection")

    if port:
        print("Looking for Arduino on {} ...".format(port))
    else:
        print("Looking for Arduino on Any port...")
    comport, name = find_arduino(port=port)

    if comport is None:
        print("No known Arduino was found in the ports listed above.")
        return

    print(name, "found on port", comport)

    heading("Testing Reactor object in debug mode")

    with Reactor(port=port, debug=True) as reactor:
        print("Reading temperature")
        print(reactor.T1)

    heading("Testing Reactor functions")

    with Reactor(port=port) as reactor:
        print("Testing LED. Should turn on for 10 seconds.")
        reactor.LED(100)
        countdown()

        print()
        print("Reading temperatures")
        T1: float = reactor.T1
        T2: float = reactor.T2
        print("T1 = {} °C, T2 = {} °C".format(T1, T2))

        print()
        print("Writing fractional value to heaters...")
        try:
            Q1: float = reactor.Q1(0.5)
        except Exception as e:
            print(f"Error occurred while setting Q1: {e}")
            Q1 = -1.0
        print("We wrote Q1 = 0.5, and read back Q1 =", Q1)

        if Q1 != 0.5:
            print(
                "Your Reactor firmware version ({}) doesn't support"
                "fractional heater values.".format(reactor.version)
            )

        print()
        print(
            "We will now turn on the heaters, wait 30 seconds "
            "and see if the temperatures have gone up. "
        )
        reactor.Q1(100)
        reactor.Q2(100)
        countdown(30)

        print()

        def tempcheck(name: str, T_initial: float, T_final: float) -> None:
            print(
                "{} started at {} °C and went to {} °C".format(name, T_initial, T_final)
            )
            if T_final - T_initial < 0.8:
                print("The temperature went up less than expected.")
                print("Check the heater power supply.")

        T1_final: float = reactor.T1
        T2_final: float = reactor.T2

        tempcheck("T1", T1, T1_final)
        tempcheck("T2", T2, T2_final)

        print()
        heading("Throughput check")
        print("This part checks how fast your unit is")
        print("We will read T1 as fast as possible")

        start: float = time.time()
        n: int = 0
        while time.time() - start < 10:
            elapsed: float = time.time() - start + 0.0001  # avoid divide by zero
            T1 = reactor.T1
            n += 1
            print(
                "\rTime elapsed: {:3.2f} s."
                " Number of reads: {}."
                " Sampling rate: {:2.2f} Hz".format(elapsed, n, n / elapsed),
                end="",
            )

        print()

    print()
    print("Diagnostics complete")
