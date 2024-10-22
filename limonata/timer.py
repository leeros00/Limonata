import time as time


class Timer:
    def __init__(self):
        self._realtime = time.time()
        self._timer = 0
        self._rate = 1
        self._running = True
        self.lastsleep = 0

    @property
    def running(self):
        """Returns variable indicating whether timer is running."""
        return self._running

    def time(self):
        """Return current timer."""
        if self.running:
            elapsed = time.time() - self._realtime
            return self._timer + self._rate * elapsed
        else:
            return self._timer

    def set_rate(self, rate=1):
        """Set the rate of timer relative to real time."""
        if rate <= 0:
            raise ValueError("timer rates must be positive.")
        self._timer = self.time()
        self._realtime = time.time()
        self._rate = rate

    def get_rate(self):
        """Return the rate of timer relative to real time."""
        return self._rate

    def sleep(self, delay):
        """Sleep in timer for a period delay."""
        self.lastsleep = delay
        if self._running:
            time.sleep(delay / self._rate)
        else:
            raise RuntimeWarning("sleep is not valid when timer is stopped.")

    def stop(self):
        """Stop timer."""
        self._timer = self.time()
        self._realtime = time.time()
        self._running = False

    def start(self):
        """Restart timer."""
        self._realtime = time.time()
        self._running = True

    def reset(self, val=0):
        """Reset timer to a specified value."""
        self._timer = val
        self._realtime = time.time()


timer = Timer()


# for backwards compatability
def setnow(tnow=0):
    timer.reset(tnow)


def clock(period, step=1, tol=float("inf"), adaptive=True):
    """Generator providing time values in sync with real time clock.

    Args:
        period (float): Time interval for clock operation in seconds.
        step (float): Time step.
        tol (float): Maximum permissible deviation from real time.
        adaptive (Boolean): If true, and if the rate != 1, then the timer
            rate is adjusted to maximize simulation speed.

    Yields:
        float: The next time step rounded to nearest 10th of a second.


    Note:
        * Passing `tol=float('inf')` will effectively disable sync error checking
        * When large values for `tol` are used, no guarantees are made that the
          last time returned will be equal to `period`.
    """
    start = timer.time()
    now = 0

    while round(now, 0) <= period:
        yield round(now, 2)
        if round(now) >= period:
            break
        elapsed = timer.time() - (start + now)
        rate = timer.get_rate()
        if (rate != 1) and adaptive:
            if elapsed > step:
                timer.set_rate(0.8 * rate * step / elapsed)
            elif (elapsed < 0.5 * step) & (rate < 50):
                timer.set_rate(1.25 * rate)
        else:
            if elapsed > step + tol:
                message = (
                    "timer clock lost synchronization with real time. "
                    "Step size was {} s, but {:.2f} s elapsed "
                    "({:.2f} too long). Consider increasing step."
                )
                raise RuntimeError(message.format(step, elapsed, elapsed - step))
        timer.sleep(step - (timer.time() - start) % step)
        now = timer.time() - start
