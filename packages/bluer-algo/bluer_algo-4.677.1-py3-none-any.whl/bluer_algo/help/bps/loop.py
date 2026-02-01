from typing import List

from bluer_options.terminal import show_usage, xtra


def help_start(
    tokens: List[str],
    mono: bool,
) -> str:
    options = "".join(
        [
            xtra("simulate,", mono=mono),
            "upload",
        ]
    )

    return show_usage(
        [
            "@bps",
            "loop",
            "start",
            f"[{options}]",
            "[-|<object-name>]",
        ],
        "start bps loop.",
        mono=mono,
    )


def help_stop(
    tokens: List[str],
    mono: bool,
) -> str:
    options = xtra("rpi,wait", mono=mono)

    return show_usage(
        [
            "@bps",
            "loop",
            "stop",
            f"[{options}]",
            "[<machine-name>]",
        ],
        "stop bps loop.",
        mono=mono,
    )


help_functions = {
    "start": help_start,
    "stop": help_stop,
}
