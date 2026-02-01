import argparse

from blueness import module
from blueness.argparse.generic import sys_exit

from bluer_ugv import env
from bluer_ugv import NAME
from bluer_ugv.swallow.session.classical.ethernet.testing import test
from bluer_ugv.logger import logger

NAME = module.name(__file__, NAME)

parser = argparse.ArgumentParser(NAME)
parser.add_argument(
    "task",
    type=str,
    help="test",
)
parser.add_argument(
    "--is_server",
    type=int,
    default=1,
    help="0 | 1",
)
parser.add_argument(
    "--server_name",
    type=str,
    default="0.0.0.0",
    help="0.0.0.0 | <server_name>.local",
)
args = parser.parse_args()

success = False
if args.task == "test":
    success = test(
        server_name=args.server_name,
        is_server=args.is_server == 1,
    )
else:
    success = None

sys_exit(logger, NAME, args.task, success)
