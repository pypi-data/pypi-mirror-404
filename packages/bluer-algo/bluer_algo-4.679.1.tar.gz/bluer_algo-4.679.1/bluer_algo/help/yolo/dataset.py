from typing import List

from bluer_options.terminal import show_usage, xtra

from bluer_algo.yolo.dataset.ingest import sources as ingest_sources


def help_ingest(
    tokens: List[str],
    mono: bool,
) -> str:
    options = "".join(
        [
            xtra("dryrun,", mono=mono),
            "source={},upload".format("|".join(ingest_sources)),
        ]
    )

    args = [
        "[--classes all | person+boat]",
        "[--verbose 1]",
    ]

    return show_usage(
        [
            "@yolo",
            "dataset",
            "ingest",
            f"[{options}]",
            "[-|<object-name>]",
        ]
        + args,
        "ingest -> <object-name>.",
        mono=mono,
    )


def help_review(
    tokens: List[str],
    mono: bool,
) -> str:
    options = xtra("~download,upload", mono=mono)

    args = [
        "[--verbose 1]",
    ]

    return show_usage(
        [
            "@yolo",
            "dataset",
            "review",
            f"[{options}]",
            "[.|<object-name>]",
        ]
        + args,
        "review <object-name>.",
        mono=mono,
    )


help_functions = {
    "ingest": help_ingest,
    "review": help_review,
}
