from bluer_objects.README.items import ImageItems
from bluer_objects.README.consts import assets_url


assets2 = assets_url(
    suffix="bps",
    volume=2,
)


docs = [
    {
        "path": "../docs/bps",
        "cols": 2,
        "items": ImageItems(
            {
                f"{assets2}/01.png": "",
                f"{assets2}/03.png": "",
                f"{assets2}/02.png": "",
                f"{assets2}/05.png": "",
            }
        ),
    }
] + [
    {
        "path": f"../docs/bps/{doc}",
    }
    for doc in [
        "literature.md",
        #
        "validations",
        "validations/test-introspect.md",
        "validations/beacon-receiver.md",
        "validations/loop-2.md",
        "validations/review.md",
        "validations/loop-3.md",
        "validations/data-collection.md",
        "validations/live-1.md",
        "validations/live-2.md",
        "validations/live-2b.md",
        "validations/live-3.md",
        #
        "simulations",
        "simulations/timing-v1.md",
        "simulations/timing.md",
        #
        "mathematics",
        "mathematics/timing",
        "mathematics/timing/v1.md",
        "mathematics/localization.md",
    ]
]
