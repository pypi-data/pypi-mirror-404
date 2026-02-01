from typing import List

from bluer_options.terminal import show_usage, xtra


def help_test(
    tokens: List[str],
    mono: bool,
) -> str:
    options = xtra("dryrun", mono=mono)

    args = [
        "[--host <host-name>]",
        "[--what receiving | sending]",
    ]

    return show_usage(
        [
            "@algo",
            "socket",
            "test",
            f"[{options}]",
        ]
        + args,
        "test socket.",
        mono=mono,
    )


help_functions = {
    "test": help_test,
}
