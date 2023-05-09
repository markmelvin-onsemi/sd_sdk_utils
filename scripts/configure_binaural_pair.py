import argparse
from pathlib import Path
import os
from enum import Enum


class Role(Enum):
    CENTRAL = 0
    PERIPHERAL = 1


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


def parse_command_line_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--sdk-root",
        action="store",
        default=None,
        help="Path to the Sound Designer SDK root folder (or set 'SD_SDK_ROOT' in your environment)",
        type=set_sdk_root,
    )
    parser.add_argument(
        "--param-file",
        action="store",
        default=None,
        help="Path to the base .param file used to program the devices",
        type=validate_file,
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

    return parser.parse_args()


def connect_device(communication_interface, product, product_name):
    from sd_sdk_python import sd
    from sd_sdk_python.sd_sdk import Ezairo, DeviceInfo

    device_info = communication_interface.DetectDevice()
    assert device_info is not None and device_info.IsValid
    assert device_info.FirmwareId == product_name

    if not product.InitializeDevice(communication_interface):
        product.ConfigureDevice()

    assert device_info.LibraryId == product.Definition.LibraryId
    assert device_info.ProductId == product.Definition.ProductId
    return Ezairo(sd, communication_interface, DeviceInfo(device_info), product)


def program_binaural_half(configured_device, param_file : Path, peer_address : int,
                          central_peripheral : Role, enable_asha=True, enable_mfi=True):
    configured_device.interface.MuteDuringCommunication = False

    configured_device.mute()

    # Configure for a pure tone input signal
    configured_device.set_input_signal_type(configured_device.sd.kPureTone)

    # Switch to memory 1
    configured_device.set_current_memory(configured_device.sd.kNvmMemory1)

    # Sync all parameters from the device
    configured_device.restore_all_parameters()

    # Load the parameters from the param file, but don't configure
    # (just burn the voice alerts and manufacturing data)
    configured_device.load_param_file(str(param_file),
                                      configure_device=False,
                                      write_manufacturer_data=True,
                                      write_voice_alerts=True)

    # Override the peer address
    configured_device.set_parameter_value(configured_device.sd.kSystemNvmMemory, 'X_RF_BinauralPeerAddress2', peer_address & 0xFFFFFF)
    configured_device.set_parameter_value(configured_device.sd.kSystemNvmMemory, 'X_RF_BinauralPeerAddress1', peer_address >> 24)
    configured_device.burn_all_parameters()
    configured_device.interface.ClearBondTableOnDevice()

    configured_device.unmute()

    # Reset the device (this must be the last thing we do as the device will disconnect)
    configured_device.reset()

def main():
    args = parse_command_line_arguments()

    from sd_sdk_python import get_product_manager

    product_manager = get_product_manager()
    sdk_root = Path(os.environ['SD_SDK_ROOT'])
    library = product_manager.LoadLibraryFromFile(str(sdk_root / f"products/{args.product}.library"))
    product = library.Products[0].CreateProduct()

    interface = product_manager.CreateCommunicationInterface(args.programmer, args.side, '' if args.interface_options is None else args.interface_options)
    interface.VerifyNvmWrites = args.verify_nvm_writes

    ezairo = connect_device(interface, product, args.product)
    print(ezairo.device_info.to_dict())


if __name__ == '__main__':
    main()
