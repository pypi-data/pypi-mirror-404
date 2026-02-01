from bluer_objects.README.items import ImageItems, Items

from bluer_ugv.README.ugvs.db import dict_of_ugvs
from bluer_ugv.README.validations.db import dict_of_validations

docs = [
    {
        "path": f"../docs/UGVs/{ugv_name}.md",
        "cols": info.get("cols", 3),
        "items": ImageItems(
            {
                item: ""
                for item in info.get(
                    "items",
                    [],
                )
            }
        ),
        "macros": {
            "class:::": "[{class_name}](../{class_name}){info}".format(
                class_name=(
                    info["class"][0]
                    if isinstance(info["class"], list)
                    else info["class"]
                ),
                info=(
                    " ".join([""] + info["class"][1:])
                    if isinstance(info["class"], list)
                    else ""
                ),
            ),
            "computers:::": (
                (
                    [
                        "- computer(s):",
                    ]
                    + [
                        "    - {}: `{}`".format(
                            location,
                            computer_name,
                        )
                        for location, computer_name in info["computers"].items()
                    ]
                )
                if "computers" in info
                else []
            ),
            "comments:::": [
                f"- {comment}"
                for comment in info.get(
                    "comments",
                    [],
                )
            ],
            "tagline:::": info.get("tagline", ""),
            "validations:::": [
                (lambda thing: f"validations: {thing}" if thing else "")(
                    ", ".join(
                        sorted(
                            [
                                f"[`{validation_name}`](../validations/{validation_name}.md)"
                                for validation_name, info in dict_of_validations.items()
                                if any(
                                    ugv_name_.startswith(f"{ugv_name}:")
                                    for ugv_name_ in info["ugv_name"]
                                )
                            ]
                        )
                    )
                ),
            ],
        },
    }
    for ugv_name, info in dict_of_ugvs.items()
] + [
    {
        "path": "../docs/UGVs",
        "items": Items(
            [
                {
                    "name": ugv_name,
                    "marquee": (
                        (
                            lambda url: (
                                url if url.endswith("?raw=true") else f"{url}/?raw=true"
                            )
                        )(info["items"][-1])
                        if info["items"]
                        else ""
                    ),
                    "url": f"./{ugv_name}.md",
                }
                for ugv_name, info in dict_of_ugvs.items()
            ]
        ),
        "macros": {
            "list:::": [
                f"- [{ugv_name}](./{ugv_name}.md)"
                for ugv_name in sorted(
                    dict_of_ugvs.keys(),
                    key=lambda ugv_name: dict_of_ugvs[ugv_name]["order"],
                )
            ],
        },
    }
]
