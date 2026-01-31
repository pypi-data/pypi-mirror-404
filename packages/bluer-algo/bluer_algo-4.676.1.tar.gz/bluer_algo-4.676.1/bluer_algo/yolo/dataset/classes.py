import os
import cv2
import os
import random
from tqdm import tqdm
import numpy as np
from typing import Dict, Any, List, Tuple
import pandas as pd

from blueness import module
from bluer_options.logger import log_list, log_list_as_str, crash_report
from bluer_options import host
from bluer_objects import objects, file, path
from bluer_objects.logger.image import log_image_grid
from bluer_objects.metadata import post_to_object

from bluer_algo import NAME
from bluer_algo.host import signature
from bluer_algo.logger import logger

NAME = module.name(__file__, NAME)


class YoloDataset:
    def __init__(
        self,
        object_name: str,
        log: bool = True,
        create: bool = False,
    ):
        self.object_name = object_name

        if create:
            self.valid = True

            self.metadata = {
                "dataset": {
                    "count": 0,
                },
                "names": {
                    0: "target",
                },
                "source": host.get_name(),
                "train": "images/train",
                "val": "images/val",
            }
        else:
            self.valid, self.metadata = file.load_yaml(
                objects.path_of(
                    object_name=object_name,
                    filename="metadata.yaml",
                )
            )

        self.train_images_path = os.path.join(
            objects.object_path(object_name),
            self.metadata.get("train", "void"),
        )
        if create:
            if not path.create(
                self.train_images_path,
                log=True,
            ):
                self.valid = False

        self.train_labels_path = self.train_images_path.replace(
            "images",
            "labels",
        )
        if create:
            if not path.create(
                self.train_labels_path,
                log=True,
            ):
                self.valid = False

        list_of_images = [
            file.name(filename)
            for filename in file.list_of(
                self.path_of(what="image", suffix="*.jpg"),
                recursive=False,
            )
        ]
        if log:
            logger.info(f"found {len(list_of_images)} image(s).")

        list_of_labels = [
            file.name(filename)
            for filename in file.list_of(
                self.path_of(what="label", suffix="*.txt"),
                recursive=False,
            )
        ]
        if log:
            logger.info(f"found {len(list_of_labels)} label(s).")

        self.list_of_records = [
            record_id for record_id in list_of_images if record_id in list_of_labels
        ]

        missing_images = [
            record_id
            for record_id in list_of_images
            if record_id not in self.list_of_records
        ]
        if missing_images and log:
            log_list(logger, "missing", missing_images, "image(s)", itemize=False)

        missing_labels = [
            record_id
            for record_id in list_of_labels
            if record_id not in self.list_of_records
        ]
        if missing_labels and log:
            log_list(logger, "missing", missing_labels, "label(s)", itemize=False)

        if log:
            logger.info(", ".join(self.signature()))

    @property
    def empty(self) -> bool:
        return len(self.list_of_records) == 0

    def filter(
        self,
        classes: List[str],
        verbose: bool = False,
    ) -> bool:
        if not self.valid:
            logger.error("invalid dataset.")
            return False

        logger.info(
            "{}.filter({})".format(
                self.__class__.__name__,
                "+".join(classes),
            )
        )

        index_map: Dict[int, int] = {}
        for index, class_name in enumerate(classes):
            if class_name not in self.metadata["names"].values():
                logger.error(f"{class_name} not found.")
                return False

            original_index = [
                index_
                for index_, class_name_ in self.metadata["names"].items()
                if class_name == class_name_
            ][0]
            logger.info(f"{class_name}: {original_index} -> {index}")

            index_map[original_index] = index

        list_of_records: List[str] = []
        for record_id in tqdm(self.list_of_records):
            filename = self.path_of_record(
                what="label",
                record_id=record_id,
            )
            success, df = self.load_label(record_id)
            if not success:
                return False

            df = df[df[0].isin(index_map.keys())]

            if df.empty:
                for what in ["image", "label"]:
                    if not file.delete(
                        self.path_of_record(
                            what=what,
                            record_id=record_id,
                        ),
                        log=verbose,
                    ):
                        return False
                continue

            list_of_records.append(record_id)

            if not self.save_label(record_id, df):
                crash_report(f"loading {filename}")
                return False
        self.list_of_records = list_of_records

        self.metadata["names"] = {
            index: class_name for index, class_name in zip(range(len(classes)), classes)
        }
        return self.save(verbose)

    def load_image(
        self,
        record_id: str,
        verbose: bool = False,
    ) -> Tuple[bool, np.ndarray]:
        success, image = file.load_image(
            self.path_of_record(
                what="image",
                record_id=record_id,
            ),
            log=verbose,
        )

        if success:
            image = np.ascontiguousarray(image)

        return success, image

    def load_label(
        self,
        record_id: str,
    ) -> Tuple[bool, pd.DataFrame]:
        try:
            df = pd.read_csv(
                self.path_of_record(
                    what="label",
                    record_id=record_id,
                ),
                sep=" ",
                header=None,
            )
        except:
            crash_report(f"load_label({record_id})")
            return False, pd.DataFrame()

        return True, df

    def path_of(
        self,
        suffix: str,
        what: str = "filename",  # filename | dir | image | label
        create: bool = True,
    ) -> str:
        if what in ["filename", "dir"]:
            output = objects.path_of(
                object_name=self.object_name,
                filename=suffix,
            )
            if what == "dir" and create:
                if not path.create(output):
                    output = f"cannot-create-{what}"

            return output

        if what == "image":
            return os.path.join(self.train_images_path, suffix)

        if what == "label":
            return os.path.join(self.train_labels_path, suffix)

        logger.error(f"path_of: {what}: not found.")
        return f"{what}-not-found"

    def path_of_record(
        self,
        record_id: str,
        what: str = "image",  # image | label
    ) -> str:
        return self.path_of(
            suffix=(
                f"{record_id}.jpg"
                if what == "image"
                else f"{record_id}.txt" if what == "label" else f"{what}-not-found"
            ),
            what=what,
        )

    def review(
        self,
        verbose: bool = False,
        cols: int = 3,
        rows: int = 2,
    ) -> bool:
        if not self.valid:
            logger.error("invalid dataset.")
            return False

        output_dir = self.path_of(what="dir", suffix="review")

        list_of_records = random.sample(
            self.list_of_records,
            min(
                cols * rows,
                len(self.list_of_records),
            ),
        )

        items: List[Dict[str, Any]] = []
        for record_id in tqdm(list_of_records):
            success, image = self.load_image(record_id, verbose)
            if not success:
                return success

            success, label_info = file.load_text(
                self.path_of_record(
                    what="label",
                    record_id=record_id,
                ),
                log=verbose,
            )
            if not success:
                return success
            try:
                h, w = image.shape[:2]
                for line in label_info:
                    cls, x, y, bw, bh = map(float, line.strip().split())
                    x1, y1 = int((x - bw / 2) * w), int((y - bh / 2) * h)
                    x2, y2 = int((x + bw / 2) * w), int((y + bh / 2) * h)
                    cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(
                        image,
                        self.metadata["names"][int(cls)],
                        (x1, y1 - 5),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        (0, 255, 0),
                        1,
                    )
            except Exception as e:
                logger.error(f'error in line "{line}": {e}')
                return False

            output_filename = os.path.join(
                output_dir,
                f"{record_id}.jpg",
            )
            if not file.save_image(
                output_filename,
                image,
                log=verbose,
            ):
                return False

            items.append({"filename": output_filename})

        return log_image_grid(
            items,
            cols=cols,
            rows=rows,
            scale=8,
            verbose=verbose,
            filename=objects.path_of(
                object_name=self.object_name,
                filename="review.png",
            ),
            header=[
                f"count: {len(self.list_of_records)}",
                log_list_as_str(
                    title="",
                    list_of_items=list(self.metadata["names"].values()),
                    item_name_plural="class(es)",
                ),
            ],
            footer=signature(),
            log=verbose,
        )

    def save(self, verbose: bool = False) -> bool:
        if not self.valid:
            logger.error("invalid dataset.")
            return False

        if not file.save_yaml(
            self.path_of("metadata.yaml"),
            self.metadata,
            log=verbose,
        ):
            return False
        if not post_to_object(
            self.object_name,
            "dataset",
            {
                "count": len(self.list_of_records),
            },
        ):
            return False

        logger.info(
            "{} -> {}".format(
                ", ".join(self.signature()),
                self.object_name,
            )
        )

        return True

    def save_label(
        self,
        record_id: str,
        df: pd.DataFrame,
    ) -> bool:
        try:
            df.to_csv(
                self.path_of_record(
                    what="label",
                    record_id=record_id,
                ),
                sep=" ",
                header=False,
                index=False,
                float_format="%.6f",
            )
        except:
            crash_report(f"save_label({record_id})")
            return False

        return True

    def signature(self) -> List[str]:
        dict_of_classes = self.metadata.get("names", {})

        return [
            self.__class__.__name__,
            "{} record(s)".format(
                len(self.list_of_records),
            ),
            log_list_as_str(
                "",
                [dict_of_classes[index] for index in range(len(dict_of_classes))],
                "class(es)",
            ),
        ]
