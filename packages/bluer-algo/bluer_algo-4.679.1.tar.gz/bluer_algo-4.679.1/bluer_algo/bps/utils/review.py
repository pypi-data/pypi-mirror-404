import argparse

from blueness import module
from blueness.argparse.generic import sys_exit

from bluer_algo import NAME
from bluer_algo.bps.stream import Stream
from bluer_algo.logger import logger

NAME = module.name(__file__, NAME)

parser = argparse.ArgumentParser(NAME)
parser.add_argument(
    "--object_name",
    type=str,
)
args = parser.parse_args()

stream = Stream.load(args.object_name)

success = stream.export(args.object_name)

sys_exit(logger, NAME, "review", success)
