from bluer_ugv.README.consts import assets_url
from bluer_ugv.README.swallow.consts import swallow_assets2
from bluer_ugv.README.arzhang.consts import (
    arzhang_assets,
    arzhang_assets2,
    arzhang2_assets2,
)
from bluer_ugv.README.rangin.consts import rangin_assets2, rangin_mechanical_design

dict_of_ugvs = {
    "swallow": {
        "order": 1,
        "cols": 1,
        "items": [
            f"{swallow_assets2}/20250701_2206342_1.gif",
            f"{swallow_assets2}/20250913_203635~2_1.gif",
            f"{swallow_assets2}/20251216_205015.jpg",
        ],
        "tagline": "the first one.",
        "class": "swallow",
        "computers": {
            "front": "swallow2",  #  `swallow` was used for Ubuntu experiments
        },
    },
    "arzhang": {
        "order": 2,
        "items": [
            f"{arzhang_assets2}/20251209_111322.jpg",
        ],
        "tagline": "the first [arzhang](../arzhang).",
        "class": "arzhang",
        "computers": {
            "front": "sparrow",
        },
        "comments": [
            "disassembled 🛑",
        ],
    },
    "arzhang2": {
        "order": 3,
        "items": [
            f"{arzhang_assets2}/20251210_154513.jpg",
            f"{arzhang2_assets2}/20260108_175635.jpg",
            f"{arzhang2_assets2}/20260109_133216.jpg",
        ],
        "tagline": "an [arzhang](../arzhang) with updated body design.",
        "class": "arzhang",
        "computers": {
            "front": "sparrow2",
            "back": "sparrow3-back",
        },
    },
    "arzhang3": {
        "order": 4,
        "items": sorted(
            [
                f"{arzhang_assets}/20251107_175506.jpg",
                f"{arzhang_assets2}/20251128_175614.jpg",
                f"{arzhang_assets2}/20251202_100317.jpg",
                f"{arzhang_assets2}/20251202_101031.jpg",
                f"{arzhang_assets2}/20251128_113314.jpg",
                f"{arzhang_assets2}/20251128_151952.jpg",
                f"{arzhang_assets2}/20251128_155616.jpg",
                f"{arzhang_assets2}/20251130_140103.jpg",
                f"{arzhang_assets2}/20251203_112602.jpg",
                f"{arzhang_assets2}/20251210_154654.jpg",
            ]
        ),
        "tagline": "the first [arzhang](../arzhang) with two computers.",
        "class": "arzhang",
        "computers": {
            "front": "arzhang3-front",
            "back": "sparrow3-back",
        },
        "comments": [
            "-> [rangin](./rangin.md) 🛑",
        ],
    },
    "rangin": {
        "order": 5,
        "items": [
            f"{rangin_mechanical_design}/robot.png",
            f"{rangin_assets2}/20251221_125120.jpg",
            f"{rangin_assets2}/20251222_104404.jpg",
            f"{rangin_assets2}/20251222_110634.jpg",
            f"{rangin_assets2}/20251222_160737.jpg",
            f"{rangin_assets2}/20251222_165829.jpg",
            f"{rangin_assets2}/20251222_173509.jpg",
            f"{rangin_assets2}/IMG-20251223-WA0001.jpg",
            f"{rangin_assets2}/IMG-20251223-WA0009.jpg",
            f"{rangin_assets2}/IMG-20251223-WA0010.jpg",
            f"{rangin_assets2}/20251224_180302.jpg",
            f"{rangin_assets2}/20251224_180308.jpg",
            f"{rangin_assets2}/20251224_180319.jpg",
            f"{rangin_assets2}/20251224_182306~3_1.gif",
            f"{rangin_assets2}/2025-12-25-lab.png",
            f"{rangin_assets2}/20251226_184718.jpg",
            f"{rangin_assets2}/20251226_184008.jpg",
            f"{rangin_assets2}/20251228_125134.jpg",
            f"{rangin_assets2}/20251231_111615.jpg",
            f"{rangin_assets2}/20251231_111656.jpg",
            f"{rangin_assets2}/20251231_111815.jpg",
            f"{rangin_assets2}/20251231_111923.jpg",
            f"{rangin_assets2}/20251231_112447.jpg",
            f"{rangin_assets2}/2026-01-26-d1.jpg",
            f"{rangin_assets2}/2026-01-26-d2.jpg",
            f"{rangin_assets2}/2026-01-26-d3.jpg",
        ],
        "tagline": "an ad robot.",
        "class": "rangin",
        "computers": {
            "front": "arzhang3-front",
            "top": "rangin-top2",
        },
        "comments": [
            "built on [arzhang3](./arzhang3.md).",
        ],
    },
    "arzhang4": {
        "order": 6,
        "items": [
            assets_url(
                suffix="bluer-sbc/parts/GM6558/01.jpg",
                volume=2,
            ),
        ],
        "tagline": "the first [arzhang](../arzhang) with [external motors](https://github.com/kamangir/bluer-sbc/blob/main/bluer_sbc/docs/parts/DC-gearboxed-motor-12V-120RPM.md).",
        "class": [
            "arzhang",
            "with external motors.",
        ],
        "comments": [
            "build is ongoing. 🔥",
        ],
    },
}
