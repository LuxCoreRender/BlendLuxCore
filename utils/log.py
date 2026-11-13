# import collections
from time import time

# Wall-clock reference for [BLC] messages. Set to "now" by reset_t0() when
# pyluxcore.Init() is called, so that [BLC][t] and the [SDL][t] timestamps
# printed by LuxCore share the same time base (seconds since luxcore::Init)
T0 = time()


def reset_t0():
    """Set the wall-time reference to now.

    Must be called when pyluxcore.Init() is called: LuxCore timestamps its
    [SDL] messages as WallClockTime() - lcInitTime, where lcInitTime is the
    wall-clock time of the luxcore::Init() call.
    """
    global T0
    T0 = time()


def log_str(msg):
    """Format a [BLC] message with a wall-time prefix: [BLC][<t>] <msg>"""
    t = time() - T0
    if msg:
        return f"[BLC][{t:.3f}] {msg}"
    return f"[BLC][{t:.3f}]"


def log(msg):
    """Print a [BLC] message with a wall-time prefix, like [SDL][t] in LuxCore."""
    print(log_str(msg))


class LuxCoreLog:
    _listeners = []

    @staticmethod
    def add(msg):
        print(msg)

        for listener in LuxCoreLog._listeners:
            listener(msg)

    @staticmethod
    def silent(msg):
        pass

    @classmethod
    def add_listener(cls, listener):
        cls._listeners.append(listener)

    @classmethod
    def remove_listener(cls, listener):
        cls._listeners.remove(listener)
