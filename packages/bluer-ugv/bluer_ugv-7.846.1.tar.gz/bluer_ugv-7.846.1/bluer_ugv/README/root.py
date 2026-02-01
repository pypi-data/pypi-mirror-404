from bluer_objects.README.alias import list_of_aliases

from bluer_ugv import NAME
from bluer_ugv.README.items import items
from bluer_ugv.README.shortcuts import items as shortcuts_items


docs = [
    {
        "path": "../..",
        "items": items,
        "macros": {
            "shortcuts:::": shortcuts_items,
            "aliases:::": list_of_aliases(NAME),
        },
    },
    {
        "path": "../docs",
    },
]
