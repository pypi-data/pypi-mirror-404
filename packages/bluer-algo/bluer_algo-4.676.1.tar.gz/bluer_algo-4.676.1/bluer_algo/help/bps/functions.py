from typing import List

from bluer_options.terminal import show_usage, xtra

from bluer_algo.help.bps.loop import help_functions as help_loop
from bluer_algo.help.bps.simulate import help_functions as help_simulate

generate_args = [
    "[--sigma <4.0>]",
    "[--simulate 1]",
    "[--x <1.0>]",
    "[--y <2.0>]",
    "[--z <3.0>]",
]


def help_beacon(
    tokens: List[str],
    mono: bool,
) -> str:
    options = xtra("~start_bluetooth", mono=mono)

    args = sorted(
        [
            "[--generate 1]",
            "[--spacing <2.0>]",
            "[--timeout <10.0 | -1>]",
        ]
        + generate_args
    )

    return show_usage(
        [
            "@bps",
            "beacon",
            f"[{options}]",
            "[-|<object-name>]",
        ]
        + args,
        "start beacon.",
        mono=mono,
    )


def help_generate(
    tokens: List[str],
    mono: bool,
) -> str:
    options = "-"

    args = sorted(
        [
            "[--as_str <x>,<y>,<z>,sigma]",
            "[--only_validate 1]",
        ]
        + generate_args
    )

    return show_usage(
        [
            "@bps",
            "generate",
            f"[{options}]",
            "[-|<object-name>]",
        ]
        + args,
        "generate a ping.",
        mono=mono,
    )


def help_install(
    tokens: List[str],
    mono: bool,
) -> str:
    return show_usage(
        [
            "@bps",
            "install",
        ],
        "install bps.",
        mono=mono,
    )


def help_introspect(
    tokens: List[str],
    mono: bool,
) -> str:
    options = "".join(
        [
            xtra("~start_bluetooth,verbose,", mono=mono),
            "unique_bus_name=<1:234>",
        ]
    )

    return show_usage(
        [
            "@bps",
            "introspect",
            f"[{options}]",
        ],
        "introspect <1:234>.",
        mono=mono,
    )


def help_receiver(
    tokens: List[str],
    mono: bool,
) -> str:
    options = xtra("~start_bluetooth,upload,verbose", mono=mono)

    args = [
        "[--grep <sparrow+swallow>]",
        "[--timeout <10>]",
    ]

    usage_1 = show_usage(
        [
            "@bps",
            "receiver",
            f"[{options}]",
            "[-|<object-name>]",
        ]
        + args,
        "start receiver.",
        mono=mono,
    )

    # ---
    options = xtra("~python,~start_bluetooth,verbose", mono=mono)

    usage_2 = show_usage(
        [
            "@bps",
            "receiver",
            f"[{options}]",
        ],
        "start receiver.",
        mono=mono,
    )

    return "\n".join(
        [
            usage_1,
            usage_2,
        ]
    )


def help_review(
    tokens: List[str],
    mono: bool,
) -> str:
    options = "~download,upload"

    return show_usage(
        [
            "@bps",
            "review",
            f"[{options}]",
            "[.|<object-name>]",
        ],
        "review <object-name>.",
        mono=mono,
    )


def help_set_anchor(
    tokens: List[str],
    mono: bool,
) -> str:
    return show_usage(
        [
            "@bps",
            "set_anchor",
            "clear | <1.1,2.2,3.3,4.4>",
        ],
        "set bps anchor.",
        mono=mono,
    )


def help_start_bluetooth(
    tokens: List[str],
    mono: bool,
) -> str:
    options = xtra("verbose", mono=mono)

    return show_usage(
        [
            "@bps",
            "start_bluetooth",
            f"[{options}]",
        ],
        "start bluetooth.",
        mono=mono,
    )


def help_test(
    tokens: List[str],
    mono: bool,
) -> str:
    options = xtra("~start_bluetooth,verbose", mono=mono)

    return show_usage(
        [
            "@bps",
            "test",
            f"[{options}]",
        ],
        "d-bus ping test.",
        mono=mono,
    )


help_functions = {
    "beacon": help_beacon,
    "generate": help_generate,
    "install": help_install,
    "introspect": help_introspect,
    "loop": help_loop,
    "receiver": help_receiver,
    "review": help_review,
    "set_anchor": help_set_anchor,
    "simulate": help_simulate,
    "start_bluetooth": help_start_bluetooth,
    "test": help_test,
}
