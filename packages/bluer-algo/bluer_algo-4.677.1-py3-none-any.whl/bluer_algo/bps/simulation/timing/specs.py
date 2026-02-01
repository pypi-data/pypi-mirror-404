from bluer_options import string

from bluer_algo import env


class Specs:
    def __init__(
        self,
        tao: int = 1,
        tac: int = 1,
        tro: int = 3,
        trc: int = 1,
        ta1: int = env.BLUER_AI_BPS_LOOP_BEACON_LENGTH_MIN,
        ta2: int = env.BLUER_AI_BPS_LOOP_BEACON_LENGTH_MAX,
        tr1: int = env.BLUER_AI_BPS_LOOP_RECEIVER_LENGTH_MIN,
        tr2: int = env.BLUER_AI_BPS_LOOP_RECEIVER_LENGTH_MAX,
    ):
        self.tao = tao
        self.tac = tac
        self.tro = tro
        self.trc = trc

        self.ta1 = ta1
        self.ta2 = ta2
        self.tr1 = tr1
        self.tr2 = tr2

    def as_str(self) -> str:
        return "ta:{} > {} - {} < {} | tr:{} > {} - {} < {}".format(
            string.pretty_minimal_duration(self.tao),
            string.pretty_minimal_duration(self.ta1),
            string.pretty_minimal_duration(self.ta2),
            string.pretty_minimal_duration(self.tac),
            string.pretty_minimal_duration(self.tro),
            string.pretty_minimal_duration(self.tr1),
            string.pretty_minimal_duration(self.tr2),
            string.pretty_minimal_duration(self.trc),
        )
