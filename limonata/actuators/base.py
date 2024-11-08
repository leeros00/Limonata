from limonata.utils import clip, sep
from typing import Any
import serial

class Actuator:
    def __init__(self, sp: serial.Serial, debug: bool = False) -> None:
        self._Q = 0
        self.sp = sp
        self.debug = debug

    def __enter__(self) -> "Actuator":
        return self

    def send(self, msg: str) -> None:
        """Sends a string message to the firmware."""
        self.sp.write((msg + "\r\n").encode())
        if self.debug:
            print('Sent: "' + msg + '"')
        self.sp.flush()

    def receive(self) -> str:
        """Returns a string message received from the firmware."""
        msg = self.sp.readline().decode("UTF-8").replace("\r\n", "")
        if self.debug:
            print('Return: "' + msg + '"')
        return msg
    
    def send_and_receive(self, msg: str, convert: type = str) -> Any:
        """Send a string message and return the response."""
        self.send(msg=msg)
        return convert(self.receive())

    @property
    def Q(self) -> float:
        return self._Q
    
    def Q(self, val: float | None = None) -> float:
        """Get or set Actuator output
        val: Value of desired actuator input from 0-100 
        """
        if val is None:
            msg = "R"
        else:
            msg = "Q" + sep + str(clip(val=val))
        return self.send_and_receive(msg=msg, convert=str)