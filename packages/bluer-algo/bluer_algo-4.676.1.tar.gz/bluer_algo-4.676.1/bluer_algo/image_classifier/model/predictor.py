from typing import Tuple, Dict, List
import torch
import numpy as np
import time
from PIL import Image
from torchvision import transforms
import matplotlib.pyplot as plt

from bluer_options import string
from bluer_objects import objects, file
from bluer_objects.metadata import get_from_object, post_to_object
from bluer_objects.graphics.signature import justify_text

from bluer_algo.image_classifier.model.model import TinyCNN
from bluer_algo.host import signature
from bluer_algo.logger import logger


class ImageClassifierPredictor:
    def __init__(self):
        self.object_name = ""
        self.class_count = 0
        self.dict_of_classes = {}
        self.model = None
        self.transform = None
        self.shape = []

    def as_str(self, what: str = "classes") -> str:
        if what == "classes":
            return "{} class(es): {}".format(
                self.class_count,
                ", ".join(
                    "#{}: {}".format(
                        class_index,
                        self.dict_of_classes[class_index],
                    )
                    for class_index in range(self.class_count)
                ),
            )

        return f"{what} not found."

    @staticmethod
    def load(object_name: str) -> Tuple[bool, "ImageClassifierPredictor"]:
        predictor = ImageClassifierPredictor()

        logger.info(
            "loading {} from {} ...".format(
                predictor.__class__.__name__,
                object_name,
            )
        )
        predictor.object_name = object_name

        metadata = get_from_object(
            object_name=predictor.object_name,
            key="model",
        )

        if "dataset" not in metadata:
            logger.error("dataset not found.")
            return False, predictor
        for thing in ["class_count", "classes", "shape"]:
            if thing not in metadata["dataset"]:
                logger.error(f"dataset.{thing} not found.")
                return False, predictor

        predictor.class_count = metadata["dataset"]["class_count"]
        predictor.dict_of_classes = metadata["dataset"]["classes"]
        logger.info(predictor.as_str(what="classes"))

        predictor.shape = metadata["dataset"]["shape"]
        logger.info("shape: {}".format(predictor.shape))

        model_filename = objects.path_of(
            object_name=predictor.object_name,
            filename="model.pth",
        )

        try:
            predictor.model = TinyCNN(predictor.class_count)
            predictor.model.load_state_dict(
                torch.load(
                    model_filename,
                    map_location="cpu",
                )
            )
            predictor.model.eval()
        except Exception as e:
            logger.error(e)
            return False, predictor

        # Apply same transform as training
        logger.info(
            "transforms: {} x {}".format(
                predictor.shape[0],
                predictor.shape[1],
            )
        )
        predictor.transform = transforms.Compose(
            [
                transforms.Resize((predictor.shape[0], predictor.shape[1])),
                transforms.ToTensor(),
            ]
        )

        return True, predictor

    def predict(
        self,
        image: np.ndarray,
        class_index: int = -1,
        object_name: str = "",
        log: bool = True,
        line_width: int = 80,
    ) -> Tuple[bool, Dict]:
        # np_img is shape (H, W, 3) in RGB
        if not isinstance(image, np.ndarray):
            logger.error(f"{image.__class__.__name__} not supported.")
            return False, {}

        if not (image.ndim == 3 and image.shape[2] == self.shape[2]):
            logger.error("color image expected.")
            return False, {}

        elapsed_time = time.time()

        try:
            # Convert to PIL for transforms
            image_ = Image.fromarray(image.astype("uint8"))

            input_tensor = self.transform(image_).unsqueeze(
                0
            )  # Shape: [1, 3, 100, 100]

            with torch.no_grad():
                output = self.model(input_tensor)
                predicted_class = torch.argmax(output, dim=1).item()

            elapsed_time = time.time() - elapsed_time
        except Exception as e:
            logger.error(e)
            return False, {}

        if log:
            logger.info(
                "prediction: {} [#{}]{}- took {}".format(
                    self.dict_of_classes[predicted_class],
                    predicted_class,
                    (
                        ""
                        if class_index == -1
                        else (
                            " ✅ "
                            if class_index == predicted_class
                            else "<❗️> {} [#{}]".format(
                                self.dict_of_classes[class_index],
                                class_index,
                            )
                        )
                    ),
                    string.pretty_duration(
                        elapsed_time,
                        include_ms=True,
                        short=True,
                    ),
                )
            )

        if object_name:
            plt.figure(figsize=(5, 5))
            plt.imshow(image)
            plt.title(
                justify_text(
                    " | ".join(
                        objects.signature(object_name=object_name)
                        + self.signature()
                        + [
                            "prediction: {} [#{}]".format(
                                self.dict_of_classes[predicted_class],
                                predicted_class,
                            )
                        ]
                        + (
                            []
                            if class_index == -1
                            else [
                                (
                                    "correct"
                                    if class_index == predicted_class
                                    else "! label: {} [#{}]".format(
                                        self.dict_of_classes[class_index],
                                        class_index,
                                    )
                                )
                            ]
                        )
                        + [
                            "took {}".format(
                                string.pretty_duration(
                                    elapsed_time,
                                    include_ms=True,
                                    short=True,
                                ),
                            ),
                        ]
                        + signature()
                    ),
                    line_width=line_width,
                    return_str=True,
                )
            )
            plt.axis("off")
            if not file.save_fig(
                objects.path_of(
                    object_name=object_name,
                    filename="prediction.png",
                )
            ):
                return False, {}

        prediction = {
            "elapsed_time": elapsed_time,
            "predicted_class": int(predicted_class),
        }

        if object_name:
            if not post_to_object(
                object_name=object_name,
                key="prediction",
                value=prediction,
            ):
                return False, {}

        return True, prediction

    def signature(self) -> List[str]:
        return [
            f"model: {self.object_name}",
            self.as_str("classes"),
            "shape: {}".format(string.pretty_shape(self.shape)),
        ]
