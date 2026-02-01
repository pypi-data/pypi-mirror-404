from typing import Tuple, Union, List

from bluer_algo.tracker.classes.generic import GenericTracker
from bluer_algo.tracker.classes.camshift import CamShiftTracker
from bluer_algo.tracker.classes.kcf import KCFTracker
from bluer_algo.tracker.classes.klt import KLTTracker
from bluer_algo.tracker.classes.meanshift import MeanShiftTracker
from bluer_algo.logger import logger

LIST_OF_TRACKER_ALGO_CLASSES: List[type[GenericTracker]] = [
    CamShiftTracker,
    KCFTracker,
    KLTTracker,
    MeanShiftTracker,
]

LIST_OF_TRACKER_ALGO: List[str] = sorted(
    [tracker_class.algo for tracker_class in LIST_OF_TRACKER_ALGO_CLASSES]
)


def get_tracker_class(algo: str) -> Tuple[
    bool,
    Union[type[GenericTracker], None],
]:
    for tracker_class in LIST_OF_TRACKER_ALGO_CLASSES:
        if tracker_class.algo.lower() == algo.lower():
            return True, tracker_class

    logger.error(f"algo: {algo} not found.")
    return False, None
