import os

from bluer_options.help.functions import get_help
from bluer_objects import file, README

from bluer_ugv import NAME, VERSION, ICON, REPO_NAME
from bluer_ugv.help.functions import help_functions
from bluer_ugv.README.ugvs.comparison.build import build as build_comparison
from bluer_ugv.README.docs import docs


def build() -> bool:
    return (
        all(
            README.build(
                items=readme.get("items", []),
                path=os.path.join(file.path(__file__), readme["path"]),
                cols=readme.get("cols", 3),
                ICON=ICON,
                NAME=NAME,
                VERSION=VERSION,
                REPO_NAME=REPO_NAME,
                help_function=lambda tokens: get_help(
                    tokens,
                    help_functions,
                    mono=True,
                ),
                macros=readme.get("macros", {}),
            )
            for readme in docs
        )
        and build_comparison()
    )
