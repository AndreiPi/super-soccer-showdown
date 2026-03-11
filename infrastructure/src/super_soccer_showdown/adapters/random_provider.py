import random

from .interface.random_provider import RandomProvider


class PythonRandomProvider(RandomProvider):
    def randint(self, start: int, end: int) -> int:
        return random.randint(start, end)
