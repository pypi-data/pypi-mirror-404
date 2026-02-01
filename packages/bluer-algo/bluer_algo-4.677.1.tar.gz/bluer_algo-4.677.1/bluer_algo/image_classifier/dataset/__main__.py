import argparse

from blueness import module
from blueness.argparse.generic import sys_exit

from bluer_algo import NAME
from bluer_algo.image_classifier.dataset.review import review
from bluer_algo.image_classifier.dataset.sequence import sequence
from bluer_algo.logger import logger

NAME = module.name(__file__, NAME)

parser = argparse.ArgumentParser(NAME)
parser.add_argument(
    "task",
    type=str,
    help="review | sequence",
)
parser.add_argument(
    "--object_name",
    type=str,
)
parser.add_argument(
    "--source_object_name",
    type=str,
)
parser.add_argument(
    "--destination_object_name",
    type=str,
)
parser.add_argument(
    "--length",
    type=int,
    default=2,
)
args = parser.parse_args()

success = False
if args.task == "review":
    success = review(object_name=args.object_name)
elif args.task == "sequence":
    success = sequence(
        source_object_name=args.source_object_name,
        destination_object_name=args.destination_object_name,
        length=args.length,
    )
else:
    success = None

sys_exit(logger, NAME, args.task, success)
