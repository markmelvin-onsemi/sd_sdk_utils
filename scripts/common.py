from pathlib import Path
import os
from enum import IntEnum

class Role(IntEnum):
    CENTRAL = 0
    PERIPHERAL = 1

class Ear(IntEnum):
    LEFT = 0
    RIGHT = 1


def connect_and_configure_device(communication_interface, product, product_name, upgrade_firmware=False):
    from sd_sdk_python import sd
    from sd_sdk_python.sd_sdk import Ezairo

    device_info = communication_interface.DetectDevice()
    assert device_info is not None and device_info.IsValid

    compatibility = product.Definition.GetDeviceCompatibility(communication_interface)

    if upgrade_firmware:
        if compatibility in (sd.kUnknownCompatibility, sd.kIncompatible):
            raise RuntimeError("Don't know how to upgrade the firmware on this device!")
        if compatibility == sd.kCompatibleUpToDate and device_info.FirmwareVersion == product.Definition.UpdateFirmwareVersion and \
                                                       device_info.RadioApplicationVersion == product.Definition.UpdateRadioApplicationVersion:
            print(f"Skipping firmware update as it is already up to date (FW: {device_info.FirmwareVersion}, Radio: {device_info.RadioApplicationVersion})")
        else:
            print(f"Upgrading firmware from {device_info.FirmwareVersion}/{device_info.RadioApplicationVersion} to {product.Definition.UpdateFirmwareVersion}/{product.Definition.UpdateRadioApplicationVersion}")
            print("This will take a few minutes...")
            update_log = product.Definition.UpdateDevice(communication_interface)
            device_info_after = communication_interface.DetectDevice()
            assert device_info_after is not None and device_info_after.IsValid
            if device_info_after.FirmwareVersion != product.Definition.UpdateFirmwareVersion:
                raise RuntimeError(f"Firmware update failed! Expected version {product.Definition.UpdateFirmwareVersion} but got {device_info_after.FirmwareVersion}!")
            if device_info_after.RadioApplicationVersion != product.Definition.UpdateRadioApplicationVersion:
                raise RuntimeError(f"Radio update failed! Expected version {product.Definition.UpdateRadioApplicationVersion} but got {device_info_after.RadioApplicationVersion}!")
            print("Firmware update complete!")
            device_info = device_info_after
    else:
        if compatibility != sd.kCompatibleUpToDate:
            print(f"Warning: firmware on the device is not the same.")
            print(f"Device:  FW: {device_info.FirmwareVersion}, Radio: {device_info.RadioApplicationVersion}")
            print(f"Library: FW: {product.Definition.UpdateFirmwareVersion}, Radio: {product.Definition.UpdateRadioApplicationVersion}")

    assert device_info.FirmwareId == product_name

    if not product.InitializeDevice(communication_interface):
        print("Configuring device...")
        product.ConfigureDevice()

    assert device_info.LibraryId == product.Definition.LibraryId
    assert device_info.ProductId == product.Definition.ProductId
    return Ezairo(sd, communication_interface, device_info, product)


def create_communication_interface(programmer, side, interface_options=None, verify_nvm_writes=False):
    from sd_sdk_python import get_product_manager

    product_manager = get_product_manager()
    interface = product_manager.CreateCommunicationInterface(programmer, side, '' if interface_options is None else interface_options)
    interface.VerifyNvmWrites = verify_nvm_writes
    return interface
