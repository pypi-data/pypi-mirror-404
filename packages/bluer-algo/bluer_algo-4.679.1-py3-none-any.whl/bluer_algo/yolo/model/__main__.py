import argparse

from blueness import module
from blueness.argparse.generic import sys_exit

from bluer_algo import NAME
from bluer_algo.yolo.model.train import train
from bluer_algo.yolo.model.prediction_test import prediction_test
from bluer_algo.yolo.model.size import ModelSize
from bluer_algo.logger import logger

NAME = module.name(__file__, NAME)

parser = argparse.ArgumentParser(NAME)
parser.add_argument(
    "task",
    type=str,
    help="prediction_test|train",
)
parser.add_argument(
    "--prediction_object_name",
    type=str,
)
parser.add_argument(
    "--dataset_object_name",
    type=str,
)
parser.add_argument(
    "--model_object_name",
    type=str,
)
parser.add_argument(
    "--epochs",
    type=int,
    default=30,
    help="Number of training epochs",
)
parser.add_argument(
    "--image_size",
    type=int,
    default=640,
    help="Training image size",
)
parser.add_argument(
    "--batch",
    type=int,
    default=8,
    help="Batch size (adjust to your VRAM/CPU)",
)
parser.add_argument(
    "--device",
    type=str,
    default=None,
    help="Device string for PyTorch (e.g., '0', '0,1', 'cpu'). None = auto",
)
parser.add_argument(
    "--workers",
    type=int,
    default=4,
    help="Dataloader workers (Windows users: try 0 if you hit issues)",
)
parser.add_argument(
    "--model_size",
    type=str,
    default="nano",
    help=ModelSize.choices(),
)
parser.add_argument(
    "--from_scratch",
    type=int,
    default=0,
    help="0 | 1: Train from scratch (use a model YAML, no Internet needed).",
)
parser.add_argument(
    "--validate",
    type=int,
    default=1,
    help="0 | 1: run validation after training",
)
parser.add_argument(
    "--verbose",
    type=int,
    default=0,
    help="0 | 1",
)
parser.add_argument(
    "--record_index",
    type=int,
    default=0,
)
parser.add_argument(
    "--warmup",
    type=int,
    default=1,
    help="0 | 1",
)
args = parser.parse_args()

success = False
if args.task == "prediction_test":
    success, _ = prediction_test(
        dataset_object_name=args.dataset_object_name,
        model_object_name=args.model_object_name,
        record_index=args.record_index,
        prediction_object_name=args.prediction_object_name,
        warmup=args.warmup == 1,
        image_size=args.image_size,
    )
elif args.task == "train":
    success = train(
        dataset_object_name=args.dataset_object_name,
        model_object_name=args.model_object_name,
        epochs=args.epochs,
        image_size=args.image_size,
        batch=args.batch,
        device=args.device,
        workers=args.workers,
        model_size=ModelSize[args.model_size.upper()],
        from_scratch=args.from_scratch == 1,
        validate=args.validate == 1,
        verbose=args.verbose == 1,
    )
else:
    success = None

sys_exit(logger, NAME, args.task, success)
