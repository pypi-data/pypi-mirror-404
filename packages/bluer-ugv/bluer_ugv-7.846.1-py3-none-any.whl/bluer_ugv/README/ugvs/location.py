from typing import Tuple

from bluer_ugv.README.ugvs.db import dict_of_ugvs
from bluer_ugv.logger import logger


def get_location(
    hostname: str,
    log: bool = True,
) -> Tuple[bool, str]:
    for info in dict_of_ugvs.values():
        dict_of_computers = info.get("computers", {})
        assert isinstance(dict_of_computers, dict)

        for location, hostname_ in dict_of_computers.items():
            if hostname == hostname_:
                if log:
                    logger.info(f"{hostname}.location={location}")
                return True, location

    logger.error(f"{hostname}.location not found.")
    return False, ""
