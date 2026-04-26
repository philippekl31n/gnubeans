import argparse

DEFAULT = object()


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="gnubeans",
        description="Convert a GnuCash file to Beancount format.",
    )
    p.add_argument("input", metavar="FILE.gnucash", help="GnuCash input file")

    mode = p.add_mutually_exclusive_group()
    mode.add_argument(
        "--plan",
        metavar="FILE|-",
        nargs="?",
        const=DEFAULT,
        default=None,
        help="write opinionated defaults to a plan YAML and exit"
             " (default: <stem>.gnubeans.yaml)",
    )
    mode.add_argument(
        "--apply",
        metavar="FILE|-",
        nargs="?",
        const=DEFAULT,
        default=None,
        help="apply a plan YAML and produce beancount output without prompting"
             " (default: <stem>.gnubeans.yaml; use - for stdin)",
    )

    p.add_argument(
        "-o", "--output",
        metavar="FILE|-",
        default=None,
        help="beancount output destination in interactive and --apply modes"
             " (default: <stem>.beancount; use - for stdout)",
    )
    return p


def main() -> None:
    build_parser().parse_args()
