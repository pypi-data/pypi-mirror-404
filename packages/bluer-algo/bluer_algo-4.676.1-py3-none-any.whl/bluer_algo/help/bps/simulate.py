from typing import List

from bluer_options.terminal import show_usage

from bluer_algo import env


def help_timing(
    tokens: List[str],
    mono: bool,
) -> str:
    options = "upload"

    args = [
        "[--length <1200>]",
        "[--anchors <4>]",
        "[--nodes <3>]",
        f"[--ta1 <{env.BLUER_AI_BPS_LOOP_BEACON_LENGTH_MIN:d}>]",
        f"[--ta2 <{env.BLUER_AI_BPS_LOOP_BEACON_LENGTH_MAX:d}>]",
        f"[--tr1 <{env.BLUER_AI_BPS_LOOP_RECEIVER_LENGTH_MIN:d}>]",
        f"[--tr2 <{env.BLUER_AI_BPS_LOOP_RECEIVER_LENGTH_MAX:d}>]",
        "[--verbose 1]",
    ]

    return show_usage(
        [
            "@bps",
            "simulate",
            "timing",
            f"[{options}]",
            "[-|<object-name>]",
        ]
        + args,
        "simulate timing.",
        mono=mono,
    )


help_functions = {
    "timing": help_timing,
}
