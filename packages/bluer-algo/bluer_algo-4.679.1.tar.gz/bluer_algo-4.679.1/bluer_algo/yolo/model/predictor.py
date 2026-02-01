from ultralytics import YOLO
import numpy as np
from typing import Tuple, Dict, List
from collections import Counter
import cv2
import time

from bluer_options import string
from bluer_objects import objects
from bluer_objects.graphics.signature import add_signature
from bluer_objects import file
from bluer_objects.metadata import post_to_object

from bluer_algo.logger import logger
from bluer_algo.host import signature


class YoloPredictor:
    def __init__(self):
        self.object_name: str = ""
        self.model: YOLO = None
        self.image_size: int = 640

    @staticmethod
    def load(
        object_name: str,
        what: str = "best",  # best | last
        image_size: int = 640,
    ) -> Tuple[bool, "YoloPredictor"]:
        predictor = YoloPredictor()

        logger.info(
            "loading {} from {}/{} @ image-size={}".format(
                predictor.__class__.__name__,
                object_name,
                what,
                image_size,
            )
        )
        predictor.object_name = object_name

        try:
            model_filename = objects.path_of(
                object_name=object_name,
                filename=f"train/weights/{what}.pt",
            )

            predictor.model = YOLO(model_filename)
        except Exception as e:
            logger.error(e)
            return False, predictor

        logger.info(predictor.model)

        predictor.image_size = image_size

        return True, predictor

    def predict(
        self,
        image: np.ndarray,
        log: bool = True,
        header: List[str] = [],
        verbose: bool = False,
        line_width: int = 80,
        prediction_object_name: str = "",
        record_id: str = "",
        return_annotated_image: bool = False,
        annotated_image_scale: int = 1,
    ) -> Tuple[bool, Dict]:
        elapsed_time = time.time()
        try:
            list_of_detections = self.model.predict(
                source=image,
                imgsz=self.image_size,
            )
        except Exception as e:
            logger.error(e)
            return False, {}
        elapsed_time = time.time() - elapsed_time
        elapsed_time_as_str = "took {}".format(
            string.pretty_duration(
                elapsed_time,
                include_ms=True,
                short=True,
            )
        )
        logger.info(elapsed_time_as_str)

        if not list_of_detections:
            logger.error("no detections.")
            return False, {}

        if len(list_of_detections) != 1:
            logger.warning(f"expected 1 result, received {len(list_of_detections)}.")

        detection = list_of_detections[0]
        detection_as_str = " + ".join(
            [
                f"{count} x {class_name}"
                for class_name, count in dict(
                    Counter([self.model.names[int(box.cls)] for box in detection.boxes])
                ).items()
            ]
        )
        detections_as_str = f"{len(detection.boxes)} detection(s): {detection_as_str}"
        if log:
            logger.info(detections_as_str)

        metadata = {
            "detections": [],
            "elapsed_time": elapsed_time,
            "image_size": list(detection.orig_shape),  # (H, W)
        }
        for box in detection.boxes:
            class_id = int(box.cls[0])
            metadata["detections"].append(
                {
                    "class_id": class_id,
                    "label": self.model.names[class_id],
                    "confidence": float(box.conf[0]),
                    "bbox_xyxy": box.xyxy[0].cpu().numpy().tolist(),  # [x1, y1, x2, y2]
                }
            )

        metadata["detections"] = sorted(
            metadata["detections"],
            key=lambda detection: detection["confidence"],
            reverse=True,
        )

        annotated_image = np.array([])

        if verbose or return_annotated_image:
            annotated_image = detection.plot()

            if annotated_image_scale != 1:
                annotated_image = cv2.resize(
                    annotated_image,
                    (
                        int(annotated_image_scale * annotated_image.shape[1]),
                        int(annotated_image_scale * annotated_image.shape[0]),
                    ),
                    interpolation=cv2.INTER_NEAREST_EXACT,
                )

            annotated_image = add_signature(
                annotated_image,
                header=[
                    " | ".join(
                        ["yolo"]
                        + header
                        + [
                            f"model: {self.object_name}",
                            f"size: {self.model_size}",
                            f"image size: {self.image_size}",
                            elapsed_time_as_str,
                            detections_as_str,
                        ]
                    )
                ],
                footer=[" | ".join(signature())],
                line_width=line_width,
            )

        if return_annotated_image:
            metadata["annotated_image"] = annotated_image

        if not verbose:
            return True, metadata

        if not post_to_object(
            prediction_object_name,
            record_id,
            metadata,
        ):
            return False, metadata

        success = file.save_image(
            objects.path_of(
                object_name=prediction_object_name,
                filename=f"{record_id}.png",
            ),
            annotated_image,
            log=verbose,
        )

        return success, metadata

    @property
    def model_size(self) -> str:
        depth = self.model.model.yaml["depth_multiple"]
        width = self.model.model.yaml["width_multiple"]

        model_size = "unknown"
        if depth == 0.33 and width == 0.25:
            model_size = "nano"
        elif depth == 0.33 and width == 0.50:
            model_size = "small"
        elif depth == 0.67 and width == 0.75:
            model_size = "medium"
        elif depth == 1.0 and width == 1.0:
            model_size = "large"
        elif depth == 1.33 and width == 1.25:
            model_size = "x-large"

        return f"{model_size} ({depth}x{width})"
