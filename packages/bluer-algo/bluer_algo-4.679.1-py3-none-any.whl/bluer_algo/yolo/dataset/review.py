from blueness import module

from bluer_algo import NAME
from bluer_algo.yolo.dataset.classes import YoloDataset
from bluer_algo.logger import logger


NAME = module.name(__file__, NAME)


def review(
    object_name: str,
    verbose: bool = False,
) -> bool:
    logger.info(f"{NAME}.review({object_name})")

    dataset = YoloDataset(
        object_name=object_name,
    )
    if not dataset.valid:
        return False

    return dataset.review(verbose=verbose)
