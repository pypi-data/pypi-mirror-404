from typing import List

from bluer_options.terminal import show_usage, xtra

from bluer_algo.tracker.factory import LIST_OF_TRACKER_ALGO


def help_tracker(
    tokens: List[str],
    mono: bool,
) -> str:
    options = "".join(
        [
            "algo={},camera".format("|".join(LIST_OF_TRACKER_ALGO)),
            xtra(",~download,dryrun,sandbox,", mono=mono),
            "upload",
        ]
    )

    args = [
        "[--frame_count <10>]",
        "[--log 1]",
        "[--show_gui 1]",
        "[--verbose 1]",
    ]

    return show_usage(
        [
            "@algo",
            "tracker",
            f"[{options}]",
            "[-|<object-name>]",
        ]
        + args,
        "run algo.",
        mono=mono,
    )


def help_tracker_list(
    tokens: List[str],
    mono: bool,
) -> str:
    args = [
        "[--delim space | <delim>]",
        "[--log 1]",
    ]

    return show_usage(
        [
            "@algo",
            "tracker",
            "list",
        ]
        + args,
        "list algo.",
        mono=mono,
    )


help_functions = {
    "": help_tracker,
    "list": help_tracker_list,
}
