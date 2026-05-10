# Prior Art

Before writing tests for any new schema element, research these tools for edge cases not obvious from the spec or mapping doc. Document findings here by element so the gap analysis accumulates over time.

## Known converters

| Tool | Source | Approach |
|---|---|---|
| [henriquebastos/gnucash-to-beancount](https://github.com/henriquebastos/gnucash-to-beancount) | GnuCash XML via `piecash` | Python; golden-file tests; supports accounts, transactions, commodities, prices |
| [dtrai2/gnucash-to-beancount](https://github.com/dtrai2/gnucash-to-beancount) | GnuCash sqlite3 via `piecash` | Python; config-driven; minimal commodity handling; no stock splits |
| [beancount/ledger2beancount](https://github.com/beancount/ledger2beancount) | Ledger format | Perl; comprehensive test suite; overlapping commodity sanitization concerns |

---

## `gnc:commodity` — gap analysis (vs. current test suite)

Researched against the three converters above. Gaps are listed in order of priority.

### Medium priority

| Gap | Notes |
|---|---|
| `cmdty:quote_source` parsed and emitted as `gnc_quote_source:` | Field is in the mapping doc but absent from the model and renderer. |
| `cmdty:xcode` (ISIN/CUSIP) parsed into model | Documented in the mapping as `gnc_cmdty_xcode:` optional metadata; no model field or parser logic exists yet. |
| Commodity ordering is deterministic | XML order may vary across GnuCash versions/saves. Output order is untested. |

### Low priority

| Gap | Notes |
|---|---|
| `cmdty:quote_tz` explicitly dropped | Dropped in parser but no specific test asserting it does not appear in output. |
| `cmdty:fraction` = 1 edge case | Minimum precision commodity. No functional impact on current output. |
