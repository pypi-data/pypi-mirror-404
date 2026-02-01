import os
import random
from tqdm import trange, tqdm

from blueness import module
from bluer_objects import objects, file

from bluer_algo import NAME
from bluer_algo.image_classifier.dataset.dataset import ImageClassifierDataset
from bluer_algo.image_classifier.dataset.ingest.fruits_360.classes import get_classes
from bluer_algo.env import BLUER_ALGO_FRUITS_360_REPO_PATH
from bluer_algo.logger import logger


NAME = module.name(__file__, NAME)


def ingest(
    object_name: str,
    count: int = 100,
    class_count: int = -1,
    test_ratio: float = 0.1,
    train_ratio: float = 0.8,
    log: bool = True,
    verbose: bool = False,
) -> bool:
    eval_ratio = 1 - test_ratio - train_ratio
    if eval_ratio <= 0:
        logger.error(f"eval_ratio = {eval_ratio:.2f} < 0")
        return False

    logger.info(
        "{}.ingest -{}{}> {} @ train={:.2f}, eval={:.2f}, test={:.2f}".format(
            NAME,
            "" if class_count == -1 else f"{class_count}-class(es)-",
            f"{count}-record(s)-",
            object_name,
            train_ratio,
            eval_ratio,
            test_ratio,
        )
    )

    dataset = ImageClassifierDataset(
        dict_of_classes=get_classes(
            class_count=count if class_count == -1 else class_count,
        ),
        object_name=object_name,
    )

    record_count_per_class = int(count / dataset.class_count)
    for class_index in trange(dataset.class_count):
        record_class = dataset.dict_of_classes[class_index]

        logger.info(f"ingesting {record_class}")

        list_of_filenames = file.list_of(
            os.path.join(
                BLUER_ALGO_FRUITS_360_REPO_PATH,
                "Training",
                record_class,
                "*.jpg",
            )
        )
        list_of_filenames = list_of_filenames[:record_count_per_class]

        for source_filename in tqdm(list_of_filenames):
            destination_filename = "{}-{}".format(
                class_index,
                file.name_and_extension(source_filename),
            )

            if not file.copy(
                source_filename,
                objects.path_of(
                    object_name=object_name,
                    filename=destination_filename,
                ),
                log=verbose,
            ):
                return False

            record_subset = random.choices(
                population=dataset.list_of_subsets,
                weights=[train_ratio, test_ratio, eval_ratio],
                k=1,
            )[0]

            if not dataset.add(
                filename=destination_filename,
                class_index=class_index,
                subset=record_subset,
            ):
                return False

    return dataset.save(
        metadata={
            "ratios": {
                "eval": eval_ratio,
                "test": test_ratio,
                "train": train_ratio,
            },
            "source": "fruits_360",
        },
        log=log,
    )
