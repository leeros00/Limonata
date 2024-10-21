from __future__ import print_function

import time
import serial  # type: ignore
from serial.tools import list_ports  # type: ignore

# from .labtime import labtime
# from .version import __version__

from typing import Any, Callable


sep = " "
_firmware_url = ""
_connected = False

mcus = [
    ("USB VID:PID=16D0:0613", "Arduino Uno"),
    ("USB VID:PID=1A86:7523", "NHduino"),
    ("USB VID:PID=2341:8036", "Arduino Leonardo"),
    ("USB VID:PID=2A03", "Arduino.org device"),
    ("USB VID:PID", "unknown device"),
]


def clip(
    val: float | int, lower: float | int = 0, upper: float | int = 100
) -> float | int:
    """Limit value to be between lower and upper limits."""
    return max(lower, min(val, upper))


def command(
    name: str,
    argument: float | int,
    lower: float | int = 0,
    upper: float | int = 100,
) -> str:
    """Locates the controller and returns the port and device."""
    return name + sep + str(clip(val=argument, lower=lower, upper=upper))


def find_microcontroller(port: str = "") -> tuple | tuple[None, None]:
    """Locates the microcontroller and returns port and device."""
    # TODO: Figure out the type hinting for port, mcu
    comports = [tuple for tuple in list_ports.comports() if port in tuple[0]]
    for port, desc, hwid in comports:
        for identifier, mcu in mcus:
            if hwid.startswith(identifier):
                return port, mcu
    print("--- Serial Ports ---")
    for (
        port,
        desc,
        hwid,
    ) in list_ports.comports():
        print(port, desc, hwid)
    return None, None


class AlreadyConnectedError(Exception):
    pass


class Reactor(object):
    def __init__(self, port: str = "", debug: bool = False) -> None:
        global _connected
        self.debug = debug
        self.baud_rate = 115200
        # print("Limonata version", __version__)
        self.port, self.dev_board = find_microcontroller(port=port)
        if self.port is None:
            raise RuntimeError("No microcontroller device found.")

        try:
            self.connect(baud_rate=self.baud_rate)
        except AlreadyConnectedError:
            raise
        except Exception:
            try:
                _connected = False
                self.baud_rate = 9600
                self.sp.close()
                self.connect(baud_rate=self.baud_rate)
                print(
                    "Could not connect at high baud rate, but succeeded at low baud rate."
                )
            except Exception as e:
                raise RuntimeError("Failed to connect.") from e

        self.sp.readline().decode("UTF-8")
        self.version = self.send_and_receive("VERSION")
        if self.sp.isOpen():
            print(
                self.dev_board,
                "connected on port",
                self.port,
                "at",
                self.baud_rate,
                "baud.",
            )
            print(self.version + ".")
        # TODO: implement labtime equivalent
        self._P = 250.0
        self.Q(0)
        # TODO: set other defaults as needed
        self.sources = [
            ("T", self.scan),
            ("Q", None),
        ]

    def __enter__(self) -> "Reactor":
        """Enters the context manager."""
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> bool:
        """Exits the context manager and ends the connection."""
        self.close()
        return exc_type is None

    def connect(self, baud_rate: int) -> None:
        """Establish a connection to the MCU"""
        global _connected
        if _connected:
            raise AlreadyConnectedError("You already have an open connection.")
        _connected = True

        self.sp = serial.Serial(port=self.port, baudrate=baud_rate, timeout=2)
        time.sleep(2)
        self.Q(0)  # Fails if not connected
        self.baud_rate = baud_rate

    def close(self) -> None:
        """Shut down the Limonata device and close serial connection."""
        global _connected

        self.Q(0)
        self.send_and_receive("X")
        self.sp.close()
        _connected = False
        print("Limonata disconnected successfully.")
        return

    def send(self, msg: str) -> None:
        """Send a string message to the MCU firmware."""
        self.sp.write((msg + "\r\n").encode())
        if self.debug:
            print('Sent: "' + msg + '"')
        self.sp.flush()

    def receive(self) -> str:
        """Retrieve a string message received from the Limonata Firmware"""
        msg = self.sp.readline().decode("UTF-8").replace("\r\n", "")
        if self.debug:
            print('Return: "' + msg + '"')
        return msg

    def send_and_receive(self, msg: str, convert: Any = str) -> Any:
        """Send a string message and return the response."""
        self.send(msg=msg)
        response = self.receive()
        if not response:
            raise ValueError("No response received from controller.")
        return convert(response)

    def alarm(self) -> None:
        pass

    @property
    def T(self) -> float:
        """Returns the interior temperature of the red reactor vessel."""
        return self.send_and_receive(msg="T", convert=float)

    @property
    def P(self) -> float:
        return self._P

    @P.setter
    def P(self, val: int | float) -> None:
        self._P = self.send_and_receive(command("P", val, 0, 255), float)

    def Q(self, val: float | int = 0) -> float:
        """Get or set Limonata red vessel temperature."""
        if val is None:
            msg = "R"
        else:
            msg = "Q" + sep + str(clip(val=val))
        return self.send_and_receive(msg=msg, convert=float)

    def scan(self) -> tuple[float, Callable[[float | int], float]]:
        """Scans for T and Q values"""
        T = self.T
        Q = self.Q
        return T, Q

    U = property(fget=Q, fset=lambda self, val: self.Q(val=val), doc="Red Heater value")
