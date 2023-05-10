import argparse
from pathlib import Path
import os


def set_sdk_root(value):
    path_value = Path(value)
    if not path_value.exists() or not path_value.is_dir():
        raise ValueError(f"{value} is not a valid path")

    os.environ['SD_SDK_ROOT'] = str(path_value)

    return path_value

def validate_file(value):
    path_value = Path(value)
    if not path_value.exists() or not path_value.is_file():
        raise ValueError(f"{value} is not a valid file path")

    return path_value

def get_side(value):
    side = value.upper()
    if side == 'LEFT':
        return 0 # sd.kLeft
    if side == 'RIGHT':
        return 1 # sd.kRight

    raise ValueError(f"Unknown side: {value}")

def get_programmer(value):
    programmer = value.upper()
    if programmer == 'CAA':
        return 'Communication Accelerator Adaptor'
    elif programmer == 'DSP3':
        return 'DSP3'
    elif programmer == 'PROMIRA':
        return 'Promira'

    raise ValueError(f"Unknown programmer: {programmer}")


def get_command_line_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--sdk-root",
        action="store",
        default=None,
        help="Path to the Sound Designer SDK root folder (or set 'SD_SDK_ROOT' in your environment)",
        type=set_sdk_root,
    )
    parser.add_argument(
        "--programmer",
        action="store",
        default="CAA",
        help="Specify which programmer to use (one of ['CAA', 'DSP3', 'Promira'])",
        choices=("CAA", "DSP3", "Promira"),
        type=get_programmer,
    )
    parser.add_argument(
        "--side",
        action="store",
        default="left",
        help="Specify which side to use (one of ['left', 'right'])",
        choices=("left", "right"),
        type=get_side,
    )
    parser.add_argument(
        "--interface-options",
        action="store",
        default=None,
        help="Options to pass to the communication interface",
    )
    parser.add_argument(
        "--product",
        action="store",
        default="E7160SL",
        help="Which product to use (one of ['E7111V2', 'E7160SL'])",
        choices=('E7111V2', 'E7160SL'),
    )
    parser.add_argument(
        "--verify-nvm-writes", action="store_true", default=False, help="Verify all NVM writes"
    )

    return parser