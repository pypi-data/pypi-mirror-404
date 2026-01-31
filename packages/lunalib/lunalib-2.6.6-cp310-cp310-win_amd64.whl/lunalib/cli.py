# lunalib/cli.py
import argparse
from .luna_lib import LunaLib

def main():
    """Command line interface for LunaLib"""
    parser = argparse.ArgumentParser(description="LunaLib Cryptocurrency Wallet")
    parser.add_argument('--version', action='store_true', help='Show version')
    
    args = parser.parse_args()
    
    if args.version:
        print(f"LunaLib v{LunaLib.get_version()}")
    else:
        print("LunaLib - Use 'luna-wallet --help' for options")

if __name__ == "__main__":
    main()