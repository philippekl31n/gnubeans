from pathlib import Path

from gnubeans.gnucash.v2 import parse
from gnubeans.beancount.v2 import render

from helpers import commodity_xml

FIXTURES = Path(__file__).parent / "fixtures"
STEM = "example"


def _xml(name: str) -> bytes:
    return (FIXTURES / name).read_bytes()


# ---------------------------------------------------------------------------
# Parsing: commodity count and filtering
# ---------------------------------------------------------------------------

def test_securities_parsed():
    book = parse(_xml("commodities.xml"), filename_stem=STEM)
    ids = {c.id for c in book.commodities}
    assert ids == {"VBMPX", "GLD", "ITOT"}


def test_template_commodity_excluded():
    book = parse(_xml("commodities.xml"), filename_stem=STEM)
    assert not any(c.id == "template" for c in book.commodities)
    assert not any(c.space == "template" for c in book.commodities)


def test_iso4217_currency_not_parsed_as_security():
    # ISO4217 is the legacy currency namespace (schema-valid; modern GnuCash
    # uses CURRENCY). Both identify monetary currencies, not securities, so
    # neither appears in book.commodities — they are handled separately by
    # the emit_currency_directives plan decision.
    xml = commodity_xml("ISO4217", "GBP")
    book = parse(xml, filename_stem=STEM)
    assert book.commodities == []


# ---------------------------------------------------------------------------
# Parsing: commodity fields
# ---------------------------------------------------------------------------

def test_commodity_space_parsed():
    book = parse(_xml("commodities.xml"), filename_stem=STEM)
    vbmpx = next(c for c in book.commodities if c.id == "VBMPX")
    assert vbmpx.space == "Vanguard"


def test_commodity_name_parsed():
    book = parse(_xml("commodities.xml"), filename_stem=STEM)
    vbmpx = next(c for c in book.commodities if c.id == "VBMPX")
    assert vbmpx.name == "Vanguard Total Bond Market Index Fund Institutional Plus Shares"


def test_commodity_user_symbol_parsed():
    book = parse(_xml("commodities.xml"), filename_stem=STEM)
    itot = next(c for c in book.commodities if c.id == "ITOT")
    assert itot.user_symbol == "ITOT"


def test_commodity_user_symbol_absent_when_no_slot():
    book = parse(_xml("commodities.xml"), filename_stem=STEM)
    vbmpx = next(c for c in book.commodities if c.id == "VBMPX")
    assert vbmpx.user_symbol == ""


def test_gnc_id_empty_when_not_sanitized():
    book = parse(_xml("commodities.xml"), filename_stem=STEM)
    vbmpx = next(c for c in book.commodities if c.id == "VBMPX")
    assert vbmpx.gnc_id == ""


def test_gnc_id_set_when_sanitized():
    xml = commodity_xml("Vanguard", "1003057", name="Vanguard Target Enrollment 2038")
    book = parse(xml, filename_stem=STEM)
    assert len(book.commodities) == 1
    c = book.commodities[0]
    assert c.id == "C1003057"
    assert c.gnc_id == "1003057"


# ---------------------------------------------------------------------------
# Rendering: basic commodity directive structure
# ---------------------------------------------------------------------------

def test_commodity_directive_line():
    book = parse(_xml("commodities.xml"), filename_stem=STEM)
    output = render(book)
    assert "1900-01-01 commodity VBMPX\n" in output


def test_commodity_name_metadata():
    book = parse(_xml("commodities.xml"), filename_stem=STEM)
    output = render(book)
    assert '  name: "Vanguard Total Bond Market Index Fund Institutional Plus Shares"\n' in output


def test_commodity_namespace_metadata():
    book = parse(_xml("commodities.xml"), filename_stem=STEM)
    output = render(book)
    assert '  gnc_namespace: "Vanguard"\n' in output


def test_exchange_key_not_in_output():
    book = parse(_xml("commodities.xml"), filename_stem=STEM)
    assert '  exchange:' not in render(book)


# ---------------------------------------------------------------------------
# Rendering: empty field suppression
# ---------------------------------------------------------------------------

def test_name_not_emitted_when_empty():
    xml = commodity_xml("Vanguard", "VBMPX", name="")
    book = parse(xml, filename_stem=STEM)
    assert "  name:" not in render(book)


def test_namespace_not_emitted_when_space_empty():
    # Build XML where cmdty:space is present but empty
    raw = b"""<?xml version="1.0" encoding="utf-8" ?>
<gnc-v2
     xmlns:gnc="http://www.gnucash.org/XML/gnc"
     xmlns:book="http://www.gnucash.org/XML/book"
     xmlns:cd="http://www.gnucash.org/XML/cd"
     xmlns:cmdty="http://www.gnucash.org/XML/cmdty">
<gnc:count-data cd:type="book">1</gnc:count-data>
<gnc:book version="2.0.0">
<book:id type="guid">4ad968fd0ff94c4591d32146e7c5d99f</book:id>
<gnc:commodity version="2.0.0">
  <cmdty:space></cmdty:space>
  <cmdty:id>VBMPX</cmdty:id>
  <cmdty:fraction>10000</cmdty:fraction>
</gnc:commodity>
</gnc:book>
</gnc-v2>"""
    book = parse(raw, filename_stem=STEM)
    assert "gnc_namespace" not in render(book)


# ---------------------------------------------------------------------------
# Rendering: commodity_symbols overrides
# ---------------------------------------------------------------------------

def test_confirmed_symbol_used_in_directive():
    xml = commodity_xml("Vanguard", "1003057", name="Vanguard Target Enrollment 2038")
    book = parse(xml, filename_stem=STEM)
    output = render(book, commodity_symbols={"1003057": "C1003057"})
    assert "1900-01-01 commodity C1003057\n" in output


def test_user_override_symbol_used_in_directive():
    xml = commodity_xml("Vanguard", "1003057", name="Vanguard Target Enrollment 2038")
    book = parse(xml, filename_stem=STEM)
    output = render(book, commodity_symbols={"1003057": "VTGT2038"})
    assert "1900-01-01 commodity VTGT2038\n" in output


def test_gnc_cmdty_id_emitted_when_confirmed_differs_from_original():
    xml = commodity_xml("Vanguard", "1003057")
    book = parse(xml, filename_stem=STEM)
    output = render(book, commodity_symbols={"1003057": "C1003057"})
    assert '  gnc_cmdty_id: "1003057"\n' in output


def test_gnc_cmdty_id_not_emitted_when_confirmed_equals_original():
    xml = commodity_xml("Vanguard", "VBMPX")
    book = parse(xml, filename_stem=STEM)
    output = render(book, commodity_symbols={"VBMPX": "VBMPX"})
    assert "gnc_cmdty_id" not in output


def test_render_without_commodity_symbols_uses_id_as_default():
    xml = commodity_xml("Vanguard", "VBMPX")
    book = parse(xml, filename_stem=STEM)
    assert "1900-01-01 commodity VBMPX\n" in render(book)


def test_render_without_commodity_symbols_prefers_user_symbol():
    xml = commodity_xml("Vanguard", "VSCIX-I", user_symbol="VSCIX")
    book = parse(xml, filename_stem=STEM)
    output = render(book)
    assert "1900-01-01 commodity VSCIX\n" in output
    assert '  gnc_cmdty_id: "VSCIX-I"\n' in output


# ---------------------------------------------------------------------------
# Rendering: dropped fields
# ---------------------------------------------------------------------------

def test_get_quotes_fields_not_in_output():
    book = parse(_xml("commodities.xml"), filename_stem=STEM)
    output = render(book)
    assert "get_quotes" not in output
    assert "quote_source" not in output
    assert "yahoo" not in output


def test_template_commodity_not_in_output():
    book = parse(_xml("commodities.xml"), filename_stem=STEM)
    assert "commodity template" not in render(book)
