import argparse
import sys

from btkeepalive import __version__
from btkeepalive.app import Application
from btkeepalive.config import config_path


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="btkeepalive",
        description=(
            "BT KeepAlive — Windows tray utility for Bluetooth headphone keepalive"
        ),
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"BT KeepAlive {__version__}",
    )
    parser.add_argument(
        "--config-path",
        action="store_true",
        help="Print the config file path and exit",
    )
    parser.add_argument(
        "--no-autoplay",
        action="store_true",
        help="Do not start audio until Play is chosen from the tray",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)
    if args.config_path:
        print(config_path())
        return
    sys.exit(Application(no_autoplay=args.no_autoplay).run())


if __name__ == "__main__":
    main()
