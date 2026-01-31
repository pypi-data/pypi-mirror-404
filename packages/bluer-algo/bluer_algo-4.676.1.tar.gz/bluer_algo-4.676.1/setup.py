from blueness.pypi import setup

from bluer_algo import NAME, VERSION, DESCRIPTION, REPO_NAME

setup(
    filename=__file__,
    repo_name=REPO_NAME,
    name=NAME,
    version=VERSION,
    description=DESCRIPTION,
    packages=[
        NAME,
        f"{NAME}.bps",
        f"{NAME}.bps.simulation",
        f"{NAME}.bps.simulation.timing",
        f"{NAME}.bps.utils",
        f"{NAME}.help",
        f"{NAME}.help.bps",
        f"{NAME}.help.image_classifier",
        f"{NAME}.help.yolo",
        f"{NAME}.image_classifier",
        f"{NAME}.image_classifier.dataset",
        f"{NAME}.image_classifier.dataset.ingest",
        f"{NAME}.image_classifier.dataset.ingest.fruits_360",
        f"{NAME}.image_classifier.model",
        f"{NAME}.README",
        f"{NAME}.tracker",
        f"{NAME}.tracker.classes",
        f"{NAME}.yolo",
        f"{NAME}.yolo.dataset",
        f"{NAME}.yolo.dataset.ingest",
        f"{NAME}.yolo.dataset.ingest.coco_128",
        f"{NAME}.yolo.model",
    ],
    include_package_data=True,
    package_data={
        NAME: [
            "config.env",
            ".abcli/**/*.sh",
            "assets/**/*",
        ],
    },
)
