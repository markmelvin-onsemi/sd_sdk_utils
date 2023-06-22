from pathlib import Path
import os
import json

from cmd_line_args import get_programmer, get_side, get_command_line_parser, validate_file
from common import create_communication_interface, connect_and_configure_device


def main():
    parser = get_command_line_parser()
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


    configured_device = connect_and_configure_device(interface, product, args.product, upgrade_firmware=False)
    print(configured_device.device_info)
    # Configure for a pure tone input signal
    configured_device.set_input_signal_type(configured_device.sd.kPureTone)

    # Switch to memory 1
    configured_device.set_current_memory(configured_device.sd.kNvmMemory1)

    print(f"Current memory: {configured_device.product.CurrentMemory}")

    # Sync all parameters from the device
    configured_device.restore_all_parameters()

    print(f"Current memory: {configured_device.product.CurrentMemory}")

    configured_device.product.CloseDevice()


if __name__ == '__main__':
    main()
