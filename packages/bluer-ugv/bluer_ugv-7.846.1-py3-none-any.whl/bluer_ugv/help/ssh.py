from typing import List

from bluer_options.terminal import show_usage


def help_ssh(
    tokens: List[str],
    mono: bool,
) -> str:
    return show_usage(
        [
            "@ugv",
            "ssh",
            "<ugv-name>",
            "[back | front | top | <node>]",
        ],
        "ssh to <ugv-name>.<node>",
        mono=mono,
    )
