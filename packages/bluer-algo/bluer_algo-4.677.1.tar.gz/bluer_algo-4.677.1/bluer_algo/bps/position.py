from filelock import FileLock
from typing import Dict, Tuple

from blueness import module
from bluer_objects import file, objects

from bluer_algo import NAME
from bluer_algo.logger import logger

NAME = module.name(__file__, NAME)


class Position:
    def __init__(
        self,
        x: float = 0.0,
        y: float = 0.0,
        z: float = 0.0,
        sigma: float = 1000.0,
    ):
        self.x = x
        self.y = y
        self.z = z
        self.sigma = sigma

    def as_dict(self) -> Dict[str, float]:
        return {
            "x": self.x,
            "y": self.y,
            "z": self.z,
            "sigma": self.sigma,
        }

    def as_str(self) -> str:
        return "{:.2f},{:.2f},{:.2f},{:.2f}".format(
            self.x,
            self.y,
            self.z,
            self.sigma,
        )

    @staticmethod
    def load(object_name: str) -> Tuple[bool, "Position"]:
        position = Position()

        filename = objects.path_of(
            object_name=object_name,
            filename="position.yaml",
        )
        lock = FileLock(filename + ".lock")

        with lock:
            success, data = file.load_yaml(filename)

        if not success:
            return success, position

        try:
            position.x = data["x"]
            position.y = data["y"]
            position.z = data["z"]
            position.sigma = data["sigma"]
        except Exception as e:
            logger.error(e)
            return False

        logger.info(
            "🎯 loaded {} from {}".format(
                position.as_str(),
                object_name,
            )
        )

        return True, position

    def save(
        self,
        object_name: str,
    ) -> bool:
        filename = objects.path_of(
            object_name=object_name,
            filename="position.yaml",
        )
        lock = FileLock(filename + ".lock")

        logger.info(
            "🎯 {} -> {}".format(
                self.as_str(),
                object_name,
            )
        )

        with lock:
            return file.save_yaml(
                filename,
                self.as_dict(),
            )
