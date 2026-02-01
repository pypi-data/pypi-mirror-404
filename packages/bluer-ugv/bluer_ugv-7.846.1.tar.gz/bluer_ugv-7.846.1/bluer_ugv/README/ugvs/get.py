from bluer_ugv.README.ugvs.db import dict_of_ugvs


def get(
    ugv_name: str,
    what: str,
) -> str:
    list_of_what = what.split(".")
    info = dict_of_ugvs.get(ugv_name, {})
    for what_ in list_of_what:
        info = info.get(what_, {})

    if isinstance(info, dict) and not info:
        info = ""

    if not info:
        info = "not-found"

    return str(info)
