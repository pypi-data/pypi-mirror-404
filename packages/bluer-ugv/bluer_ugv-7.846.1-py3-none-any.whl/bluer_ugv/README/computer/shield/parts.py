from bluer_sbc.README.design import design_doc_parts

parts = {
    "470-mF": "",
    "green-terminal": "2 x",
    "LED": "green + red + yellow + 4 x blue",
    "pin-headers": "1 x (female, 2 x 40) -> 2 x 20 + 2 x (male, 1 x 40) -> 4 x 1 + 2 x 20 + 1 x (male, 2 x 40) -> 2 x 2 x 6",
    "Polyfuse": "optional",
    "pushbutton": "",
    "resistor": "7 x 330-470 Ω + 4 x 2.2 kΩ + 4 x 3.3 kΩ",
    "TVS-diode": "",
}

docs = [
    {
        "path": "../docs/swallow/digital/design/computer/shield/parts.md",
        "macros": design_doc_parts(
            dict_of_parts=parts,
            parts_reference="https://github.com/kamangir/bluer-sbc/tree/main/bluer_sbc/docs/parts",
        ),
    }
]
