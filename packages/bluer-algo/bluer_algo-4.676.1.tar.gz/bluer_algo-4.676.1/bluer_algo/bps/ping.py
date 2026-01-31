import random
from typing import Dict
import hashlib

from bluer_options.env import abcli_hostname

from bluer_algo.logger import logger


class Ping:
    def __init__(
        self,
        as_dict: Dict[str, float] = {},
        log: bool = True,
    ):
        self.x = as_dict.get("x", 0.0)
        self.y = as_dict.get("y", 0.0)
        self.z = as_dict.get("z", 0.0)
        self.sigma = as_dict.get("sigma", 1000.0)
        self.tx_power = as_dict.get("tx_power", -1.0)  # -1: unknown
        self.rssi = as_dict.get("rssi", -1.0)  # -1: unknown

        self.hostname = as_dict.get("hostname", abcli_hostname)

        if log:
            logger.info(self.as_str())

    def as_dict(self) -> dict:
        return {
            "hostname": self.hostname,
            "x": self.x,
            "y": self.y,
            "z": self.z,
            "sigma": self.sigma,
            "tx_power": self.tx_power,
            "rssi": self.rssi,
        }

    def as_str(
        self,
        include_id: str = False,
    ) -> str:
        return ", ".join(
            [
                "{}{} from {} @ [{:.2f} {:.2f} {:.2f}] +- {:.2f} m".format(
                    self.__class__.__name__,
                    f"[{self.id}]" if include_id else "",
                    self.hostname,
                    self.x,
                    self.y,
                    self.z,
                    self.sigma,
                )
            ]
            + [
                "{}: {:.2f} dBm".format(param_name, param_value)
                for param_name, param_value in {
                    "tx-power": self.tx_power,
                    "rssi": self.rssi,
                }.items()
                if param_value != -1
            ]
        )

    @property
    def id(self) -> str:
        return hashlib.sha256(
            self.as_str(include_id=False).encode("utf-8")
        ).hexdigest()[:8]

    @classmethod
    def simulate(
        cls,
        min: float = 0.0,
        max: float = 100.0,
        log: bool = True,
    ) -> "Ping":
        return cls(
            {
                "x": random.uniform(min, max),
                "y": random.uniform(min, max),
                "z": random.uniform(min, max),
                "sigma": random.uniform(min, max),
            },
            log=log,
        )
