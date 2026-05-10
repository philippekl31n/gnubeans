"""Tests for proposed defaults and plan YAML generation."""
from gnubeans.gnucash.v2 import parse
from gnubeans.planner import proposed_commodity_symbols, commodity_plan_yaml

from helpers import commodity_xml

STEM = "example"


# ---------------------------------------------------------------------------
# proposed_commodity_symbols — what interactive mode shows as default
# ---------------------------------------------------------------------------

def test_proposed_is_sanitized_id_for_numeric_cmdty_id():
    # numeric ID → sanitized to C-prefix; that sanitized form is the proposal
    xml = commodity_xml("Vanguard", "1003057", name="Vanguard Target Enrollment 2038")
    book = parse(xml, filename_stem=STEM)
    proposed = proposed_commodity_symbols(book)
    assert proposed == {"1003057": "C1003057"}


def test_proposed_is_user_symbol_when_present():
    # user_symbol takes precedence over cmdty:id as the proposed default
    xml = commodity_xml("Vanguard", "VSCIX-I",
                        name="Vanguard Small-Cap Index Institutional",
                        user_symbol="VSCIX")
    book = parse(xml, filename_stem=STEM)
    proposed = proposed_commodity_symbols(book)
    assert proposed == {"VSCIX-I": "VSCIX"}


def test_proposed_is_cmdty_id_when_no_user_symbol():
    xml = commodity_xml("Vanguard", "VBMPX",
                        name="Vanguard Total Bond Market Index Fund")
    book = parse(xml, filename_stem=STEM)
    proposed = proposed_commodity_symbols(book)
    assert proposed == {"VBMPX": "VBMPX"}


def test_proposed_uses_original_id_as_key_not_sanitized():
    # the key is always the original cmdty:id, even after sanitization
    xml = commodity_xml("Vanguard", "1003057")
    book = parse(xml, filename_stem=STEM)
    proposed = proposed_commodity_symbols(book)
    assert "1003057" in proposed
    assert "C1003057" not in proposed


def test_proposed_empty_when_no_commodities():
    from helpers import _BOOK_OPEN, _BOOK_CLOSE
    xml = (_BOOK_OPEN + _BOOK_CLOSE).encode()
    book = parse(xml, filename_stem=STEM)
    assert proposed_commodity_symbols(book) == {}


# ---------------------------------------------------------------------------
# commodity_plan_yaml — YAML output structure
# ---------------------------------------------------------------------------

def test_yaml_key_is_confirmed_symbol():
    xml = commodity_xml("Vanguard", "1003057")
    book = parse(xml, filename_stem=STEM)
    confirmed = {"1003057": "C1003057"}
    yaml = commodity_plan_yaml(book, confirmed)
    assert "  C1003057:\n" in yaml


def test_yaml_gnc_cmdty_id_active_when_sanitized():
    xml = commodity_xml("Vanguard", "1003057")
    book = parse(xml, filename_stem=STEM)
    confirmed = {"1003057": "C1003057"}
    yaml = commodity_plan_yaml(book, confirmed)
    assert '    gnc_cmdty_id: "1003057"\n' in yaml
    assert '    # gnc_cmdty_id:' not in yaml


def test_yaml_gnc_cmdty_id_commented_when_not_sanitized():
    xml = commodity_xml("Vanguard", "VBMPX")
    book = parse(xml, filename_stem=STEM)
    confirmed = {"VBMPX": "VBMPX"}
    yaml = commodity_plan_yaml(book, confirmed)
    assert '    # gnc_cmdty_id: "VBMPX"\n' in yaml
    assert '    gnc_cmdty_id: "VBMPX"\n' not in yaml


def test_yaml_gnc_user_symbol_comment_present_when_set():
    xml = commodity_xml("Vanguard", "VSCIX-I", user_symbol="VSCIX")
    book = parse(xml, filename_stem=STEM)
    confirmed = {"VSCIX-I": "VSCIX"}
    yaml = commodity_plan_yaml(book, confirmed)
    assert '    # gnc_user_symbol: "VSCIX"\n' in yaml


def test_yaml_gnc_user_symbol_absent_when_not_set():
    xml = commodity_xml("Vanguard", "VBMPX")
    book = parse(xml, filename_stem=STEM)
    confirmed = {"VBMPX": "VBMPX"}
    yaml = commodity_plan_yaml(book, confirmed)
    assert '    # gnc_user_symbol:' not in yaml


def test_yaml_export_comment_always_present():
    xml = commodity_xml("Vanguard", "VBMPX")
    book = parse(xml, filename_stem=STEM)
    confirmed = {"VBMPX": "VBMPX"}
    yaml = commodity_plan_yaml(book, confirmed)
    assert '    # export: "<EXCHANGE_CODE>:VBMPX"\n' in yaml


def test_yaml_header_included():
    xml = commodity_xml("Vanguard", "VBMPX")
    book = parse(xml, filename_stem=STEM)
    yaml = commodity_plan_yaml(book, {"VBMPX": "VBMPX"})
    assert "bean-report" in yaml
    assert "EXCHANGE_CODE" in yaml
