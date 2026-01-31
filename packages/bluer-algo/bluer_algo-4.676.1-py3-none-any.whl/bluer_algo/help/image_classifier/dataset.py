from typing import List

from bluer_options.terminal import show_usage, xtra

from bluer_algo.image_classifier.dataset.ingest import sources as ingest_sources


def help_ingest(
    tokens: List[str],
    mono: bool,
) -> str:
    options = "".join(
        [
            "clone,count=<100>,source={}".format("|".join(ingest_sources)),
            xtra(",upload", mono=mono),
        ]
    )

    args = [
        "[--class_count -1]",
        "[--test_ratio 0.1]",
        "[--train_ratio 0.8]",
    ]

    return show_usage(
        [
            "@image_classifier",
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

    return show_usage(
        [
            "@image_classifier",
            "dataset",
            "review",
            f"[{options}]",
            "[.|<object-name>]",
        ],
        "review <object-name>.",
        mono=mono,
    )


def help_sequence(
    tokens: List[str],
    mono: bool,
) -> str:
    options = "".join(
        [
            xtra("~download,", mono=mono),
            "length=<2>",
            xtra(",upload", mono=mono),
        ]
    )

    return show_usage(
        [
            "@image_classifier",
            "dataset",
            "sequence",
            f"[{options}]",
            "[.|<source-object-name>]",
            "[-|<destination-object-name>]",
        ],
        "<source-object-name> -sequence-> <destination-object-name>.",
        mono=mono,
    )


help_functions = {
    "ingest": help_ingest,
    "review": help_review,
    "sequence": help_sequence,
}
