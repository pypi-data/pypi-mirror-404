import argparse

from blueness import module
from blueness.argparse.generic import sys_exit

from bluer_algo import NAME
from bluer_algo.image_classifier.model.prediction_test import prediction_test
from bluer_algo.image_classifier.model.train import train
from bluer_algo.logger import logger

NAME = module.name(__file__, NAME)

parser = argparse.ArgumentParser(NAME)
parser.add_argument(
    "task",
    type=str,
    help="prediction_test|train",
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
    "--prediction_object_name",
    type=str,
)
parser.add_argument(
    "--batch_size",
    type=int,
    default=16,
)
parser.add_argument(
    "--num_epochs",
    type=int,
    default=10,
)
args = parser.parse_args()

success = False
if args.task == "prediction_test":
    success, _ = prediction_test(
        dataset_object_name=args.dataset_object_name,
        model_object_name=args.model_object_name,
        prediction_object_name=args.prediction_object_name,
    )
elif args.task == "train":
    success = train(
        dataset_object_name=args.dataset_object_name,
        model_object_name=args.model_object_name,
        batch_size=args.batch_size,
        num_epochs=args.num_epochs,
    )
else:
    success = None

sys_exit(logger, NAME, args.task, success)
