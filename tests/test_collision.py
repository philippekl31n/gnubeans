"""Tests for commodity symbol collision detection and resolution."""
import pytest
from xml.sax.saxutils import escape as _e

from gnubeans.gnucash.v2 import parse
from gnubeans.beancount.v2 import render
from gnubeans.planner import proposed_commodity_symbols, commodity_plan_yaml

from helpers import _BOOK_OPEN, _BOOK_CLOSE

STEM = "example"


def _two_commodity_xml(space1, id1, space2, id2) -> bytes:
    return (_BOOK_OPEN + f"""\
<gnc:commodity version="2.0.0">
  <cmdty:space>{_e(space1)}</cmdty:space>
  <cmdty:id>{_e(id1)}</cmdty:id>
  <cmdty:fraction>10000</cmdty:fraction>
</gnc:commodity>
<gnc:commodity version="2.0.0">
  <cmdty:space>{_e(space2)}</cmdty:space>
  <cmdty:id>{_e(id2)}</cmdty:id>
  <cmdty:fraction>10000</cmdty:fraction>
</gnc:commodity>
""" + _BOOK_CLOSE).encode()


# ---------------------------------------------------------------------------
# Detection: warning on stderr
# ---------------------------------------------------------------------------

def test_collision_warning_emitted_to_stderr(capsys):
    # AT&T and AT[T] both sanitize to AT-T
    xml = _two_commodity_xml("NYSE", "AT&T", "NYSE", "AT[T]")
    parse(xml, filename_stem=STEM)
    err = capsys.readouterr().err
    assert "WARNING" in err
    assert "collision" in err.lower()


def test_collision_warning_names_both_originals(capsys):
    xml = _two_commodity_xml("NYSE", "AT&T", "NYSE", "AT[T]")
    parse(xml, filename_stem=STEM)
    err = capsys.readouterr().err
    assert '"AT&T"' in err
    assert '"AT[T]"' in err


def test_collision_warning_names_conflicting_currency(capsys):
    xml = _two_commodity_xml("NYSE", "AT&T", "NYSE", "AT[T]")
    parse(xml, filename_stem=STEM)
    err = capsys.readouterr().err
    assert '"AT-T"' in err


def test_pre_sanitized_id_collides_with_numeric(capsys):
    # C1003057 is already a valid symbol; 1003057 sanitizes to C1003057
    xml = _two_commodity_xml("Vanguard", "C1003057", "Vanguard", "1003057")
    parse(xml, filename_stem=STEM)
    err = capsys.readouterr().err
    assert "WARNING" in err
    assert "collision" in err.lower()


def test_no_collision_warning_for_distinct_symbols(capsys):
    xml = _two_commodity_xml("Vanguard", "VBMPX", "ETrade", "GLD")
    parse(xml, filename_stem=STEM)
    err = capsys.readouterr().err
    assert "collision" not in err.lower()


# ---------------------------------------------------------------------------
# Model: colliding commodities still present for user resolution
# ---------------------------------------------------------------------------

def test_colliding_commodities_both_present_in_model():
    xml = _two_commodity_xml("NYSE", "AT&T", "NYSE", "AT[T]")
    book = parse(xml, filename_stem=STEM)
    # Both originals must be retained so the user can resolve the conflict
    original_ids = {c.gnc_id or c.id for c in book.commodities}
    assert "AT&T" in original_ids
    assert "AT[T]" in original_ids


# ---------------------------------------------------------------------------
# Plan YAML: colliding entries marked as requiring resolution
# ---------------------------------------------------------------------------

def test_plan_yaml_marks_colliding_entries():
    xml = _two_commodity_xml("NYSE", "AT&T", "NYSE", "AT[T]")
    book = parse(xml, filename_stem=STEM)
    confirmed = proposed_commodity_symbols(book)
    yaml = commodity_plan_yaml(book, confirmed)
    # Both entries must be present and flagged so the user knows to resolve
    assert "AT-T" in yaml
    assert "COLLISION" in yaml.upper()


def test_plan_yaml_collision_entries_include_both_originals():
    xml = _two_commodity_xml("NYSE", "AT&T", "NYSE", "AT[T]")
    book = parse(xml, filename_stem=STEM)
    confirmed = proposed_commodity_symbols(book)
    yaml = commodity_plan_yaml(book, confirmed)
    assert '"AT&T"' in yaml
    assert '"AT[T]"' in yaml


# ---------------------------------------------------------------------------
# Render: unresolved collision raises an error
# ---------------------------------------------------------------------------

def test_render_raises_on_unresolved_collision():
    xml = _two_commodity_xml("NYSE", "AT&T", "NYSE", "AT[T]")
    book = parse(xml, filename_stem=STEM)
    # Default symbols still collide — render must refuse
    confirmed = proposed_commodity_symbols(book)
    with pytest.raises(ValueError, match="collision"):
        render(book, commodity_symbols=confirmed)


def test_render_succeeds_when_collision_resolved():
    xml = _two_commodity_xml("NYSE", "AT&T", "NYSE", "AT[T]")
    book = parse(xml, filename_stem=STEM)
    # User resolves by assigning distinct symbols
    confirmed = {"AT&T": "ATT", "AT[T]": "AT-T"}
    output = render(book, commodity_symbols=confirmed)
    assert "1900-01-01 commodity ATT\n" in output
    assert "1900-01-01 commodity AT-T\n" in output


# ---------------------------------------------------------------------------
# End-to-end: parse → resolve → render with correct metadata
# ---------------------------------------------------------------------------

def test_e2e_resolved_collision_emits_gnc_cmdty_id_for_both():
    xml = _two_commodity_xml("NYSE", "AT&T", "NYSE", "AT[T]")
    book = parse(xml, filename_stem=STEM)
    confirmed = {"AT&T": "ATT", "AT[T]": "ATBT"}
    output = render(book, commodity_symbols=confirmed)
    assert '  gnc_cmdty_id: "AT&T"\n' in output
    assert '  gnc_cmdty_id: "AT[T]"\n' in output


def test_e2e_resolved_collision_emits_correct_directive_lines():
    xml = _two_commodity_xml("NYSE", "AT&T", "NYSE", "AT[T]")
    book = parse(xml, filename_stem=STEM)
    confirmed = {"AT&T": "ATT", "AT[T]": "ATBT"}
    output = render(book, commodity_symbols=confirmed)
    assert "1900-01-01 commodity ATT\n" in output
    assert "1900-01-01 commodity ATBT\n" in output


def test_e2e_no_collision_renders_without_gnc_cmdty_id():
    xml = _two_commodity_xml("Vanguard", "VBMPX", "ETrade", "GLD")
    book = parse(xml, filename_stem=STEM)
    confirmed = {"VBMPX": "VBMPX", "GLD": "GLD"}
    output = render(book, commodity_symbols=confirmed)
    assert "gnc_cmdty_id" not in output
