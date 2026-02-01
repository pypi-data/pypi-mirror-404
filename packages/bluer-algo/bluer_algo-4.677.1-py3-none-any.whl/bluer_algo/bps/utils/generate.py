import argparse

from blueness import module
from blueness.argparse.generic import sys_exit

from bluer_algo import NAME
from bluer_algo.bps.stream import Stream
from bluer_algo.bps.position import Position
from bluer_algo.logger import logger

NAME = module.name(__file__, NAME)


parser = argparse.ArgumentParser(NAME)
parser.add_argument(
    "--as_str",
    type=str,
    default="",
)
parser.add_argument(
    "--object_name",
    type=str,
)
parser.add_argument(
    "--sigma",
    type=float,
    default=4.0,
)
parser.add_argument(
    "--simulate",
    type=int,
    default=0,
    help="0 | 1",
)
parser.add_argument(
    "--x",
    type=float,
    default=1.0,
)
parser.add_argument(
    "--y",
    type=float,
    default=2.0,
)
parser.add_argument(
    "--z",
    type=float,
    default=3.0,
)
parser.add_argument(
    "--only_validate",
    type=int,
    default=0,
    help="0|1",
)
args = parser.parse_args()

if args.only_validate:
    stream = Stream()
else:
    stream = Stream.load(args.object_name)

x = args.x
y = args.y
z = args.z
sigma = args.sigma

success = True
if args.as_str:
    as_str_parts = args.as_str.split(",")
    if len(as_str_parts) == 4:
        try:
            x, y, z, sigma = [float(part) for part in as_str_parts]
        except Exception as e:
            logger.error(e)
            success = False
    else:
        logger.error("too few inputs, expected x,y,z,sigma (4).")
        success = False

position = Position(
    x=x,
    y=y,
    z=z,
    sigma=sigma,
)

if success:
    stream.generate(
        simulate=args.simulate,
        as_dict=position.as_dict(),
    )

    if not args.only_validate:
        success = stream.save(args.object_name)

if success and not args.only_validate:
    success = position.save(args.object_name)

sys_exit(logger, NAME, "generate", success)
