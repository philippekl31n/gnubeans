import pytest
from gnubeans.cli import build_parser, DEFAULT

# DEFAULT is the sentinel argparse stores when a flag is given without a value,
# meaning "use the default filepath for this mode".

INPUT = "ledger.gnucash"


# --- required argument ---

def test_no_args_exits_with_error():
    with pytest.raises(SystemExit) as exc:
        build_parser().parse_args([])
    assert exc.value.code == 2


def test_help_exits_cleanly():
    with pytest.raises(SystemExit) as exc:
        build_parser().parse_args(["--help"])
    assert exc.value.code == 0


def test_unknown_flag_exits_with_error():
    with pytest.raises(SystemExit) as exc:
        build_parser().parse_args([INPUT, "--unknown"])
    assert exc.value.code == 2


# --- default (interactive) mode ---

def test_input_only_defaults_all_none():
    args = build_parser().parse_args([INPUT])
    assert args.input == INPUT
    assert args.plan is None
    assert args.apply is None
    assert args.output is None


def test_interactive_mode_with_output_filepath():
    args = build_parser().parse_args([INPUT, "-o", "/tmp/out.beancount"])
    assert args.plan is None
    assert args.apply is None
    assert args.output == "/tmp/out.beancount"


def test_interactive_mode_with_output_stdout():
    args = build_parser().parse_args([INPUT, "-o", "-"])
    assert args.output == "-"


# --- --plan ---

def test_plan_without_value_uses_sentinel():
    args = build_parser().parse_args([INPUT, "--plan"])
    assert args.plan is DEFAULT


def test_plan_with_filepath():
    args = build_parser().parse_args([INPUT, "--plan", "/tmp/out.yaml"])
    assert args.plan == "/tmp/out.yaml"


def test_plan_stdout():
    args = build_parser().parse_args([INPUT, "--plan", "-"])
    assert args.plan == "-"


# --- --apply ---

def test_apply_without_value_uses_sentinel():
    args = build_parser().parse_args([INPUT, "--apply"])
    assert args.apply is DEFAULT


def test_apply_with_filepath():
    args = build_parser().parse_args([INPUT, "--apply", "/tmp/plan.yaml"])
    assert args.apply == "/tmp/plan.yaml"


def test_apply_stdin():
    args = build_parser().parse_args([INPUT, "--apply", "-"])
    assert args.apply == "-"


def test_apply_with_output_filepath():
    args = build_parser().parse_args([INPUT, "--apply", "/tmp/plan.yaml", "-o", "/tmp/out.beancount"])
    assert args.apply == "/tmp/plan.yaml"
    assert args.output == "/tmp/out.beancount"


def test_apply_with_output_long_form():
    args = build_parser().parse_args([INPUT, "--apply", "/tmp/plan.yaml", "--output", "/tmp/out.beancount"])
    assert args.output == "/tmp/out.beancount"


def test_apply_stdin_output_stdout():
    args = build_parser().parse_args([INPUT, "--apply", "-", "-o", "-"])
    assert args.apply == "-"
    assert args.output == "-"


# --- mutual exclusion ---

def test_plan_and_apply_are_mutually_exclusive():
    with pytest.raises(SystemExit) as exc:
        build_parser().parse_args([INPUT, "--plan", "--apply"])
    assert exc.value.code == 2


def test_plan_with_filepath_and_apply_are_mutually_exclusive():
    with pytest.raises(SystemExit) as exc:
        build_parser().parse_args([INPUT, "--plan", "/tmp/out.yaml", "--apply"])
    assert exc.value.code == 2
