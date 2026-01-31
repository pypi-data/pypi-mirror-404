from blueness import module

from bluer_algo import NAME
from bluer_algo.image_classifier.dataset.dataset import ImageClassifierDataset
from bluer_algo.logger import logger


NAME = module.name(__file__, NAME)


def review(object_name: str) -> bool:
    logger.info(f"{NAME}.review({object_name})")

    success, dataset = ImageClassifierDataset.load(object_name=object_name)
    if not success:
        return success

    return all(
        [
            dataset.log_image_grid(log=True),
            dataset.generate_timeline(log=True),
        ]
    )
