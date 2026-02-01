import argparse

from blueness import module
from blueness.argparse.generic import sys_exit

from bluer_algo import NAME
from bluer_algo.yolo.dataset.ingest.coco_128.ingest import ingest
from bluer_algo.logger import logger

NAME = module.name(__file__, NAME)

parser = argparse.ArgumentParser(NAME)
parser.add_argument(
    "task",
    type=str,
    help="ingest",
)
parser.add_argument(
    "--verbose",
    type=bool,
    default=0,
    help="0|1",
)
parser.add_argument(
    "--object_name",
    type=str,
)
parser.add_argument(
    "--classes",
    type=str,
    default="all",
    help="<this>+<that>",
)
args = parser.parse_args()

success = False
if args.task == "ingest":
    success = ingest(
        object_name=args.object_name,
        verbose=args.verbose == 1,
        filter_classes=args.classes != "all",
        classes=args.classes.split("+"),
    )
else:
    success = None

sys_exit(logger, NAME, args.task, success)
