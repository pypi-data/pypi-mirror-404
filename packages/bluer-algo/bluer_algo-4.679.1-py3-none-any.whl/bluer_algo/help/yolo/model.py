from typing import List

from bluer_options.terminal import show_usage, xtra

from bluer_algo.yolo.model.size import ModelSize


def help_prediction_test(
    tokens: List[str],
    mono: bool,
) -> str:
    options = xtra("~download,upload", mono=mono)

    args = [
        "[--image_size 640]",
        "[--record_index 0]",
        "[--warmup 0]",
    ]

    return show_usage(
        [
            "@yolo",
            "model",
            "prediction_test",
            f"[{options}]",
            "[..|<dataset-object-name>]",
            "[.|<model-object-name>]",
            "[-|<prediction-object-name>]",
        ]
        + args,
        "test prediction.",
        mono=mono,
    )


def help_train(
    tokens: List[str],
    mono: bool,
) -> str:
    options = xtra("~download,upload", mono=mono)

    args = [
        "[--batch 8]",
        "[--device cpu | 0 | 0,1]",
        "[--epochs 30]",
        "[--from_scratch 1]",
        "[--image_size 640]",
        f"[--model_size {ModelSize.choices()}]",
        "[--validate 0]",
        "[--verbose 1]",
        "[--workers 4]",
    ]

    return show_usage(
        [
            "@yolo",
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
