from typing import Protocol


class RandomProvider(Protocol):
    def randint(self, start: int, end: int) -> int:
        """Return a random integer in the inclusive range [start, end]."""
