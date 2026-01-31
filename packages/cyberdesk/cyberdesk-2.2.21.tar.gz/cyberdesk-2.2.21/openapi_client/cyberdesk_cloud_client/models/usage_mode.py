from enum import Enum


class UsageMode(str, Enum):
    BILLED = "billed"
    SIMULATED = "simulated"

    def __str__(self) -> str:
        return str(self.value)
