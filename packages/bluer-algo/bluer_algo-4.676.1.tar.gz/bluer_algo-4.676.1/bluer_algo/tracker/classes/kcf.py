from typing import Tuple, Any
import numpy as np
import cv2

from bluer_algo.tracker.classes.generic import GenericTracker
from bluer_algo.logger import logger


BBox = Tuple[int, int, int, int]


class KCFTracker(GenericTracker):
    algo = "kcf"

    def __init__(
        self,
        with_gui: bool = False,
        scales=(0.8, 0.9, 1.0, 1.1, 1.2),
        match_threshold: float = 0.6,
    ):
        super().__init__(with_gui)
        self.tracker = None
        self.is_started = False

        self.scales = scales
        self.match_threshold = match_threshold

        self.template_gray = None  # tight target template

    # ---------- helpers ----------

    @staticmethod
    def _clip_bbox(bbox: BBox, frame: np.ndarray) -> BBox:
        x, y, w, h = map(int, bbox)
        H, W = frame.shape[:2]
        x = max(0, min(x, W - 1))
        y = max(0, min(y, H - 1))
        w = max(1, min(w, W - x))
        h = max(1, min(h, H - y))
        return x, y, w, h

    def _extract_template(self, frame: np.ndarray, bbox: BBox):
        x, y, w, h = self._clip_bbox(bbox, frame)
        patch = frame[y : y + h, x : x + w]
        self.template_gray = cv2.cvtColor(patch, cv2.COLOR_BGR2GRAY)

    def _reacquire(self, frame: np.ndarray) -> Tuple[bool, BBox, float]:
        """
        Full-frame multi-scale template matching.
        """
        if self.template_gray is None:
            return False, None, -1.0

        frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        H, W = frame_gray.shape[:2]

        best_score = -1.0
        best_bbox = None

        for s in self.scales:
            tw = max(8, int(self.template_gray.shape[1] * s))
            th = max(8, int(self.template_gray.shape[0] * s))
            if tw >= W or th >= H:
                continue

            tpl = cv2.resize(self.template_gray, (tw, th))
            res = cv2.matchTemplate(frame_gray, tpl, cv2.TM_CCOEFF_NORMED)
            _, score, _, loc = cv2.minMaxLoc(res)

            if score > best_score:
                best_score = float(score)
                best_bbox = (loc[0], loc[1], tw, th)

        if best_score >= self.match_threshold:
            return True, self._clip_bbox(best_bbox, frame), best_score

        return False, None, best_score

    # ---------- API ----------

    def start(
        self,
        frame: np.ndarray,
        track_window: BBox,
    ):
        if frame is None or not isinstance(frame, np.ndarray):
            raise ValueError(f"{self.algo}.start: frame must be a numpy ndarray.")

        x, y, w, h = map(int, track_window)
        if w <= 0 or h <= 0:
            raise ValueError(f"{self.algo}.start: invalid track_window={track_window}.")

        self._extract_template(frame, track_window)

        # pylint:disable=c-extension-no-member
        self.tracker = cv2.legacy.TrackerKCF_create()
        ok = self.tracker.init(frame, (x, y, w, h))
        self.is_started = bool(ok)
        self.tracking = bool(ok)

        if ok:
            logger.info(f"{self.algo}.start: initialized with bbox={track_window}.")
        else:
            logger.error(f"{self.algo}.start: init failed.")

    def track(
        self,
        frame: np.ndarray,
        track_window: BBox,
        log: bool = False,
    ) -> Tuple[Any, BBox, np.ndarray]:

        if frame is None or not isinstance(frame, np.ndarray):
            raise ValueError(f"{self.algo}.track: frame must be a numpy ndarray.")

        output_image = frame.copy()

        # draw history
        if self.with_gui or log:
            for i in range(len(self.history) - 1):
                cv2.line(
                    output_image,
                    self.history[i],
                    self.history[i + 1],
                    (0, 255, 0),
                    2,
                )

        # ---------- REACQUIRE FIRST ----------
        ok, bbox, score = self._reacquire(frame)

        if ok:
            # re-init KCF at found location
            self.tracker = cv2.legacy.TrackerKCF_create()
            self.tracking = self.tracker.init(frame, bbox)
            updated = bbox

            x, y, w, h = bbox
            self.history.append((x + w // 2, y + h // 2))

            logger.info(f"{self.algo}.track: reacquired score={score:.2f} bbox={bbox}")
        else:
            self.tracking = False
            updated = track_window
            logger.warning(f"{self.algo}.track: lost (best score={score:.2f})")

        # ---------- RENDER ----------
        if self.with_gui or log:
            x, y, w, h = updated
            color = (0, 255, 0) if self.tracking else (0, 0, 255)
            cv2.rectangle(
                output_image,
                (x, y),
                (x + w, y + h),
                color,
                2,
            )
            cv2.putText(
                output_image,
                "KCF{}".format("" if self.tracking else ": lost"),
                (max(0, x), max(20, y - 8)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                color,
                2,
                cv2.LINE_AA,
            )

        return None, updated, output_image
