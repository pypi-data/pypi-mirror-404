import os
from typing import Dict
import random

from blueness import module
from bluer_options.logger import log_list
from bluer_objects import path

from bluer_algo import NAME
from bluer_algo.env import BLUER_ALGO_FRUITS_360_REPO_PATH
from bluer_algo.logger import logger


NAME = module.name(__file__, NAME)


def get_classes(
    class_count: int = -1,
    shuffle: bool = True,
) -> Dict[str, int]:
    logger.info(
        "{}.get_classes{}".format(
            NAME,
            "" if class_count == -1 else f": {class_count} class(es)",
        )
    )

    training_path = os.path.join(BLUER_ALGO_FRUITS_360_REPO_PATH, "Training")
    logger.info(f"reading {training_path} ...")

    list_of_classes = [path.name(path_) for path_ in path.list_of(training_path)]

    if shuffle:
        random.shuffle(list_of_classes)

    if class_count != -1:
        list_of_classes = list_of_classes[:class_count]

    list_of_classes = sorted(list_of_classes)
    log_list(
        logger,
        "found",
        list_of_classes,
        "class(es)",
        itemize=False,
    )

    return {
        class_index: class_name
        for class_name, class_index in zip(
            list_of_classes,
            range(len(list_of_classes)),
        )
    }
