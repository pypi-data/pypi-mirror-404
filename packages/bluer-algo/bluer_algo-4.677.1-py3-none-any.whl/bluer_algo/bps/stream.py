from typing import List, Tuple
import matplotlib
import matplotlib.pyplot as plt
import random
import math

from bluer_objects import file, objects
from bluer_objects.graphics.signature import justify_text
from bluer_objects.metadata import post_to_object
from bluer_algo.bps.position import Position

from bluer_algo.bps.ping import Ping
from bluer_algo.host import signature
from bluer_algo.logger import logger


class Stream:
    def __init__(self):
        self.ping: Ping = Ping(log=False)
        self.history: List[Ping] = []

    def append(
        self,
        ping: Ping,
        log: bool = False,
    ) -> bool:
        if ping.id in [ping.id for ping in self.history]:
            if log:
                logger.info(f"repeat ping ignored: {ping.as_str()}")

            return False

        self.history.append(ping)
        if log:
            logger.info(f"🏓 # unique pings: {len(self.history)}")

        return True

    def estimate_position(self, object_name: str) -> Tuple[bool, Position]:
        logger.info("estimating position from {} ping(s)...".format(len(self.history)))

        logger.info("🪄")

        position = Position(
            x=0,
            y=0,
            z=0,
            sigma=1000,
        )
        logger.info(f"position: {position.as_str()}")

        return position.save(object_name), position

    def export(
        self,
        object_name: str,
        log: bool = True,
        line_width: int = 80,
    ) -> bool:
        if not post_to_object(
            object_name,
            "bps",
            {
                "ping": self.ping.as_dict(),
                "history": [ping.as_dict() for ping in self.history],
            },
        ):
            return False

        list_of_hostnames = self.list_of_hostnames()
        list_of_colors = [
            color
            for color in list(matplotlib.colors.BASE_COLORS.keys())
            if color != "gray"
        ]
        while len(list_of_colors) < len(list_of_hostnames):
            list_of_colors = list_of_colors + list_of_colors

        host_color = {
            hostname: color
            for hostname, color in zip(list_of_hostnames, list_of_colors)
        }

        plt.figure(figsize=(10, 10))

        for hostname in list_of_hostnames:
            plt.plot(
                [ping.x for ping in self.history if ping.hostname == hostname],
                [ping.y for ping in self.history if ping.hostname == hostname],
                "o",
                color=host_color[hostname],
                label=hostname,
            )

        if self.history:
            plt.legend()

        ax = plt.gca()

        for ping in self.history:
            circle = plt.Circle(
                (ping.x, ping.y),
                radius=ping.sigma,
                fill=False,
                color=host_color[ping.hostname],
                linestyle=":",
            )
            ax.add_artist(circle)

            theta = random.uniform(0, 360)

            ax.text(
                ping.x + ping.sigma * math.cos(theta),
                ping.y + ping.sigma * math.sin(theta),
                "{}rssi={:.2f} dBm".format(
                    (
                        "tx_power={:.2f} dBm, ".format(ping.tx_power)
                        if ping.tx_power != -1
                        else ""
                    ),
                    ping.rssi,
                ),
                ha="center",
                va="center",
                fontsize=12,
                color=host_color[ping.hostname],
            )

        plt.title(
            justify_text(
                " | ".join(
                    objects.signature(object_name=object_name) + self.signature()
                ),
                line_width=line_width,
                return_str=True,
            )
        )
        plt.xlabel(
            justify_text(
                " | ".join(["x (m)"] + signature()),
                line_width=line_width,
                return_str=True,
            )
        )
        plt.ylabel("y (m)")

        if self.history:
            max_x = max(ping.x + ping.sigma for ping in self.history)
            min_x = min(ping.x - ping.sigma for ping in self.history)
            max_y = max(ping.y + ping.sigma for ping in self.history)
            min_y = min(ping.y - ping.sigma for ping in self.history)
            range = max(max_x - min_x, max_y - min_y)
            plt.xlim(min_x - 0.1 * range, max_x + 0.1 * range)
            plt.ylim(min_y - 0.1 * range, max_y + 0.1 * range)

        plt.tight_layout()
        ax.set_aspect("equal", "box")
        plt.grid(True)
        return file.save_fig(
            objects.path_of(
                object_name=object_name,
                filename="bps.png",
            ),
            log=log,
        )

    def generate(
        self,
        simulate: bool = False,
        as_dict: dict = {},
    ):
        if simulate:
            logger.info("simulating stream...")
            self.ping = Ping.simulate()
        else:
            logger.info("generating stream...")
            self.ping = Ping(as_dict)

    def list_of_hostnames(self) -> List[str]:
        return list({ping.hostname for ping in self.history})

    @classmethod
    def load(cls, object_name: str) -> "Stream":
        _, stream = file.load(
            objects.path_of(
                object_name=object_name,
                filename="bps-stream.dill",
            ),
            default=Stream(),
            ignore_error=True,
        )
        assert isinstance(stream, Stream)

        logger.info(f"loaded {len(stream.history)} ping(s)")

        return stream

    def save(
        self,
        object_name: str,
        log: bool = True,
    ) -> bool:
        return file.save(
            objects.path_of(
                object_name=object_name,
                filename="bps-stream.dill",
            ),
            self,
            log=log,
        )

    def signature(self) -> List[str]:
        list_of_hostnames = self.list_of_hostnames()

        return [
            "{} ping(s)".format(len(self.history)),
            "{} hostname(s): {}".format(
                len(list_of_hostnames),
                ", ".join(list_of_hostnames),
            ),
        ]
