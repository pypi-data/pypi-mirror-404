from typing import List
import random
import numpy as np

from bluer_options import string

from bluer_algo.bps.simulation.timing.specs import Specs
from bluer_algo.bps.simulation.timing.state import State
from bluer_algo.logger import logger


class Node:
    def __init__(
        self,
        specs: Specs = Specs(),
        anchor: bool = False,
    ):
        self.specs = specs
        self.is_anchor = anchor

        self.history: List[State] = []
        self.legend: np.ndarray = np.zeros((1))

    def simulate(
        self,
        length: int = 1200,
        verbose: bool = False,
    ) -> bool:
        logger.info(
            "simulating {}[{}] for {}...".format(
                self.__class__.__name__,
                "anchor" if self.is_anchor else "node",
                string.pretty_minimal_duration(length),
            )
        )

        self.history = []
        while len(self.history) < length:
            ta = int(
                random.uniform(
                    self.specs.ta1,
                    self.specs.ta2,
                )
            )

            message: str = f"ta={ta}"

            slice = (
                self.specs.tao * [State.AO]
                + ta * [State.A]
                + self.specs.tac * [State.AC]
            )

            if not self.is_anchor:
                tr = int(
                    random.uniform(
                        self.specs.tr1,
                        self.specs.tr2,
                    )
                )

                message += f", tr={tr}"

                slice += (
                    self.specs.tro * [State.RO]
                    + tr * [State.R]
                    + self.specs.trc * [State.RC]
                )

            if verbose:
                logger.info(message)

            self.history += slice

        self.history = self.history[:length]

        self.legend = np.zeros((1, length, 3), dtype=np.uint8)
        for index, state in enumerate(self.history):
            self.legend[0, index] = state.color_code

        return True
