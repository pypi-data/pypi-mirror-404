from bluer_ai.help.generic import help_functions as generic_help_functions

from bluer_algo import ALIAS
from bluer_algo.help.bps.functions import help_functions as help_bps
from bluer_algo.help.image_classifier import help_functions as help_image_classifier
from bluer_algo.help.socket import help_functions as help_socket
from bluer_algo.help.tracker import help_functions as help_tracker
from bluer_algo.help.yolo import help_functions as help_yolo


help_functions = generic_help_functions(plugin_name=ALIAS)

help_functions.update(
    {
        "bps": help_bps,
        "image_classifier": help_image_classifier,
        "socket": help_socket,
        "tracker": help_tracker,
        "yolo": help_yolo,
    }
)
