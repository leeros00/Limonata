from limonata.reactor import Reactor
import pytest as pt


@pt.fixture
def reactor() -> Reactor:
    """Fixture for creating a Reactor instance for each test."""
    return Reactor(port="", debug=True)  # You can customize the port if needed


def test_reactor_initialization(reactor: Reactor) -> None:
    """Test if the reactor connects and initializes correctly."""
    reactor.connect(baud_rate=115200)
    assert reactor.sp.isOpen()  # Ensure the serial connection is open
    assert reactor.baud_rate == 115200  # Ensure the baud rate is set correctly


def test_start_reactor(reactor: Reactor) -> None:
    """Test if the reactor initializes with the correct default values."""
    assert reactor.port is not None  # Ensure the port is set
    assert reactor.baud_rate in [115200, 9600]  # Ensure valid baud rate
    assert reactor.version.startswith("VERSION")  # Ensure version is set correctly
    assert reactor.sp.isOpen()  # Ensure the serial connection is open


def test_Q_control(reactor: Reactor) -> None:
    """Test if the Q control works properly."""
    reactor.connect(baud_rate=115200)
    reactor.Q(100)  # Set the temperature to 100
    assert reactor.Q() == 100  # Ensure the temperature is set to 100

