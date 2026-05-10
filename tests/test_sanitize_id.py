"""Unit tests for commodity ID sanitization."""
import pytest
from gnubeans.gnucash.v2 import _sanitize_id


# ---------------------------------------------------------------------------
# Already-valid symbols — no change, no warning
# ---------------------------------------------------------------------------

def test_valid_symbol_unchanged():
    assert _sanitize_id("VBMPX") == ("VBMPX", "")

def test_single_char_valid():
    assert _sanitize_id("T") == ("T", "")

def test_mid_dash_valid():
    # dash in non-edge position is allowed by the beancount spec
    assert _sanitize_id("VSCIX-I") == ("VSCIX-I", "")

def test_mid_period_valid():
    assert _sanitize_id("B.V") == ("B.V", "")

def test_mid_apostrophe_valid():
    assert _sanitize_id("O'REILLY") == ("O'REILLY", "")

def test_no_warning_for_valid_symbol(capsys):
    _sanitize_id("VBMPX")
    assert capsys.readouterr().err == ""


# ---------------------------------------------------------------------------
# Lowercase → uppercase
# ---------------------------------------------------------------------------

def test_lowercase_uppercased():
    result, original = _sanitize_id("vbmpx")
    assert result == "VBMPX"
    assert original == "vbmpx"

def test_mixed_case_uppercased():
    result, original = _sanitize_id("VbMpX")
    assert result == "VBMPX"
    assert original == "VbMpX"


# ---------------------------------------------------------------------------
# Digit-leading → C prefix
# ---------------------------------------------------------------------------

def test_digit_leading_gets_c_prefix():
    result, original = _sanitize_id("1003057")
    assert result == "C1003057"
    assert original == "1003057"

def test_digit_leading_short():
    result, original = _sanitize_id("4651")
    assert result == "C4651"
    assert original == "4651"

def test_warning_text_for_digit_leading(capsys):
    _sanitize_id("1003057")
    err = capsys.readouterr().err
    assert "WARNING" in err
    assert '"1003057"' in err
    assert '"C1003057"' in err
    assert "suggesting" in err


# ---------------------------------------------------------------------------
# Invalid middle characters → dashes
# ---------------------------------------------------------------------------

def test_ampersand_replaced():
    result, original = _sanitize_id("AT&T")
    assert result == "AT-T"
    assert original == "AT&T"

def test_space_replaced():
    result, original = _sanitize_id("FUND A")
    assert result == "FUND-A"
    assert original == "FUND A"

def test_parenthesis_replaced():
    result, original = _sanitize_id("FUND(A)")
    assert result == "FUND-A"
    assert original == "FUND(A)"

def test_consecutive_invalid_chars_collapsed_to_one_dash():
    result, _ = _sanitize_id("AT&&T")
    assert result == "AT-T"

def test_slash_replaced():
    result, original = _sanitize_id("A/B")
    assert result == "A-B"
    assert original == "A/B"


# ---------------------------------------------------------------------------
# Edge punctuation stripped
# ---------------------------------------------------------------------------

def test_trailing_dash_stripped():
    result, original = _sanitize_id("FUND-")
    assert result == "FUND"
    assert original == "FUND-"

def test_leading_period_stripped():
    result, original = _sanitize_id(".FUND")
    assert result == "FUND"
    assert original == ".FUND"

def test_leading_and_trailing_stripped():
    result, original = _sanitize_id("-FUND-")
    assert result == "FUND"
    assert original == "-FUND-"

def test_leading_punct_then_digit_gets_c_prefix():
    # strip leading "." → "1003057" → digit → prefix C
    result, original = _sanitize_id(".1003057")
    assert result == "C1003057"
    assert original == ".1003057"


# ---------------------------------------------------------------------------
# Length > 24 → truncated
# ---------------------------------------------------------------------------

def test_truncated_to_24():
    long_id = "A" * 30
    result, original = _sanitize_id(long_id)
    assert result == "A" * 24
    assert original == long_id

def test_truncation_then_trailing_punct_stripped():
    # position 24 (0-indexed 23) is a dash; must be stripped after truncation
    id_ = "A" * 23 + "-Z"        # 25 chars; truncated to "A"*23 + "-" → strip → "A"*23
    result, original = _sanitize_id(id_)
    assert result == "A" * 23
    assert original == id_


# ---------------------------------------------------------------------------
# Degenerate inputs
# ---------------------------------------------------------------------------

def test_all_dashes_gives_c_fallback():
    result, original = _sanitize_id("---")
    assert result == "C"
    assert original == "---"

def test_empty_after_strip_gives_c_fallback():
    result, original = _sanitize_id(".")
    assert result == "C"
    assert original == "."
