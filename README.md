# abswedge

A tool to convert [GnuCash](https://www.gnucash.org/) ledger files to [Beancount](https://github.com/beancount/beancount) plain-text accounting format.

## Goals

- Parse GnuCash's compressed XML format (`gnc:book version="2.0.0"`) and produce a valid, importable Beancount ledger file.
- Preserve the full account hierarchy, converting GnuCash's 13 account types to the appropriate Beancount root types (`Assets`, `Liabilities`, `Equity`, `Income`, `Expenses`).
- Convert all transactions with their splits, correctly handling:
  - Simple currency postings
  - Multi-currency transfers (using `@` price annotations)
  - Security buy/sell transactions (using `{cost}` lot annotations)
  - Investment lot tracking (mapping GnuCash's `gnc:lot` cost-basis records to Beancount's `{cost, date, "label"}` syntax)
- Export the price history database (`gnc:pricedb`) as Beancount `price` directives.
- Emit `commodity` directives with descriptive metadata for all non-currency instruments.
- Produce well-formed account names: sanitize GnuCash names (spaces, parentheses, special characters) to Beancount's `[A-Za-z0-9-]` component syntax.
- Be idempotent and deterministic: the same input always produces the same output.

## Out of scope

GnuCash's business-accounting module (customers, vendors, invoices, purchase orders, scheduled transactions, budgets) has no equivalent in plain Beancount and will not be converted.

## Reference

- [`gnucash-beancount-mapping.md`](gnucash-beancount-mapping.md) — detailed field-by-field mapping from the GnuCash `gnc-v2` XML schema to Beancount directives.
- [Beancount Language Syntax](https://furius.ca/beancount/doc/syntax)
- [GnuCash XML file format](https://wiki.gnucash.org/wiki/GnuCash_XML_format)
