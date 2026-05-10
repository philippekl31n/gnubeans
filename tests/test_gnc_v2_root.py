from pathlib import Path

import pytest

from gnubeans.gnucash.v2 import parse
from gnubeans.beancount.v2 import render

FIXTURES = Path(__file__).parent / "fixtures"


def _xml(name: str) -> bytes:
    return (FIXTURES / name).read_bytes()


# ---------------------------------------------------------------------------
# Parsing: book title
# ---------------------------------------------------------------------------

def test_title_taken_from_company_name():
    book = parse(_xml("root_only_with_title.xml"), filename_stem="example")
    assert book.title == "BayBook"


def test_title_falls_back_to_filename_stem_when_company_name_empty():
    book = parse(_xml("root_only_no_title.xml"), filename_stem="example")
    assert book.title == "example"


def test_title_falls_back_to_filename_stem_when_company_name_slot_absent():
    xml = b"""<?xml version="1.0" encoding="utf-8" ?>
<gnc-v2
     xmlns:gnc="http://www.gnucash.org/XML/gnc"
     xmlns:book="http://www.gnucash.org/XML/book"
     xmlns:cd="http://www.gnucash.org/XML/cd"
     xmlns:slot="http://www.gnucash.org/XML/slot">
<gnc:count-data cd:type="book">1</gnc:count-data>
<gnc:book version="2.0.0">
<book:id type="guid">4ad968fd0ff94c4591d32146e7c5d99f</book:id>
</gnc:book>
</gnc-v2>"""
    book = parse(xml, filename_stem="example")
    assert book.title == "example"


# ---------------------------------------------------------------------------
# Parsing: fields that must be dropped
# ---------------------------------------------------------------------------

def test_book_guid_not_exposed_on_model():
    book = parse(_xml("root_only_with_title.xml"), filename_stem="example")
    assert not hasattr(book, "id") or book.id is None


# ---------------------------------------------------------------------------
# Rendering: option "title"
# ---------------------------------------------------------------------------

def test_render_emits_title_option_from_company_name():
    book = parse(_xml("root_only_with_title.xml"), filename_stem="example")
    assert 'option "title" "BayBook"' in render(book)


def test_render_emits_title_option_from_filename_stem():
    book = parse(_xml("root_only_no_title.xml"), filename_stem="example")
    assert 'option "title" "example"' in render(book)


def test_render_does_not_expose_book_guid():
    book = parse(_xml("root_only_with_title.xml"), filename_stem="example")
    assert "4ad968fd0ff94c4591d32146e7c5d99f" not in render(book)


# ---------------------------------------------------------------------------
# Complete output: root-only conversion produces exactly option "title".
# option "operating_currency" is deferred until account/commodity data is
# available; it must not appear when converting a book-only file.
# ---------------------------------------------------------------------------

def test_complete_output_root_only_with_title():
    book = parse(_xml("root_only_with_title.xml"), filename_stem="example")
    assert render(book) == 'option "title" "BayBook"\n'


def test_complete_output_root_only_no_title_uses_stem():
    book = parse(_xml("root_only_no_title.xml"), filename_stem="example")
    assert render(book) == 'option "title" "example"\n'


def test_operating_currency_absent_from_root_only_output():
    book = parse(_xml("root_only_with_title.xml"), filename_stem="example")
    assert "operating_currency" not in render(book)
