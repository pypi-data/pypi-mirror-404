from blueness import module

from bluer_algo import NAME
from bluer_algo.image_classifier.dataset.dataset import ImageClassifierDataset
from bluer_algo.logger import logger

NAME = module.name(__file__, NAME)


def sequence(
    source_object_name: str,
    destination_object_name: str,
    length: str,
    log: bool = True,
) -> bool:
    success, dataset = ImageClassifierDataset.load(
        object_name=source_object_name,
        log=log,
    )
    if not success:
        return success

    success, _ = dataset.sequence(
        length=length,
        object_name=destination_object_name,
        log=log,
    )

    return success
