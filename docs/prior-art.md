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

### High priority

| Gap | Notes |
|---|---|
| Numeric `cmdty:id` sanitized to valid beancount currency | Open decision: `"1003057"` → `"C1003057"`. ledger2beancount prefixes with `X`; our design uses `C`. Not yet implemented or tested. |
| Collision after sanitization | Two different GnuCash IDs sanitizing to the same beancount currency. None of the prior art tools handle this well; it needs a plan-level decision. |
| `ISO4217` space filtered same as `CURRENCY` | We filter `CURRENCY` but have no test for the legacy `ISO4217` namespace (used by older GnuCash files). |
| Commodity with absent/empty `cmdty:name` | CURRENCY commodities carry no name in GnuCash. Non-currency commodities occasionally also lack one. Renderer behaviour with empty `name` is untested. |

### Medium priority

| Gap | Notes |
|---|---|
| `cmdty:quote_source` parsed and emitted as `gnc_quote_source:` | Field is in the mapping doc and fixture but absent from the model and renderer. |
| Final-character sanitization | ledger2beancount replaces non-letter/digit trailing characters with `X` (e.g. `VSCIX-` → `VSCIX-X`). Our sanitization rules don't yet address this. |
| `cmdty:xcode` (ISIN/CUSIP) parsed into model | Documented in the mapping as `gnc_cmdty_xcode:` optional metadata; no model field or parser logic exists yet. |
| Commodity ordering is deterministic | XML order may vary across GnuCash versions/saves. Output order is untested. |

### Low priority

| Gap | Notes |
|---|---|
| Symbol longer than 24 characters | Beancount rejects >24 chars. The schema allows free text in `cmdty:id`; long fund codes are rare but possible. |
| `cmdty:quote_tz` explicitly dropped | Fixture has it; we test that `yahoo` doesn't appear in output but don't assert that `quote_tz` specifically is absent. |
| `cmdty:fraction` = 1 edge case | The minimum precision commodity (template and some custom commodities). No functional impact on current output. |
