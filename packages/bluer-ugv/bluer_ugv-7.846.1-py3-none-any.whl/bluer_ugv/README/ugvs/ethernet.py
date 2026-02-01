from typing import Tuple

from bluer_ugv.README.ugvs.db import dict_of_ugvs
from bluer_ugv.logger import logger


def find_server(
    hostname: str,
) -> Tuple[
    bool,  # success
    bool,  # is_server
    str,  # "0.0.0.0" if is_server else f"{server_name}.local"
]:
    for ugv_name, info in dict_of_ugvs.items():
        found: bool = False
        dict_of_computers = info.get("computers", {})
        assert isinstance(dict_of_computers, dict)

        for location, hostname_ in dict_of_computers.items():
            if hostname != hostname_:
                continue

            logger.info(f"{hostname} == {ugv_name}.{location}")
            found = True

            if location == "front":
                return True, True, "0.0.0.0"

        if not found:
            continue

        list_of_server_names = [
            hostname_
            for location, hostname_ in dict_of_computers.items()
            if location == "front"
        ]
        if not list_of_server_names:
            logger.error(f"no server (.front) onboard {ugv_name}.")
            return False, False, ""

        if len(list_of_server_names) > 1:
            logger.warning(
                "{} servers (.front) onboard {}".format(
                    len(list_of_server_names),
                    ugv_name,
                )
            )

        server_name = list_of_server_names[0]
        logger.info(f"{hostname}: server_name={server_name}")

        return True, False, f"{server_name}.local"

    logger.error(f"cannot find hostname: {hostname}.")
    return False, False, ""
