# gnubeans

Convert a [GnuCash](https://www.gnucash.org/) ledger to [Beancount](https://github.com/beancount/beancount) plain-text accounting format.

## Goals

- Parse GnuCash's compressed XML format and produce a valid, importable Beancount ledger file.
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

- [`docs/gnucash-beancount-mapping.md`](docs/gnucash-beancount-mapping.md) — detailed field-by-field mapping from the GnuCash `gnc-v2` XML schema to Beancount directives
- [Beancount Language Syntax](https://furius.ca/beancount/doc/syntax)
- [GnuCash XML file format](https://wiki.gnucash.org/wiki/GnuCash_XML_format)

## Installation

Clone the repository and install in editable mode:

```
git clone https://github.com/PhilippeKlein/gnubeans.git
cd gnubeans
pip install -e .
```

To also install `bean-check` for automatic output validation:

```
pip install -e ".[validate]"
```

## Usage

### Interactive (default)

```
gnubeans ledger.gnucash
```

Prompts for confirmation at each judgment call — account renames, commodity symbol fixes, dropped entities — with an opinionated default pre-filled at each step. Writes `ledger.beancount` and saves all decisions to `ledger.gnubeans.yaml` for reproducible re-runs.

### Generate a plan without converting

```
gnubeans ledger.gnucash --plan
```

Writes opinionated defaults to `ledger.gnubeans.yaml` without prompting. Edit the file, then apply it:

```
gnubeans ledger.gnucash --apply
```

### Pipeline mode

`--plan` accepts `-` to write the plan YAML to stdout; `--apply` accepts `-` to read it from stdin:

```
gnubeans ledger.gnucash --plan - | gnubeans ledger.gnucash --apply -
```

Use `-o -` to write beancount output to stdout:

```
gnubeans ledger.gnucash --apply plan.yaml -o - | bean-check -
```

### Output path

By default output is written alongside the input file. Use `-o` to redirect:

```
gnubeans ledger.gnucash -o /tmp/ledger.beancount
gnubeans ledger.gnucash --apply plan.yaml -o /tmp/ledger.beancount
```
