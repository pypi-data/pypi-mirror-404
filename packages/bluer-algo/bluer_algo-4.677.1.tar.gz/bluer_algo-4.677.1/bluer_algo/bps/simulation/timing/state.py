from enum import Enum, auto
from typing import Tuple


class State(Enum):
    AO = auto()
    A = auto()
    AC = auto()
    RO = auto()
    R = auto()
    RC = auto()

    @property
    def color_code(self) -> Tuple[int, int, int]:
        return (
            3 * [64]
            if self in [State.AO, State.RO]
            else (
                3 * [128]
                if self in [State.AC, State.RC]
                else ([0, 255, 0] if self == State.A else [0, 0, 255])
            )
        )
