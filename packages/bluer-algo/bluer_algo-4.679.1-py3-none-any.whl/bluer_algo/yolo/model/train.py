from typing import Dict, Any
from ultralytics import YOLO

from blueness import module
from bluer_objects import objects
from bluer_objects.metadata import post_to_object, flatten

from bluer_algo import NAME
from bluer_algo.yolo.model.size import ModelSize
from bluer_algo.logger import logger


NAME = module.name(__file__, NAME)


def train(
    dataset_object_name: str,
    model_object_name: str,
    epochs: int = 30,
    image_size: int = 640,
    batch: int = 8,
    device: str = None,
    workers: int = 4,
    model_size: ModelSize = ModelSize.NANO,
    from_scratch: bool = False,
    validate: bool = True,
    verbose: bool = False,
) -> bool:
    metadata: Dict[str, Any] = {}

    logger.info(
        "{}.train: {} -{}-epochs-{}-pixels-{}-batch:{}-on:{}-{}-workers-size:{}-{}> {}".format(
            NAME,
            dataset_object_name,
            epochs,
            image_size,
            batch,
            device,
            workers,
            model_size.name.lower(),
            "from-scratch" if from_scratch else "transfer-learning",
            "validate-" if validate else "",
            model_object_name,
        )
    )

    if from_scratch:
        logger.info(f"training from scratch, using {model_size.model_yaml}")
        model = YOLO(model_size.model_yaml)
    else:
        logger.info(f"transfer learning, from {model_size.pretrained}")
        model = YOLO(model_size.pretrained)

    train_metrics = model.train(
        data=objects.path_of(
            object_name=dataset_object_name,
            filename="metadata.yaml",
        ),  # path to your coco128.yaml
        epochs=epochs,
        imgsz=image_size,
        batch=batch,
        device=device,  # e.g., '0' for GPU 0 or 'cpu'
        workers=workers,
        project=objects.object_path(object_name=model_object_name),
        name="train",
        verbose=True,
        seed=0,  # reproducibility (as much as possible)
        close_mosaic=10,  # a small quality bump near the end
    )
    logger.info("training complete.")
    if verbose:
        logger.info(f"training metrics: {train_metrics}")
    metadata["train"] = train_metrics

    if validate:
        logger.info("validating the best checkpoint...")

        # gives mAP, precision/recall, etc.
        val_metrics = model.val(
            data=objects.path_of(
                object_name=dataset_object_name,
                filename="metadata.yaml",
            ),
            imgsz=image_size,
            device=device,
            name="validation",
        )
        if verbose:
            logger.info(
                f"validation metrics: {val_metrics}",
            )
        metadata["validation"] = val_metrics

    return post_to_object(
        model_object_name,
        "train",
        flatten(metadata),
    )
