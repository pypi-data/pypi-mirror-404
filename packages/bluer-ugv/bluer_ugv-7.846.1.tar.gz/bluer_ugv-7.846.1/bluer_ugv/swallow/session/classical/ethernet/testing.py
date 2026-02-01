import keyboard

from blueness import module

from bluer_ugv import NAME
from bluer_ugv import env
from bluer_ugv.swallow.session.classical.ethernet.client import EthernetClient
from bluer_ugv.swallow.session.classical.ethernet.command import EthernetCommand
from bluer_ugv.logger import logger


NAME = module.name(__file__, NAME)


def test(
    server_name: str,
    is_server: bool,
    port: int = env.BLUER_UGV_ETHERNET_PORT,
) -> bool:
    success = True

    logger.info(
        "{}.test: server_name={}, is_server={}, port={}".format(
            NAME,
            server_name,
            is_server,
            port,
        )
    )

    client = EthernetClient(
        host=server_name,
        port=port,
        is_server=is_server,
    )

    logger.info("press 5 to send a message.")
    try:
        while True:
            client.process()

            if keyboard.is_pressed("5"):
                client.send(EthernetCommand(action="hello"))
    except KeyboardInterrupt:
        logger.info("Ctrl+C, stopping.")
    except Exception as e:
        logger.error(e)
        success = False

    client.close()

    return success
