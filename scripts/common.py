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
        if compatibility == sd.kCompatibleUpToDate:
            print(f"Skipping firmware update as it is already up to date ({product.Definition.UpdateFirmwareVersion})")
        else:
            print(f"Upgrading firmware from {device_info.FirmwareVersion} to {product.Definition.UpdateFirmwareVersion}")
            print("This will take a few minutes...")
            update_log = product.Definition.UpdateDevice(communication_interface)
            device_info_after = communication_interface.DetectDevice()
            assert device_info_after is not None and device_info_after.IsValid
            if device_info_after.FirmwareVersion != product.Definition.UpdateFirmwareVersion:
                raise RuntimeError(f"Firmware update failed! Expected version {product.Definition.UpdateFirmwareVersion} but got {device_info_after.FirmwareVersion}!")
            print("Firmware update complete!")
            device_info = device_info_after
    else:
        if compatibility != sd.kCompatibleUpToDate:
            print(f"Warning: firmware on the device is not the same (Device: {device_info.FirmwareVersion}, Library: {product.Definition.UpdateFirmwareVersion})!")

    assert device_info.FirmwareId == product_name

    if not product.InitializeDevice(communication_interface):
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
