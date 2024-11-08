from serial.tools import list_ports  # type: ignore

sep: str = " "  # command/value separator in Reactor firmware

arduinos: list[tuple[str, str]] = [
    ("USB VID:PID=16D0:0613", "Arduino Uno"),
    ("USB VID:PID=1A86:7523", "NHduino"),
    ("USB VID:PID=2341:8036", "Arduino Leonardo"),
    ("USB VID:PID=2A03", "Arduino.org device"),
    ("USB VID:PID", "unknown device"),
]


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