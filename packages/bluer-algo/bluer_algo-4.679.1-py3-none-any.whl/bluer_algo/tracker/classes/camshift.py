from typing import Tuple, Any
import numpy as np
import cv2

from bluer_algo.tracker.classes.generic import GenericTracker


class CamShiftTracker(GenericTracker):
    algo = "camshift"

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
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        dst = cv2.calcBackProject([hsv], [0], self.roi_hist, [0, 180], 1)

        # apply camshift to get the new location
        ret, track_window = cv2.CamShift(dst, track_window, self.term_crit)

        x, y, w, h = track_window
        self.history.append(
            (
                x + w // 2,
                y + h // 2,
            )
        )

        # draw track_window on image
        output_image = np.array([])
        if self.with_gui or log:
            pts = cv2.boxPoints(ret)
            pts = np.intp(pts)
            output_image = cv2.polylines(frame, [pts], True, 255, 2)

            for i in range(len(self.history) - 1):
                cv2.line(
                    output_image,
                    self.history[i],
                    self.history[i + 1],
                    color=(0, 255, 0),
                    thickness=2,
                )

        return ret, track_window, output_image
