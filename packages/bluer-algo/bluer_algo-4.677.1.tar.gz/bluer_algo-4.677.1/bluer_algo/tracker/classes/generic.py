from typing import Tuple, Any, List
import numpy as np
import cv2

from bluer_options import string

from bluer_algo.logger import logger


class GenericTracker:
    algo = "generic"

    def __init__(
        self,
        with_gui: bool = False,
    ):
        self.roi_hist = None
        self.with_gui = with_gui

        self.history: List[Tuple[int, int]] = []

        # for camshift and meanshift
        # Setup the termination criteria, either 10 iteration or move by at least 1 pt
        self.term_crit = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 1)

        self.tracking: bool = True

        logger.info(
            "{} initialized{}.".format(
                self.__class__.__name__,
                " with gui" if with_gui else "",
            )
        )

    def start(
        self,
        frame: np.ndarray,
        track_window: Tuple[int, int, int, int],
    ):
        x, y, w, h = track_window

        logger.info(
            "{}.started on {} at ({},{},{},{})".format(
                self.__class__.__name__,
                string.pretty_shape_of_matrix(frame),
                x,
                y,
                w,
                h,
            )
        )

        # set up the ROI for tracking
        roi = frame[y : y + h, x : x + w]
        hsv_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(
            hsv_roi,
            np.array((0.0, 60.0, 32.0)),
            np.array((180.0, 255.0, 255.0)),
        )
        self.roi_hist = cv2.calcHist(
            [hsv_roi],
            [0],
            mask,
            [180],
            [0, 180],
        )
        cv2.normalize(
            self.roi_hist,
            self.roi_hist,
            0,
            255,
            cv2.NORM_MINMAX,
        )

    def track(
        self,
        frame: np.ndarray,
        track_window: Tuple[int, int, int, int],
        log: bool = False,
    ) -> Tuple[
        Any,
        Tuple[int, int, int, int],
        np.ndarray,
    ]:
        return None, [0, 0, 0, 0], np.array([])
