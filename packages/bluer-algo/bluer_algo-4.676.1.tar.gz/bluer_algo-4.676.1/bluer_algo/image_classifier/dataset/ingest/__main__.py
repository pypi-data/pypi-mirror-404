import argparse

from blueness import module
from blueness.argparse.generic import sys_exit

from bluer_algo import NAME
from bluer_algo.image_classifier.dataset.ingest import sources as ingest_sources
from bluer_algo.logger import logger

NAME = module.name(__file__, NAME)

parser = argparse.ArgumentParser(NAME)
parser.add_argument(
    "task",
    type=str,
    help="get_source",
)
parser.add_argument(
    "--index",
    type=int,
    default=0,
    help=" | ".join([str(value) for value in range(len(ingest_sources))]),
)
args = parser.parse_args()

success = False
if args.task == "get_source":
    try:
        success = True
        print(ingest_sources[args.index])
    except Exception as e:
        success = False
        print(e)
else:
    success = None

sys_exit(logger, NAME, args.task, success)
