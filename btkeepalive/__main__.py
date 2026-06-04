import sys

from btkeepalive.app import Application


def main() -> None:
    sys.exit(Application().run())


if __name__ == "__main__":
    main()
