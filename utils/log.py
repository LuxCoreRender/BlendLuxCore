# import collections


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
