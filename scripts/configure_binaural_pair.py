from pathlib import Path
import os
import json
import time

from cmd_line_args import get_programmer, get_side, get_command_line_parser, validate_file
from common import Role, Ear, create_communication_interface, connect_and_configure_device
import argparse


def program_binaural_half(configured_device, param_file : Path, peer_address : int,
                          role : Role, enable_asha=True, enable_mfi=True):
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
    if role == Role.CENTRAL:
        configured_device.set_parameter_value(configured_device.sd.kSystemNvmMemory, 'X_RF_RoleSelect', Role.CENTRAL.value)
        configured_device.set_parameter_value(configured_device.sd.kSystemNvmMemory, 'X_FWK_Ear', Ear.LEFT.value)
    else:
        configured_device.set_parameter_value(configured_device.sd.kSystemNvmMemory, 'X_RF_RoleSelect', Role.PERIPHERAL.value)
        configured_device.set_parameter_value(configured_device.sd.kSystemNvmMemory, 'X_FWK_Ear', Ear.RIGHT.value)

    configured_device.set_parameter_value(configured_device.sd.kSystemNvmMemory, 'X_RF_BinauralPeerAddress2', peer_address & 0xFFFFFF)
    configured_device.set_parameter_value(configured_device.sd.kSystemNvmMemory, 'X_RF_BinauralPeerAddress1', peer_address >> 24)

    configured_device.set_parameter_value(configured_device.sd.kSystemNvmMemory, 'X_RF_ASHAEnable', 1 if enable_asha else 0)
    configured_device.set_parameter_value(configured_device.sd.kSystemNvmMemory, 'X_RF_MFiEnable', 1 if enable_mfi else 0)

    configured_device.burn_all_parameters()

    configured_device.unmute()

    # Reset the device (this must be the last thing we do as the device will disconnect)
    configured_device.reset()

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
    parser.add_argument(
        "--central-address",
        action="store",
        default=None,
        help="Manually specify the central's MAC address (default is to auto-detect)",
        type=lambda x: int(x, 0),
    )
    parser.add_argument(
        "--peripheral-address",
        action="store",
        default=None,
        help="Manually specify the peripheral's MAC address (default is to auto-detect)",
        type=lambda x: int(x, 0),
    )
    parser.add_argument(
        "--asha",
        action=argparse.BooleanOptionalAction,
        default=False, help="Enable ASHA on the device",
    )
    parser.add_argument(
        "--mfi",
        action=argparse.BooleanOptionalAction,
        default=False, help="Enable MFi on the device",
    )
    parser.add_argument(
        "--delete-bonds",
        action="store_true",
        default=False, help="When specified, delete the bond table on both devices"
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

    peripheral_address = args.peripheral_address
    if peripheral_address is None:
        # Auto-deteect the peripheral address
        print("Unplug everything except for the desired RIGHT / PERIPHERAL device and press Enter when ready: ", end='')
        input()
        peripheral = connect_and_configure_device(interface, product, args.product, upgrade_firmware=args.upgrade_firmware)
        peripheral_address = int(peripheral.product.DeviceMACAddress, 16)
        peripheral.product.CloseDevice()

    print(f"Peripheral MAC: {hex(peripheral_address)}")

    print("Unplug everything except for the desired LEFT / CENTRAL device and press Enter when ready: ", end='')
    input()

    central = connect_and_configure_device(interface, product, args.product, upgrade_firmware=args.upgrade_firmware)
    central_address = int(central.product.DeviceMACAddress, 16)
    if args.central_address is not None and central_address != args.central_address:
        print(f"Warning! The detected central address ({hex(central_address)}) is different than the one specified ({args.central_address})!")
        print(f"(Used the one specified on the command line: {args.central_address})")
    print(f"Central MAC: {hex(central_address)}")

    # Program the Central
    print("Programming the LEFT / CENTRAL device ...")
    program_binaural_half(central, args.param_file, peripheral_address,
                          Role.CENTRAL, enable_asha=args.asha, enable_mfi=args.mfi)
    if args.delete_bonds:
        print("Waiting for a reboot...")
        # Wait and then re-connect and delete the bond table
        time.sleep(5.0)
        device_info = central.interface.DetectDevice()
        assert device_info is not None and device_info.IsValid
        assert product.InitializeDevice(central.interface)
        central.interface.ClearBondTableOnDevice()
        print("Deleted the bond table on the central")

    central.product.CloseDevice()

    print("Power off the central and power on the RIGHT / PERIPHERAL device and press Enter when ready: ", end='')
    input()

    print("Programming the RIGHT / PERIPHERAL device ...")
    peripheral = connect_and_configure_device(interface, product, args.product, upgrade_firmware=args.upgrade_firmware)

    if args.peripheral_address is not None:
        peripheral_address = int(peripheral.product.DeviceMACAddress, 16)
        if args.peripheral_address != peripheral_address:
            print(f"Warning! The detected peripheral address ({hex(peripheral_address)}) is different than the one specified ({args.peripheral_address})!")
            print(f"(Used the one specified on the command line: {args.peripheral_address})")

    program_binaural_half(peripheral, args.param_file, central_address,
                          Role.PERIPHERAL, enable_asha=args.asha, enable_mfi=args.mfi)
    if args.delete_bonds:
        print("Waiting for a reboot...")
        # Wait and then re-connect and delete the bond table
        time.sleep(5.0)
        device_info = peripheral.interface.DetectDevice()
        assert device_info is not None and device_info.IsValid
        assert product.InitializeDevice(peripheral.interface)
        peripheral.interface.ClearBondTableOnDevice()
        print("Deleted the bond table peripheral")

    peripheral.product.CloseDevice()


if __name__ == '__main__':
    main()
