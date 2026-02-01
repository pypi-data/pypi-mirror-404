from typing import Tuple
import numpy as np
import cv2

from bluer_options import string
from bluer_options.env import abcli_hostname

from bluer_algo.socket.connection import SocketConnection, DEV_HOST, DEFAULT_PORT
from bluer_algo.logger import logger


class Target:

    @classmethod
    def select(
        cls,
        frame: np.ndarray,
        title: str = "select target",
        local: bool = True,
        port: int = DEFAULT_PORT,
    ) -> Tuple[bool, Tuple[int, int, int, int]]:
        logger.info(
            "{}: {} @ {} on {} ...".format(
                cls.__name__,
                title,
                "local" if local else "remote",
                string.pretty_shape_of_matrix(frame),
            )
        )

        if local:
            return cls.select_local(frame, title)

        return cls.select_remote(
            frame=frame,
            title=title,
            port=port,
        )

    @classmethod
    def select_local(
        cls,
        frame: np.ndarray,
        title: str = "select target",
    ) -> Tuple[bool, Tuple[int, int, int, int]]:
        roi_box = [0, 0, 0, 0]
        dragging = [False]

        def mouse_callback(event, x, y, flags, param):
            if event == cv2.EVENT_LBUTTONDOWN:
                roi_box[0], roi_box[1] = x, y
                dragging[0] = True
            elif event == cv2.EVENT_MOUSEMOVE and dragging[0]:
                roi_box[2], roi_box[3] = x - roi_box[0], y - roi_box[1]
            elif event == cv2.EVENT_LBUTTONUP:
                roi_box[2], roi_box[3] = x - roi_box[0], y - roi_box[1]
                dragging[0] = False

        cv2.namedWindow(title)
        cv2.setMouseCallback(title, mouse_callback)

        while True:
            temp_frame = frame.copy()
            if roi_box[2] and roi_box[3]:
                x, y, w, h = roi_box
                cv2.rectangle(temp_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.imshow(title, temp_frame)
            key = cv2.waitKey(1) & 0xFF
            if key in [13, 32]:  # ENTER or SPACE to confirm
                break
            if key == 27:  # ESC to cancel
                cv2.destroyWindow(title)
                return False, (0, 0, 0, 0)

        cv2.destroyWindow(title)
        cv2.waitKey(1)
        return True, tuple(roi_box)

    @classmethod
    def select_remote(
        cls,
        frame: np.ndarray,
        title: str = "select target",
        port: int = DEFAULT_PORT,
    ) -> Tuple[bool, Tuple[int, int, int, int]]:
        logger.info(
            'run "{}" on {}.'.format(
                f"@swallow select_target --host {abcli_hostname}.local",
                DEV_HOST,
            )
        )

        socket = SocketConnection.connect_to(
            target_host=DEV_HOST,
            port=port,
        )
        if not socket.send_data(frame):
            return False, (0, 0, 0, 0)

        socket = SocketConnection.listen_on(port=port)
        return socket.receive_data(tuple)
