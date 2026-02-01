from enum import Enum


class ModelSize(Enum):
    NANO = "n"
    SMALL = "s"
    MEDIUM = "m"
    LARGE = "l"
    XLARGE = "x"

    @staticmethod
    def choices() -> str:
        return " | ".join(m.name.lower() for m in ModelSize)

    @property
    def model_yaml(self) -> str:
        return f"yolov8{self.value}.yaml"

    @property
    def pretrained(self) -> str:
        return f"yolov8{self.value}.pt"
