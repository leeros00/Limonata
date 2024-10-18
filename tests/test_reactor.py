# from limonata.reactor import Reactor
# import pytest as pt
# from unittest import mock


# @pt.fixture
# def reactor() -> Reactor:
#     """Fixture for creating a Reactor instance for each test."""
#     # Mock the serial connection
#     with mock.patch('serial.Serial') as mock_serial:
#         mock_serial.return_value.isOpen.return_value = True  # Simulate open connection
#         mock_serial.return_value.readline.return_value = b'OK\n'  # Simulate reading a line
#         mock_serial.return_value.write.return_value = None  # Simulate writing to serial
#         return Reactor(port="", debug=True)


# def test_reactor_initialization(reactor: Reactor) -> None:
#     """Test if the reactor connects and initializes correctly."""
#     reactor.connect(baud_rate=115200)
#     assert reactor.sp.isOpen()  # Ensure the serial connection is open
#     assert reactor.baud_rate == 115200  # Ensure the baud rate is set correctly


# def test_start_reactor(reactor: Reactor) -> None:
#     """Test if the reactor initializes with the correct default values."""
#     assert reactor.port is not None  # Ensure the port is set
#     assert reactor.baud_rate in [115200, 9600]  # Ensure valid baud rate
#     assert reactor.version.startswith("VERSION")  # Ensure version is set correctly
#     assert reactor.sp.isOpen()  # Ensure the serial connection is open


# def test_Q_control(reactor: Reactor) -> None:
#     """Test if the Q control works properly."""
#     reactor.connect(baud_rate=115200)
#     reactor.Q(100)  # Set the temperature to 100
#     assert reactor.Q() == 100  # Ensure the temperature is set to 100
