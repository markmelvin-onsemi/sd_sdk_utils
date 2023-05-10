from cmd_line_args import get_command_line_parser
import os

def main():
    parser = get_command_line_parser()
    args = parser.parse_args()

    from sd_sdk_python import get_product_manager
    product_manager = get_product_manager()
    print(f"\nFound an SDK at {os.environ['SD_SDK_ROOT']}")
    print(f"ProductManager Version: 0x{hex(product_manager.Version)}")

if __name__ == '__main__':
    main()
