from pathlib import Path

from gnubeans.gnucash.v2 import parse
from gnubeans.beancount.v2 import render

FIXTURES = Path(__file__).parent / "fixtures"


def _xml(name: str) -> bytes:
    return (FIXTURES / name).read_bytes()


STEM = "example"


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
    assert itot.ticker == "ITOT"


def test_commodity_user_symbol_absent_when_no_slot():
    book = parse(_xml("commodities.xml"), filename_stem=STEM)
    vbmpx = next(c for c in book.commodities if c.id == "VBMPX")
    assert vbmpx.ticker == ""


# ---------------------------------------------------------------------------
# Rendering: commodity directive structure
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
    output = render(book)
    assert '  exchange:' not in output


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
    output = render(book)
    assert "commodity template" not in output
