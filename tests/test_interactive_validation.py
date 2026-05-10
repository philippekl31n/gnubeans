"""Tests for interactive mode currency validation."""
from gnubeans.interactive import is_valid_beancount_currency, _validate_currency


# ---------------------------------------------------------------------------
# is_valid_beancount_currency
# ---------------------------------------------------------------------------

def test_simple_symbol_valid():
    assert is_valid_beancount_currency("VBMPX") is True

def test_single_letter_valid():
    assert is_valid_beancount_currency("T") is True

def test_mid_dash_valid():
    assert is_valid_beancount_currency("VSCIX-I") is True

def test_sanitized_numeric_valid():
    assert is_valid_beancount_currency("C1003057") is True

def test_digit_leading_invalid():
    assert is_valid_beancount_currency("1003057") is False

def test_empty_invalid():
    assert is_valid_beancount_currency("") is False

def test_trailing_dash_invalid():
    assert is_valid_beancount_currency("FUND-") is False

def test_leading_dash_invalid():
    assert is_valid_beancount_currency("-FUND") is False

def test_lowercase_invalid():
    assert is_valid_beancount_currency("vbmpx") is False

def test_too_long_invalid():
    assert is_valid_beancount_currency("A" * 25) is False

def test_exactly_24_chars_valid():
    assert is_valid_beancount_currency("A" * 24) is True

def test_ampersand_invalid():
    assert is_valid_beancount_currency("AT&T") is False

def test_space_invalid():
    assert is_valid_beancount_currency("FUND A") is False


# ---------------------------------------------------------------------------
# _validate_currency — questionary callback
# ---------------------------------------------------------------------------

def test_validate_returns_true_for_valid():
    assert _validate_currency("VBMPX") is True

def test_validate_returns_true_for_sanitized_numeric():
    assert _validate_currency("C1003057") is True

def test_validate_returns_error_string_for_digit_leading():
    result = _validate_currency("1003057")
    assert isinstance(result, str)
    assert "1003057" in result

def test_validate_returns_error_string_for_empty():
    result = _validate_currency("")
    assert isinstance(result, str)
    assert "empty" in result.lower()

def test_validate_returns_error_string_for_too_long():
    result = _validate_currency("A" * 25)
    assert isinstance(result, str)

def test_validate_accepts_lowercase_by_uppercasing():
    # user types lowercase; validate uppercases before checking
    assert _validate_currency("vbmpx") is True

def test_validate_strips_whitespace_before_checking():
    assert _validate_currency("  VBMPX  ") is True
