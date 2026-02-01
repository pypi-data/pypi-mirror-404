import cv2
from typing import List
import numpy as np

from blueness import module
from bluer_objects import file, objects
from bluer_objects.graphics.gif import generate_animated_gif
from bluer_objects.graphics.signature import add_signature
from bluer_options import string
from bluer_options.timer import Timer

from bluer_algo import NAME
from bluer_algo import env
from bluer_algo.host import signature
from bluer_algo.tracker.classes.target import Target
from bluer_algo.tracker.factory import get_tracker_class
from bluer_algo.logger import logger


NAME = module.name(__file__, NAME)


def track(
    source: str,
    object_name: str = "",
    algo: str = env.BLUER_ALGO_TRACKER_DEFAULT_ALGO,
    frame_count: int = -1,
    log: bool = False,
    verbose: bool = False,
    show_gui: bool = True,
    title: str = "",
    line_width: int = 80,
) -> bool:
    logger.info(
        "{}.track({}){}{}{} on {}".format(
            NAME,
            algo,
            "" if frame_count == -1 else " {} frame(s)".format(frame_count),
            " with gui" if show_gui else "",
            (
                " log every {}".format(
                    string.pretty_duration(env.BLUER_ALGO_TRACKER_LOG_PERIOD)
                    if source == "camera"
                    else string.pretty_duration(env.BLUER_ALGO_TRACKER_LOG_FRAME)
                )
                if log
                else ""
            ),
            source,
        )
    )

    if not title:
        title = f"tracker: {algo} - Esc to exit"

    log_timer = Timer(
        env.BLUER_ALGO_TRACKER_LOG_PERIOD if (log and source == "camera") else -1,
        "log_timer",
    )

    log_image_list: List[str] = []

    cap = cv2.VideoCapture(0 if source == "camera" else source)

    # take first frame of the video
    ret, frame = cap.read()
    if source == "camera" and not ret:
        logger.error("failed to grab initial frame from camera.")
        cap.release()
        return False

    # setup initial location of window
    if source == "camera":
        ret, frame = cap.read()
        success, roi = Target.select(
            frame,
            title="select target - Esc to exit",
        )
        if not success:
            logger.error("target not found.")
            cap.release()
            cv2.destroyAllWindows()
            return False

        x, y, w, h = roi
    else:
        x, y, w, h = 300, 200, 100, 50  # simply hardcoded the values
    track_window = (x, y, w, h)

    success, tracker_class = get_tracker_class(algo)
    if not success:
        return False

    tracker = tracker_class(with_gui=show_gui)
    tracker.start(
        frame=frame,
        track_window=track_window,
    )

    frame_index: int = 0
    while True:
        success, frame = cap.read()
        if not success:
            break

        frame_index += 1
        if frame_count != -1 and frame_index > frame_count:
            logger.info(f"frame_count={frame_count} reached.")
            break

        log_this_frame = (
            log_timer.tick()
            if source == "camera"
            else (frame_index % env.BLUER_ALGO_TRACKER_LOG_FRAME == 0)
        )

        ret, track_window, output_image = tracker.track(
            frame=frame,
            track_window=track_window,
            log=log_this_frame,
        )

        if log_this_frame:
            filename = objects.path_of(
                filename="frames/{}.png".format(string.timestamp()),
                object_name=object_name,
            )
            log_image_list.append(filename)

            if not file.save_image(
                filename,
                add_signature(
                    np.flip(output_image, axis=2),
                    header=[
                        " | ".join(
                            [f"frame #{frame_index:04d}"]
                            + objects.signature(
                                file.name_and_extension(filename),
                                object_name,
                            )
                            + [
                                f"algo: {algo}",
                                "source: {}".format(
                                    source
                                    if source == "camera"
                                    else file.name_and_extension(source)
                                ),
                                (
                                    "({:04d},{:04d}) - ({:04d},{:04d})".format(
                                        *track_window
                                    )
                                    if tracker.tracking
                                    else "lost"
                                ),
                            ]
                        )
                    ],
                    footer=[" | ".join(signature())],
                    line_width=line_width,
                ),
                log=verbose,
            ):
                break

        if verbose:
            logger.info(f"frame #{frame_index}: ret={ret}, track_window={track_window}")

        if show_gui:
            cv2.imshow(title, output_image)

            k = cv2.waitKey(30) & 0xFF
            if k == 27:
                break

    if source == "camera":
        cap.release()

    if show_gui:
        cv2.destroyAllWindows()

    if log and not generate_animated_gif(
        log_image_list,
        objects.path_of(
            filename="tracker.gif",
            object_name=object_name,
        ),
        log=log,
    ):
        return False

    return True
