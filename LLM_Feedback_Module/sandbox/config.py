import configparser
import mmap
import os

TEST = False
CONFIG_DIR = os.getenv("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")
config = configparser.ConfigParser()
options_file = os.path.expanduser(f"{CONFIG_DIR}/tcp_server/options.conf")
cached_file_path = ""


def read_config():
    """Read and parse the options file."""
    try:
        config.read(options_file)
    except configparser.Error as e:
        print(f"Configuration error:\n {e}")
        exit(1)


read_config()


def find_file() -> str:
    """
    Return the path to the file to search as read from the server configuration.
    """
    global cached_file_path
    config_path = os.path.expanduser("~/.config/tcp_server/config")
    try:
        with open(config_path, "r+b") as f:
            with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mf:
                for line in mf.read().decode().splitlines():
                    if line.startswith("linuxpath="):
                        cached_file_path = line.split("=", 1)[1].strip()
                        return cached_file_path
    except FileNotFoundError as e:
        if TEST:
            return ""
        raise FileNotFoundError("Configuration file not found!").with_traceback(
            e.__traceback__
        )
    except IOError as e:
        raise IOError("IOError!").with_traceback(e.__traceback__)
    except Exception as e:
        print("Unexpected error!", e)
        raise
    raise FileNotFoundError("Configuration file is missing!")


def get_port_opt() -> int:
    """Return the PORT configuration option value."""
    try:
        return config.getint("options", "PORT", fallback=DEFAULT_PORT)
    except ValueError as e:
        raise configparser.Error(
            "PORT value provided is not an integer"
        ).with_traceback(e.__traceback__)


def get_roq_opt() -> bool:
    """Return the REREAD_ON_QUERY configuration option value."""
    try:
        return config.getboolean("options", "REREAD_ON_QUERY", fallback=False)
    except ValueError as e:
        raise configparser.Error(
            "REREAD_ON_QUERY option provided is not a boolean"
        ).with_traceback(e.__traceback__)


def get_ssl_opt() -> bool:
    """Return the SSL configuration option value."""
    try:
        return config.getboolean("options", "SSL", fallback=False)
    except ValueError as e:
        raise configparser.Error("SSL option provided is not a boolean").with_traceback(
            e.__traceback__
        )


def get_opts() -> tuple[int, bool, bool]:
    """Gather configuration options and return them as a tuple."""
    try:
        port = get_port_opt()
        roq = get_roq_opt()
        ssl = get_ssl_opt()
    except configparser.Error as e:
        print(f"Configuration error:\n {e}")
        exit(1)
    return port, roq, ssl


DEFAULT_PORT = 44445
FILE_PATH = cached_file_path or find_file()
PORT, REREAD_ON_QUERY, SSL = get_opts()
