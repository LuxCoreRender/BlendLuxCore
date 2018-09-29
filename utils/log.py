# import collections


class LuxCoreLog:
    # _history = collections.deque(maxlen=50)
    _listeners = []

    @staticmethod
    def add(msg):
        print(msg)
        # LuxCoreLog._history.append(msg)

        for listener in LuxCoreLog._listeners:
            listener(msg)

    @classmethod
    def clear(cls):
        cls._history.clear()

    @classmethod
    def add_listener(cls, listener):
        cls._listeners.append(listener)

    @classmethod
    def remove_listener(cls, listener):
        cls._listeners.remove(listener)
