from typing import Tuple, Dict

from bluer_algo.image_classifier.dataset.dataset import ImageClassifierDataset
from bluer_algo.image_classifier.model.predictor import ImageClassifierPredictor


def prediction_test(
    dataset_object_name: str,
    model_object_name: str,
    prediction_object_name: str = "",
) -> Tuple[bool, Dict]:
    success, dataset = ImageClassifierDataset.load(
        object_name=dataset_object_name,
    )
    if not success:
        return False, {}

    success, predictor = ImageClassifierPredictor.load(
        object_name=model_object_name,
    )
    if not success:
        return False, {}

    success, class_index, image = dataset.sample(
        subset="test",
    )
    if not success:
        return False, {}

    return predictor.predict(
        image=image,
        class_index=class_index,
        object_name=prediction_object_name,
        log=True,
    )
