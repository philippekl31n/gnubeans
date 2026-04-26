# Design Decisions

## Implementation language: Python

### Rationale

1. **Ecosystem alignment.** Beancount is Python-native — `beancount.core` can be used to construct entry objects programmatically and validate output with `bean-check`, rather than writing raw strings and hoping they parse.

2. **Exact rational arithmetic.** GnuCash stores every amount as `numerator/denominator`. Python's stdlib `fractions.Fraction` handles this exactly, with no floating-point drift — critical for amounts that must balance to zero.

3. **XML + gzip out of the box.** `gzip` + `xml.etree.ElementTree` (or `lxml` for XPath) are stdlib or widely available; no dependency wrangling.

4. **Scale is trivial.** several thousand transactions is noise for Python. Performance will never be the constraint.

### Main tradeoff

The case against Python is **static typing**: the GnuCash schema has a lot of structure (13 account types, 6 slot value types, split annotations, lot references) and a typed language like Haskell or Rust would make the mapping exhaustive by construction — the compiler catches unhandled cases. In Python those are found at runtime, or by writing explicit `assert`s and `dataclass` definitions carefully.

For a project of this scope — one-time or occasional conversion, ~1 KLOC — the Beancount ecosystem integration and fast iteration outweigh the type-safety argument. If this were expected to be maintained long-term or distributed widely, Haskell or Rust would be worth the setup cost.

### Implementation approach

- `dataclasses` for the intermediate representation (one class per GnuCash entity)
- `beancount.core` for constructing and serialising output entries
- `fractions.Fraction` for all amount arithmetic
- `xml.etree.ElementTree` for XML parsing
- `gzip` for transparent decompression of `.gnucash` files
