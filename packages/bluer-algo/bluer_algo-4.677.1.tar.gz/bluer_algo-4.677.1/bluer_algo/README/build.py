import os

from bluer_options.help.functions import get_help
from bluer_objects import file, README

from bluer_algo import NAME, VERSION, ICON, REPO_NAME
from bluer_algo.help.functions import help_functions
from bluer_algo.README import (
    alias,
    bps,
    image_classifier,
    socket,
    tracker,
    yolo,
)
from bluer_algo.README.items import items


def build():
    return all(
        README.build(
            items=doc.get("items", []),
            path=os.path.join(file.path(__file__), doc["path"]),
            cols=doc.get("cols", 3),
            ICON=ICON,
            NAME=NAME,
            VERSION=VERSION,
            REPO_NAME=REPO_NAME,
            help_function=lambda tokens: get_help(
                tokens,
                help_functions,
                mono=True,
            ),
        )
        for doc in [
            {
                "path": "../docs",
            },
            {
                "path": "../..",
                "cols": 2,
                "items": items,
            },
        ]
        + alias.docs
        + bps.docs
        + image_classifier.docs
        + socket.docs
        + tracker.docs
        + yolo.docs
    )
