from typing import List

from bluer_options.terminal import show_usage, xtra

from bluer_algo import ALIAS


def help_prediction_test(
    tokens: List[str],
    mono: bool,
) -> str:
    options = "".join(
        [
            xtra("~download,upload", mono=mono),
        ]
    )

    return show_usage(
        [
            "@image_classifier",
            "model",
            "prediction_test",
            f"[{options}]",
            "[..|<dataset-object-name>]",
            "[.|<model-object-name>]",
            "[-|<prediction-object-name>]",
        ],
        "test prediction.",
        mono=mono,
    )


def help_train(
    tokens: List[str],
    mono: bool,
) -> str:
    options = xtra("~download,upload", mono=mono)

    args = [
        "[--batch_size 16]",
        "[--num_epochs 10]",
    ]

    return show_usage(
        [
            "@image_classifier",
            "model",
            "train",
            f"[{options}]",
            "[.|<dataset-object-name>]",
            "[-|<model-object-name>]",
        ]
        + args,
        "train.",
        mono=mono,
    )


help_functions = {
    "prediction_test": help_prediction_test,
    "train": help_train,
}
