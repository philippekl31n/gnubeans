# Design Decisions

## Implementation language: Python

### Rationale

1. **Ecosystem alignment.** Beancount is Python-native — `beancount.core` can be used to construct entry objects programmatically and validate output with `bean-check`, rather than writing raw strings and hoping they parse.

2. **Exact rational arithmetic.** GnuCash stores every amount as `numerator/denominator`. Python's stdlib `fractions.Fraction` handles this exactly, with no floating-point drift — critical for amounts that must balance to zero.

3. **XML + gzip out of the box.** `gzip` + `xml.etree.ElementTree` (or `lxml` for XPath) are stdlib or widely available; no dependency wrangling.

4. **Scale is trivial.** several thousand transactions is noise for Python. Performance will never be the constraint.

### Main tradeoff

The case against Python is **static typing**: the GnuCash schema has a lot of structure (13 account types, 6 slot value types, split annotations, lot references) and a typed language like Haskell or Rust would make the mapping exhaustive by construction — the compiler catches unhandled cases. In Python those are found at runtime, or by writing explicit `assert`s and `dataclass` definitions carefully.

For a project of this scope — one-time or occasional conversion — the Beancount ecosystem integration and fast iteration outweigh the type-safety argument. If this were expected to be maintained long-term or distributed widely, Haskell or Rust would be worth the setup cost.

### Implementation approach

- `dataclasses` for the intermediate representation (one class per GnuCash entity)
- Plain-text generation for beancount output (see *Beancount as a dependency* below)
- `fractions.Fraction` for all amount arithmetic
- `xml.etree.ElementTree` for XML parsing
- `gzip` for transparent decompression of `.gnucash` files

---

## Beancount as a dependency

### Decision

Beancount is an **optional** dependency, not a hard one. The tool writes plain-text beancount journal output directly, without using `beancount.core` for output construction. If `bean-check` is available on `$PATH`, it is run automatically after conversion and its results reported. Users who want this validation behaviour can install it explicitly:

```
pip install gnubeans[validate]   # or: uv tool install gnubeans[validate]
```

If `bean-check` is not found, the tool emits a single line directing the user to validate manually.

### Rationale

Beancount 2.x and 3.x have divergent APIs — `beancount.core` changed significantly between versions, and both are actively in use. Treating beancount as a hard dependency would require maintaining two code paths or constraining users to one version. Since the beancount journal format is a stable text format that both versions can consume, there is no need to take on that coupling just to produce output.

Writing plain text also keeps the tool lighter (fewer transitive dependencies) and version-agnostic, which is appropriate for a one-shot migration tool.

### Resolved open decision

This closes the *Target Beancount version* open decision: by not depending on `beancount.core`, the question of which version to target is eliminated at the library level. The output text should be valid beancount 2.x journal syntax; 3.x is a strict superset for core directives so compatibility with both follows automatically.

---

## Input format

### Decision

Accept only `.gnucash` files (gzip-compressed XML). Decompress transparently in memory at the start of execution using Python's `gzip` module. No temp file, no streaming, no alternative input path.

### Rationale

The `.gnucash` format is always gzip-compressed XML — that is the canonical on-disk representation. Decompressed XML is an implementation detail, not a user-facing format. GnuCash files from even the most prolific users rarely exceed 20MB compressed; the in-memory DOM is well under 200MB in the worst case, comfortably within any environment where Python runs. A size-based threshold for switching to streaming or a temp file would be principled in theory but is over-engineering for this use case.

### Resolved open decision

This closes the *Input handling* open decision.

---

## Interactive judgment calls

### Decision

The tool has three operating modes, controlled by flags:

Flag semantics:

- **`--plan [filepath|-]`** — YAML destination: a path, `-` for stdout, or omitted for `<stem>.gnubeans.yaml` alongside the input file.
- **`--apply [filepath|-]`** — plan input source: a path, `-` for stdin, or omitted for `<stem>.gnubeans.yaml` alongside the input file.
- **`-o`/`--output [filepath|-]`** — beancount output destination in interactive and `--apply` modes: a path, `-` for stdout, or omitted for `<stem>.beancount` alongside the input file.

`--plan` and `--apply` are symmetric: `-` means stdout or stdin respectively, enabling pipelines with no intermediate file:

```
# fully non-interactive conversion using opinionated defaults
gnubeans ledger.gnucash --plan - | gnubeans ledger.gnucash --apply -

# with an editing step in between
gnubeans ledger.gnucash --plan - | yq '.accounts |= ...' | gnubeans ledger.gnucash --apply -

# apply a saved plan, validate output immediately
gnubeans ledger.gnucash --apply plan.yaml -o - | bean-check -
```

**Default (interactive):** The tool parses the input, then at each judgment call presents its opinionated default and prompts for confirmation or override. Context is rendered by **Rich**; prompts are handled by **questionary** (see *TUI libraries*). When a default is derived from one or more source values in the input file, all contributing sources are shown above the prompt so the user has complete information. Similar decisions are batched (e.g. all proposed account renames shown as a Rich table — accept all or edit by number). After all decisions are confirmed, beancount output is written and the full set of decisions is saved to `<stem>.gnubeans.yaml` alongside the input file. On a subsequent run, if that file already exists it is loaded as the pre-filled defaults at each prompt.

**`--plan [filepath|-]`:** Non-interactive. Writes opinionated defaults to the plan YAML without prompting and exits — no beancount output is produced.

**`--apply [filepath|-]`:** Reads decisions from the plan file (or stdin) and executes without prompting, producing beancount output.

### Rationale

A pure two-phase (plan-then-convert) flow is auditable and scriptable but adds friction for the common case: a user doing a one-shot migration who just wants to confirm the tool's choices and get output. A single interactive pass compresses both phases into one execution while still producing the YAML artifact for repeatability. Expert users who have already reviewed a plan file can skip prompts entirely with `--apply`.

`--apply` pairs naturally with `--plan` (generate vs. apply) and follows the convention established by tools like Terraform. `--config` was considered but rejected as it conventionally implies tool configuration rather than a user-generated data file.

`-` as a filepath meaning stdin/stdout is a standard Unix convention. TTY detection is avoided in favour of explicit opt-in, keeping output destination predictable regardless of how the tool is invoked.

---

## TUI libraries

### Decision

**Rich** + **questionary** are core dependencies.

- **Rich** renders all formatted output: source-value context before prompts, batch-decision tables, warnings, and the final conversion summary.
- **questionary** handles all interactive input: text fields (with pre-filled defaults), confirmations, and indexed-row editing for batch decisions. It is built on prompt_toolkit and provides the `?`-prefixed prompt style that is the de facto standard in modern Python CLIs.

Both are unconditional dependencies — not optional extras — because interactive mode is the default execution path.

The general prompt pattern is:

```
  <source label 1>   <source value 1>       ← Rich: dim label, normal value
  <source label 2>   <source value 2>

? <Decision label>: <proposed default>›     ← questionary text prompt, default pre-filled
```

For batch decisions a Rich table with indexed rows is shown first, followed by a questionary confirmation:

```
  ┌─────┬─────────────────────────────────────┬───────────────────────────────────┐
  │  #  │ GnuCash name                        │ Proposed Beancount name           │
  ├─────┼─────────────────────────────────────┼───────────────────────────────────┤
  │  1  │ Chase Total Checking (2930)         │ Chase-Total-Checking-2930         │
  │  2  │ Vanguard Total Bond Market …        │ Vanguard-Total-Bond-Market-…      │
  └─────┴─────────────────────────────────────┴───────────────────────────────────┘
? Accept all, or enter row numbers to edit (e.g. 1,3): ›
```

### Rationale

Rich is the Python standard for terminal output formatting and is actively maintained by Textualize. questionary is the most ergonomic Python prompt library; its API is a thin, idiomatic layer over prompt_toolkit. Together they cover the full interactive surface without overlapping.

Textual (Textualize's full TUI widget framework) was considered and rejected: it is designed for persistent, application-like UIs, whereas gnubeans needs a linear, top-to-bottom prompt flow that completes and exits — the same usage model questionary is built for.

prompt_toolkit directly was considered but rejected in favour of questionary's higher-level API, which handles cursor positioning, default pre-filling, and keyboard shortcuts without boilerplate.

---

## Repository structure

```
gnubeans/
├── src/
│   └── gnubeans/
│       ├── __init__.py
│       ├── __main__.py       # enables python -m gnubeans
│       ├── cli.py            # argument parsing, entry point
│       ├── model.py          # schema-agnostic intermediate repr
│       ├── planner.py        # judgment calls, plan YAML I/O
│       ├── interactive.py    # batched prompting UI
│       ├── gnucash/
│       │   ├── __init__.py   # file format detection + dispatch
│       │   └── v2.py         # gnc-v2 file format reader
│       └── beancount/
│           ├── __init__.py   # target version dispatch
│           ├── v2.py         # beancount 2.x writer
│           └── v3.py         # beancount 3.x writer
├── tests/
│   └── fixtures/             # small synthetic .gnucash files
├── docs/
│   ├── design-decisions.md
│   ├── gnucash-beancount-mapping.md
│   └── Beancount - Language Syntax.md
├── pyproject.toml
├── README.md
└── CLAUDE.md
```

The `src/` layout is the PyPA-recommended standard for published packages — it prevents accidental imports of the package from the project root during development and testing. The package name carries the role (`gnucash/` = reading, `beancount/` = writing); format variants are module names within each subpackage (`v2.py`, `v3.py`), following the convention used by Django's `db/backends/` and SQLAlchemy's `dialects/`. `model.py` is the format-agnostic intermediate representation bridging the two.

Support for additional GnuCash file format versions is not included in the initial release; the `gnucash/` subpackage structure accommodates them when added.

`.gnucash` and `.gnucash.xml` files are personal financial data and must not be committed. Both patterns are gitignored. Test fixtures use small synthetic `.gnucash` files under `tests/fixtures/`.

---

## Version tracking

CalVer with scheme `YYYY.MM` (e.g. `2025.04`), with a `.N` patch suffix when needed (`2025.04.1`). The version lives in `pyproject.toml` as the single source of truth and is bumped manually before tagging. Git tags (`v2025.04`) mark releases.

Semver was considered but rejected: this is a migration tool with no API compatibility promises to make. CalVer communicates recency, which is the only signal users need.

Automated version derivation from git tags (`hatch-vcs`, `setuptools-scm`) is not used — the overhead is not justified for a tool with infrequent releases.

---

## Open decisions

### Account names
- How to sanitize GnuCash names to valid Beancount components (spaces→dashes, strip parens, capitalize — but what about collisions after sanitization?)
- Whether to preserve the GnuCash hierarchy depth verbatim or flatten/restructure it
- Whether placeholder (non-postable) accounts get `open` directives at all
- How to map the `TRADING` account type — present when `options/Accounts/Use Trading Accounts = "t"`; Beancount has no equivalent construct and the booking model differs
- How to handle `NONE`-typed accounts — the schema permits this value but GnuCash assigns no financial meaning to it

### Amounts & commodities
- How to handle `cmdty:id` values that aren't valid Beancount symbols — e.g., `FUND-A` (dash mid-symbol is technically valid), `1234567` (starts with digit, which is invalid)
- Whether to emit `commodity` directives for CURRENCY-space entries or only for securities

### Transactions
- How to split GnuCash's single `trn:description` field into Beancount's optional payee + narration (always narration-only, heuristic split, or configurable?)
- How to generate the capital-gains posting on security sales — GnuCash doesn't record it explicitly; Beancount requires the transaction to balance
- How to handle the `template` commodity / scheduled-transaction splits that appear in the ledger
- How to handle voided transactions (any split with `split:reconciled-state = v`) — options: drop silently, emit as a comment block, or emit as a flagged `!` transaction with a `voided:` note

### Lots & cost basis
- Whether to track lots at all (full `{cost, date, "label"}`) or use a simpler `{cost}` annotation — depends on whether the output needs to support FIFO/LIFO queries
- How to recover cost-per-unit when multiple purchases were posted to the same GnuCash lot

### Opening balances
- Whether to emit `pad` + `balance` pairs for opening-balance transactions, or emit them as explicit transactions against `Equity:Opening-Balances`

### Balance assertions
- Whether to generate `balance` directives at all, and if so, from what trigger (reconciled splits? end of each month?)

### Output structure
- Single `.beancount` file vs. split by year/account-type with `include` directives
- `option "title"` — resolved: emit using `options/Business/Company Name` from `book:slots` when non-empty, falling back to the input filename stem. In interactive mode both source values are shown above the prompt (Rich), and the proposed value is pre-filled in the input field (questionary):
- `option "operating_currency"` — deferred: cannot be reliably inferred from book metadata alone (no currency signal exists at the book level in the schema). Emit only once account or commodity data is available to derive it from. Not part of root-element conversion output.
- `option "title"` interactive prompt example:
  ```
    Company Name (book:slots)   not set
    Filename stem               2025

  ? Book title: 2025›
  ```
  In the plan YAML the same source values are preserved as comments so `--plan`/`--apply` users have equivalent context when reviewing the file before applying:
  ```yaml
  output:
    # Company Name (book:slots): not set
    # Filename stem: "2025"
    title: "2025"
  ```

### Target beancount output version
- Whether to expose a `--beancount-version [2|3]` flag or detect from the environment (e.g. shelling out to `bean-check --version` if on `$PATH`)
- Default version if unspecified (2 is the conservative choice; 3 is the emerging standard)

### Error handling
- Fail-fast on unexpected data vs. warn-and-skip with a report at the end

