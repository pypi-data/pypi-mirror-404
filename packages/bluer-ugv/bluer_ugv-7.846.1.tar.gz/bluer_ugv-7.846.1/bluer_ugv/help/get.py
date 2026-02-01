from typing import List

from bluer_options.terminal import show_usage


def help_get(
    tokens: List[str],
    mono: bool,
) -> str:
    return show_usage(
        [
            "@ugv",
            "get",
            "<ugv-name>",
            "computers.back | computers.front | computers.top | <what>",
        ],
        "get ugv info.",
        mono=mono,
    )
