from pathlib import Path
import os
import json

from cmd_line_args import get_programmer, get_side, get_command_line_parser, validate_file
from common import create_communication_interface, connect_and_configure_device


def main():
    parser = get_command_line_parser()
    parser.add_argument(
        "--upgrade-firmware",
        action="store_true",
        default=False, help="Upgrade the firmware on the device if it is not the same"
    )
    parser.add_argument(
        "--param-file",
        action="store",
        default=None,
        help="Path to the base .param file used to program the devices",
        required=True,
        type=validate_file,
    )
    parser.add_argument(
        "--library-file",
        action="store",
        default=None,
        help="Path to the .library file to use (if different than the product default)",
        type=validate_file,
    )
    parser.add_argument(
        "--product-index",
        action="store",
        default=0,
        help="Index of the product in the library file",
        type=int,
    )

    args = parser.parse_args()

    interface = create_communication_interface(get_programmer(args.programmer),
                                               get_side(args.side),
                                               interface_options=args.interface_options,
                                               verify_nvm_writes=args.verify_nvm_writes)

    from sd_sdk_python import get_product_manager
    product_manager = get_product_manager()
    sdk_root = Path(os.environ['SD_SDK_ROOT'])
    library_path = str(sdk_root / f"products/{args.product}.library") if args.library_file is None else str(args.library_file)
    library = product_manager.LoadLibraryFromFile(library_path)
    product = library.Products[args.product_index].CreateProduct()

    # Confirm that the .library referenced in the .param file is the same as the product library specified
    with args.param_file.open() as fp:
        param_json = json.load(fp)
        assert param_json["libraryid"] == product.Definition.LibraryId, "The library ID in the .param file does not match the product library!"

    configured_device = connect_and_configure_device(interface, product, args.product, upgrade_firmware=args.upgrade_firmware)

    print(f"Configuring device from .param file: {str(args.param_file)}...", end='', flush=True)
    configured_device.interface.MuteDuringCommunication = False
    configured_device.mute()

    # Configure for a pure tone input signal
    configured_device.set_input_signal_type(configured_device.sd.kPureTone)
    # Switch to memory 1
    configured_device.set_current_memory(configured_device.sd.kNvmMemory1)
    # Sync all parameters from the device
    configured_device.restore_all_parameters()

    # Load the parameters from the param file and configure the device
    configured_device.load_param_file(str(args.param_file),
                                      configure_device=True,
                                      write_manufacturer_data=True,
                                      write_voice_alerts=True)
    configured_device.burn_all_parameters()

    configured_device.unmute()

    # Reset the device (this must be the last thing we do as the device will disconnect)
    configured_device.reset()
    configured_device.product.CloseDevice()
    print(" done!")


if __name__ == '__main__':
    main()
