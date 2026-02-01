import argparse

from blueness import module
from blueness.argparse.generic import sys_exit

from bluer_ugv import NAME
from bluer_ugv.README.ugvs.get import get
from bluer_ugv.logger import logger

NAME = module.name(__file__, NAME)

parser = argparse.ArgumentParser(NAME)
parser.add_argument(
    "task",
    type=str,
    help="get",
)
parser.add_argument(
    "--ugv_name",
    type=str,
)
parser.add_argument(
    "--what",
    type=str,
)
args = parser.parse_args()

success = False
if args.task == "get":
    success = True
    print(
        get(
            ugv_name=args.ugv_name,
            what=args.what,
        )
    )
else:
    success = None

sys_exit(logger, NAME, args.task, success)
