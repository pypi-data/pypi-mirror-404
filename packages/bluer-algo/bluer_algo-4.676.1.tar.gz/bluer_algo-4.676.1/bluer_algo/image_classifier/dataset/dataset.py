import copy
import pandas as pd
from typing import Dict, Tuple, List
import numpy as np
from tqdm import tqdm
import random
import re
from datetime import datetime
import matplotlib.pyplot as plt

from blueness import module
from bluer_options import string
from bluer_objects import objects, file
from bluer_objects.graphics.signature import justify_text
from bluer_objects.metadata import post_to_object
from bluer_objects.logger.image import log_image_grid
from bluer_objects.metadata import get_from_object

from bluer_algo import NAME
from bluer_algo.host import signature
from bluer_algo.logger import logger

NAME = module.name(__file__, NAME)


class ImageClassifierDataset:
    def __init__(
        self,
        dict_of_classes: Dict = {},
        object_name: str = "",
    ):
        self.list_of_subsets = ["train", "test", "eval"]

        self.df = pd.DataFrame(
            columns=[
                "filename",
                "class_index",
                "subset",
            ]
        )

        self.dict_of_classes = dict_of_classes.copy()

        self.object_name = object_name

        self.shape = []

    def add(
        self,
        filename: str,
        class_index: int,
        subset: str = "train",
        log: bool = False,
    ) -> bool:
        filename = file.name_and_extension(filename)

        self.df.loc[len(self.df)] = {
            "filename": filename,
            "class_index": class_index,
            "subset": subset,
        }

        if log:
            logger.info(
                "{} += {} : {}/{}".format(
                    self.__class__.__name__,
                    filename,
                    subset,
                    self.dict_of_classes[class_index],
                )
            )

        if self.shape:
            return True

        success, image = file.load_image(
            objects.path_of(
                object_name=self.object_name,
                filename=filename,
            )
        )
        if not success:
            return False

        self.shape = list(image.shape)
        logger.info(
            "shape: {}".format(
                string.pretty_shape(self.shape),
            )
        )

        return True

    def as_str(self, what="subsets") -> str:
        count = self.count

        if what == "classes":
            return "{} class(es): {}".format(
                self.class_count,
                ", ".join(
                    [
                        "{}: {} [%{:.1f}]".format(
                            self.dict_of_classes[class_index],
                            class_count,
                            0.0 if count == 0 else class_count / count * 100,
                        )
                        for class_index, class_count in self.dict_of_class_counts.items()
                    ]
                ),
            )

        if what == "subsets":
            return "{} subset(s): {}".format(
                len(self.list_of_subsets),
                ", ".join(
                    [
                        "{}: {} [%{:.1f}]".format(
                            subset,
                            subset_count,
                            0.0 if count == 0 else subset_count / count * 100,
                        )
                        for subset, subset_count in self.dict_of_subsets.items()
                    ]
                ),
            )

        return f"{what} not found."

    @property
    def class_count(self) -> int:
        return len(self.dict_of_classes)

    @staticmethod
    def combine(
        list_of_datasets: List["ImageClassifierDataset"],
        object_name: str,
        split: bool = True,
        test_ratio: float = 0.1,
        train_ratio: float = 0.8,
        log: bool = True,
        verbose: bool = False,
    ) -> Tuple[bool, "ImageClassifierDataset"]:
        if not list_of_datasets:
            return False, None

        eval_ratio = 1 - train_ratio - test_ratio
        if eval_ratio <= 0:
            logger.error(f"eval_ratio = {eval_ratio:.2f} <= 0")
            return False, None

        dataset = None
        for i, dataset_ in tqdm(enumerate(list_of_datasets)):
            if not i:
                dataset = ImageClassifierDataset(
                    dict_of_classes=dataset_.dict_of_classes,
                    object_name=object_name,
                )

                dataset.shape = copy.deepcopy(dataset_.shape)
            else:
                if dataset.dict_of_classes != dataset_.dict_of_classes:
                    logger.error(
                        "different classes: {} <> {}".format(
                            dataset.dict_of_classes,
                            dataset_.dict_of_classes,
                        )
                    )
                    return False, dataset

                if dataset.shape != dataset_.shape:
                    logger.error(
                        "different shapes: {} <> {}".format(
                            dataset.shape,
                            dataset_.shape,
                        )
                    )
                    return False, dataset

            if not file.copy(
                objects.path_of(
                    filename="grid.png",
                    object_name=dataset_.object_name,
                ),
                objects.path_of(
                    filename=f"grid-{i:03d}.png",
                    object_name=object_name,
                ),
                log=verbose,
            ):
                return False, dataset

            for _, row in tqdm(dataset_.df.iterrows()):
                filename = "{}-{:03d}.{}".format(
                    file.name(row["filename"]),
                    i,
                    file.extension(row["filename"]),
                )
                if not file.copy(
                    objects.path_of(
                        filename=row["filename"],
                        object_name=dataset_.object_name,
                    ),
                    objects.path_of(
                        filename=filename,
                        object_name=object_name,
                    ),
                    log=verbose,
                ):
                    return False, dataset

                if not dataset.add(
                    filename=filename,
                    class_index=row["class_index"],
                    subset=(
                        random.choices(
                            population=dataset.list_of_subsets,
                            weights=[train_ratio, test_ratio, eval_ratio],
                            k=1,
                        )[0]
                        if split
                        else row["subset"]
                    ),
                    log=verbose,
                ):
                    return False, dataset

        dataset.df.reset_index(drop=True, inplace=True)

        return True, dataset

    @property
    def count(self) -> int:
        return len(self.df)

    @property
    def dict_of_class_counts(self) -> Dict[int, int]:
        return {
            class_index: self.df[self.df["class_index"] == class_index].shape[0]
            for class_index in self.dict_of_classes.keys()
        }

    @property
    def dict_of_subsets(self) -> Dict[str, int]:
        return {
            subset_name: self.df[self.df["subset"] == subset_name].shape[0]
            for subset_name in self.list_of_subsets
        }

    def generate_timeline(
        self,
        log: bool = True,
        line_width: int = 80,
    ) -> bool:
        df = self.df.copy()

        pattern = re.compile(r"(\d{4}-\d{2}-\d{2}-\d{2}-\d{2}-\d{2})-[a-z0-9]+\.png")

        if not df["filename"].apply(lambda x: bool(pattern.fullmatch(x))).all():
            logger.warning("Not all filenames match the expected timestamp pattern.")
            return True

        df["datetime"] = df["filename"].apply(
            lambda x: datetime.strptime(
                pattern.match(x).group(1),
                "%Y-%m-%d-%H-%M-%S",
            )
        )

        df = df.sort_values(by="datetime")

        plt.figure(figsize=(10, 4))
        plt.plot(df["datetime"], df["class_index"], marker="o")
        plt.title(
            justify_text(
                " | ".join(
                    objects.signature(object_name=self.object_name) + self.signature()
                ),
                line_width=line_width,
                return_str=True,
            )
        )
        plt.xlabel(
            justify_text(
                " | ".join(["acquisition time"] + signature()),
                line_width=line_width,
                return_str=True,
            )
        )
        plt.ylabel("label")
        plt.xticks(rotation=45)
        plt.yticks(
            ticks=sorted(self.dict_of_classes.keys()),
            labels=[
                self.dict_of_classes[i] for i in sorted(self.dict_of_classes.keys())
            ],
        )
        plt.tight_layout()
        plt.grid(True)
        return file.save_fig(
            objects.path_of(
                object_name=self.object_name,
                filename="grid-timeline.png",
            ),
            log=log,
        )

    @staticmethod
    def load(
        object_name: str,
        log: bool = True,
    ) -> Tuple[bool, "ImageClassifierDataset"]:
        dataset = ImageClassifierDataset(object_name=object_name)

        logger.info(
            "loading {} from {} ...".format(
                dataset.__class__.__name__,
                object_name,
            )
        )

        success, dataset.df = file.load_dataframe(
            objects.path_of(
                object_name=object_name,
                filename="metadata.csv",
            ),
            log=log,
        )
        if not success:
            return False, dataset

        metadata = get_from_object(
            object_name=object_name,
            key="dataset",
        )

        for thing in ["classes", "shape"]:
            if thing not in metadata:
                logger.error(f"{thing} not found.")
                return False, dataset

        dataset.dict_of_classes = metadata["classes"]
        dataset.shape = metadata["shape"]

        logger.info(dataset.as_str("subsets"))
        logger.info(dataset.as_str("classes"))
        logger.info("shape: {}".format(string.pretty_shape(dataset.shape)))

        return True, dataset

    @staticmethod
    def load_list(
        list_of_object_names: List[str],
        log: bool = True,
    ) -> Tuple[bool, List["ImageClassifierDataset"]]:
        output: List[ImageClassifierDataset] = []

        for object_name in tqdm(list_of_object_names):
            success, dataset = ImageClassifierDataset.load(
                object_name=object_name,
                log=log,
            )
            if not success:
                return success, []

            output.append(dataset)

        return True, output

    def log_image_grid(
        self,
        log: bool = True,
        verbose: bool = False,
    ) -> bool:
        df = self.df.copy()

        if not df.empty:
            df["title"] = df.apply(
                lambda row: "#{}: {} @ {}".format(
                    row["class_index"],
                    self.dict_of_classes[row["class_index"]],
                    row["subset"],
                ),
                axis=1,
            )

        return log_image_grid(
            df,
            objects.path_of(
                object_name=self.object_name,
                filename="grid.png",
            ),
            shuffle=True,
            header=[
                f"count: {self.count}",
                self.as_str("subsets"),
                self.as_str("classes"),
            ],
            footer=signature(),
            log=log,
            verbose=verbose,
            relative_path=True,
        )

    def sample(self, subset: str = "test") -> Tuple[bool, int, np.ndarray]:
        test_row = self.df[self.df["subset"] == subset].sample(n=1)

        success, image = file.load_image(
            objects.path_of(
                object_name=self.object_name,
                filename=test_row["filename"].values[0],
            )
        )
        if not success:
            return success, 0, np.array([])

        class_index = test_row["class_index"].values[0]
        return True, int(class_index), image

    def save(
        self,
        metadata: Dict = {},
        log: bool = True,
    ) -> bool:
        logger.info(self.as_str("subsets"))
        logger.info(self.as_str("classes"))

        metadata_ = copy.deepcopy(metadata)
        metadata_["classes"] = self.dict_of_classes
        metadata_["class_count"] = self.class_count
        metadata_["count"] = self.count
        metadata_["subsets"] = self.dict_of_subsets
        metadata_["shape"] = self.shape

        if not file.save_csv(
            objects.path_of(
                object_name=self.object_name,
                filename="metadata.csv",
            ),
            self.df,
            log=log,
        ):
            return False

        if not post_to_object(
            object_name=self.object_name,
            key="dataset",
            value=metadata_,
        ):
            return False

        if not self.log_image_grid(log=log):
            return False

        if not self.generate_timeline():
            return False

        logger.info(
            "{} x {} record(s) -> {}".format(
                self.count,
                string.pretty_shape(self.shape),
                self.object_name,
            )
        )

        return True

    def sequence(
        self,
        length: int,
        object_name: str,
        log: bool = True,
        verbose: bool = False,
    ) -> Tuple[bool, "ImageClassifierDataset"]:
        logger.info(
            "{}.sequence: {} -{}X-> {}".format(
                NAME,
                self.object_name,
                length,
                object_name,
            )
        )

        dataset = ImageClassifierDataset(
            dict_of_classes=self.dict_of_classes,
            object_name=object_name,
        )

        buffer: List[np.ndarray] = []
        for _, row in tqdm(self.df.iterrows()):
            success, image = file.load_image(
                objects.path_of(
                    object_name=self.object_name,
                    filename=row["filename"],
                ),
                log=verbose,
            )
            if not success:
                return False, dataset

            buffer.append(image)
            if len(buffer) > length:
                buffer = buffer[1:]

            if len(buffer) < length:
                logger.info("buffering ...")
                continue
            if len(buffer) > length:
                logger.error("buffer overflow - this must not happen.")
                return False, dataset

            if not file.save_image(
                objects.path_of(
                    object_name=object_name,
                    filename=row["filename"],
                ),
                np.hstack(buffer),
                log=verbose,
            ):
                return False, dataset

            if not dataset.add(
                filename=row["filename"],
                class_index=row["class_index"],
                subset=row["subset"],
                log=verbose,
            ):
                return False, dataset

        success = dataset.save(
            metadata={
                "length": length,
                "source": self.object_name,
            },
            log=log,
        )

        return success, dataset

    def signature(self) -> List[str]:
        return [
            f"{self.count} record(s)",
            self.as_str("subsets"),
            self.as_str("classes"),
            "shape: {}".format(string.pretty_shape(self.shape)),
        ]
