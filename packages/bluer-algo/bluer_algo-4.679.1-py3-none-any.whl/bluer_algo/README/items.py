from bluer_objects import README
from bluer_objects.README.consts import assets2


items = README.Items(
    [
        {
            "name": "bps",
            "description": "ultra-low-bandwidth command and telemetry channel using BLE local sensing and LoRa extended range",
            "marquee": f"{assets2}/anchor/03.png?raw=true",
            "url": "./bluer_algo/docs/bps",
        },
        {
            "name": "yolo",
            "description": "a yolo interface.",
            "marquee": "https://github.com/kamangir/assets/raw/main/swallow-debug-2025-09-16-19-53-19-4yzsp8/swallow-debug-2025-09-16-19-53-19-4yzsp8-2.gif?raw=true",
            "url": "./bluer_algo/docs/yolo",
        },
        {
            "name": "tracker",
            "marquee": "https://github.com/kamangir/assets/raw/main/tracker-camshift-2025-07-16-11-07-52-4u3nu4/tracker.gif?raw=true",
            "description": "a visual tracker.",
            "url": "./bluer_algo/docs/tracker",
        },
        {
            "name": "image classifier",
            "marquee": "https://github.com/kamangir/assets/raw/main/swallow-model-2025-07-11-15-04-03-2glcch/evaluation.png?raw=true",
            "description": "an image classifier.",
            "url": "./bluer_algo/docs/image_classifier",
        },
    ]
)
