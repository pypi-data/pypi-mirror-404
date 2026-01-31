from colorama import Fore, Style, init
init(autoreset=True)

def print_info(msg):
    print(Fore.CYAN + str(msg) + Style.RESET_ALL)

def print_warn(msg):
    print(Fore.YELLOW + str(msg) + Style.RESET_ALL)

def print_error(msg):
    print(Fore.RED + str(msg) + Style.RESET_ALL)

def print_success(msg):
    print(Fore.GREEN + str(msg) + Style.RESET_ALL)

def print_debug(msg):
    print(Fore.MAGENTA + str(msg) + Style.RESET_ALL)
