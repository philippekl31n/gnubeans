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

---

## Open decisions

### Account names
- How to sanitize GnuCash names to valid Beancount components (spaces→dashes, strip parens, capitalize — but what about collisions after sanitization?)
- Whether to preserve the GnuCash hierarchy depth verbatim or flatten/restructure it
- Whether placeholder (non-postable) accounts get `open` directives at all

### Amounts & commodities
- How to handle `cmdty:id` values that aren't valid Beancount symbols — e.g., `FUND-A` (dash mid-symbol is technically valid), `1234567` (starts with digit, which is invalid)
- Whether to emit `commodity` directives for CURRENCY-space entries or only for securities

### Transactions
- How to split GnuCash's single `trn:description` field into Beancount's optional payee + narration (always narration-only, heuristic split, or configurable?)
- How to generate the capital-gains posting on security sales — GnuCash doesn't record it explicitly; Beancount requires the transaction to balance
- How to handle the `template` commodity / scheduled-transaction splits that appear in the ledger

### Lots & cost basis
- Whether to track lots at all (full `{cost, date, "label"}`) or use a simpler `{cost}` annotation — depends on whether the output needs to support FIFO/LIFO queries
- How to recover cost-per-unit when multiple purchases were posted to the same GnuCash lot

### Opening balances
- Whether to emit `pad` + `balance` pairs for opening-balance transactions, or emit them as explicit transactions against `Equity:Opening-Balances`

### Balance assertions
- Whether to generate `balance` directives at all, and if so, from what trigger (reconciled splits? end of each month?)

### Output structure
- Single `.beancount` file vs. split by year/account-type with `include` directives
- Whether to emit `option "operating_currency"` and `option "title"` from book metadata

### Input handling
- Accept only decompressed XML, only compressed `.gnucash`, or both transparently

### Error handling
- Fail-fast on unexpected data vs. warn-and-skip with a report at the end

### Target Beancount version
- Beancount 2.x (`beancount.core`) vs. Beancount 3.x (different API, still maturing)
