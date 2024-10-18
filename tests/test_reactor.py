from limonata.reactor import Reactor
import pytest as pt


@pt.fixture
def test_T() -> Reactor:
    """Fixture for creating a Reactor instance each test."""
    return Reactor()


def test_reactor_initialization(reactor: Reactor) -> None:
    """Test starting the reactor."""
    reactor.initialize()
    reactor.start()
    assert reactor.status == "running"


def test_start_reactor(reactor: Reactor) -> None:
    """Test if the reactor initializes with the correct values."""
    assert reactor.port is not None
    assert reactor.baud_rate in [11520, 9600]
    assert reactor.version.startswith("VERSION")
    assert reactor.sp.isOpen()
