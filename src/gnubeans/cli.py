import argparse
import gzip
import sys
from pathlib import Path

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


def _read_gnucash(path: Path) -> bytes:
    try:
        with gzip.open(path, 'rb') as f:
            return f.read()
    except gzip.BadGzipFile:
        sys.exit(f"error: {path} is not a valid .gnucash file (expected gzip-compressed XML)")


def _write_output(text: str, dest, stem: Path) -> None:
    if dest is None:
        out_path = stem.parent / (stem.stem + '.beancount')
        out_path.write_text(text)
        print(f"wrote {out_path}", file=sys.stderr)
    elif dest == '-':
        sys.stdout.write(text)
    else:
        Path(dest).write_text(text)
        print(f"wrote {dest}", file=sys.stderr)


def main() -> None:
    from gnubeans.gnucash.v2 import parse
    from gnubeans.beancount.v2 import render
    from gnubeans.interactive import prompt_commodity_symbols
    from gnubeans.planner import proposed_commodity_symbols, commodity_plan_yaml

    args = build_parser().parse_args()
    input_path = Path(args.input)
    xml = _read_gnucash(input_path)
    book = parse(xml, filename_stem=input_path.stem)

    if args.plan is not None:
        confirmed = proposed_commodity_symbols(book)
        yaml_text = commodity_plan_yaml(book, confirmed)
        if args.plan is DEFAULT:
            dest = input_path.parent / (input_path.stem + '.gnubeans.yaml')
            dest.write_text(yaml_text)
            print(f"wrote {dest}", file=sys.stderr)
        elif args.plan == '-':
            sys.stdout.write(yaml_text)
        else:
            Path(args.plan).write_text(yaml_text)
            print(f"wrote {args.plan}", file=sys.stderr)

    elif args.apply is not None:
        sys.exit("--apply mode not yet implemented")

    else:
        confirmed = prompt_commodity_symbols(book)
        try:
            output = render(book, confirmed)
        except ValueError as e:
            sys.exit(f"error: {e}")
        _write_output(output, args.output, input_path)
