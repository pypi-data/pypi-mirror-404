from typing import List

from blueness import module
from bluer_objects import file, objects

from bluer_algo import NAME
from bluer_algo.yolo.dataset.classes import YoloDataset
from bluer_algo.logger import logger


NAME = module.name(__file__, NAME)


def ingest(
    object_name: str,
    filter_classes: bool = False,
    classes: List[str] = [],
    log: bool = True,
    verbose: bool = False,
) -> bool:
    logger.info(
        "{}.ingest -{}> {}".format(
            NAME,
            "{}-".format("+".join(classes)) if filter_classes else "",
            object_name,
        )
    )

    if not file.copy(
        file.absolute(
            "../../../../assets/coco_128.yaml",
            file.path(__file__),
        ),
        objects.path_of(
            object_name=object_name,
            filename="metadata.yaml",
        ),
        log=log,
    ):
        return False

    dataset = YoloDataset(
        object_name=object_name,
    )
    if not dataset.save(verbose):
        return False

    if filter_classes:
        return dataset.filter(
            classes=classes,
            verbose=verbose,
        )

    return True
