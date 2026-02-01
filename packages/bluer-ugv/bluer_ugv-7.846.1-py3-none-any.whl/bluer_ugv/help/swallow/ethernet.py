from typing import List

from bluer_options.terminal import show_usage, xtra

from bluer_ugv import env


def help_test(
    tokens: List[str],
    mono: bool,
) -> str:
    options = xtra("dryrun", mono=mono)

    args = [
        "[--is_server 0 | 1]",
        "[--server_name 0.0.0.0 | <server_name>.local]",
    ]

    return show_usage(
        [
            "@swallow",
            "ethernet",
            "test",
            f"[{options}]",
        ]
        + args,
        "test ethernet.",
        mono=mono,
    )


help_functions = {
    "test": help_test,
}
