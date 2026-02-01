from bluer_ugv.README.ravin.ravin3 import docs
from bluer_ugv.README.ravin.items import items
from bluer_ugv.README.ravin.ravin4 import docs

docs = (
    [
        {
            "items": items,
            "path": "../docs/ravin",
        },
    ]
    + docs.docs
    + docs.docs
)
