# GnuCash gnc-v2 → Beancount Mapping

Source: GnuCash XML format (`gnc:book version="2.0.0"`, namespace `http://www.gnucash.org/XML/gnc`)  
Target: Beancount plain-text ledger format (Language Syntax, April 2016/2026 edition)

---

## Document structure (`gnc:` namespace)

The root `<gnc-v2>` element contains exactly one `<gnc:book>`, which holds all financial data as a flat sequence of child elements. The `gnc:` namespace owns the top-level structural wrappers.

| GnuCash element | Role | Beancount equivalent |
|---|---|---|
| `<gnc-v2>` | Root document | The `.beancount` file itself |
| `<gnc:book>` | Single ledger | The `.beancount` file; `option "title" "..."` for book metadata |
| `<gnc:count-data>` | Element counts (informational) | None — no equivalent |
| `<gnc:commodity>` | Commodity definition | `commodity` directive |
| `<gnc:pricedb>` | Price history database | `price` directives |
| `<gnc:account>` | Account node | `open` directive |
| `<gnc:transaction>` | Double-entry transaction | Transaction (`*`/`!` flag + postings) |
| `<gnc:lot>` (nested in `<act:lots>`) | Investment cost lot | Cost lot annotation `{cost, date, "label"}` on postings |

---

## `gnc:commodity` → `commodity` directive

**Namespaces used:** `cmdty:`

GnuCash commodities fall into two classes by `cmdty:space`:

- **`CURRENCY`** (or legacy **`ISO4217`**) — ISO 4217 currency codes (`USD`, `GBP`, …). The schema permits both namespace strings for currencies; modern GnuCash writes `CURRENCY`, older files may use `ISO4217`. Beancount treats these as regular commodities; no `commodity` directive is required, but one may be added. Whether to emit them is a single yes/no plan decision applied to all currencies in the file (see *Output structure* in design decisions).
- **Non-`CURRENCY`** (e.g., `Vanguard`, `Fidelity`, `Robinhood`) — represent securities. These **do** warrant an explicit `commodity` directive.
- **`template`** — GnuCash internal commodity used for scheduled transactions. Always dropped; no Beancount equivalent.

### Field mapping

| GnuCash field | Notes | Beancount target |
|---|---|---|
| `cmdty:id` | Ticker/symbol (`VBMPX`, `USD`, …) | The commodity symbol on the `commodity` line. Must match `[A-Z][A-Z0-9'._\-]{0,23}` — characters outside that set need sanitizing. |
| `cmdty:space` | Exchange/namespace (`Vanguard`, `CURRENCY`, …) | `exchange:` metadata field; omitted for CURRENCY-space entries (the value "CURRENCY" is meaningless as an exchange name) |
| `cmdty:name` | Full name | `name:` metadata field. For CURRENCY-space entries GnuCash stores no name — looked up from ISO 4217 instead. |
| `cmdty:fraction` | Smallest tradeable unit (100 = 0.01, 10000 = 0.0001) | Implicit in Beancount from the precision of amounts; no direct field, but guides rounding |
| `cmdty:get_quotes` | Flag element — price fetching enabled | No equivalent; drop |
| `cmdty:quote_source` | Price source string (`currency`, `yahoo`, …) | `quote-source:` metadata — preserved as informational (Beancount allows arbitrary custom metadata on `commodity` directives) |
| `cmdty:quote_tz` | Price timezone | No equivalent; drop |
| `cmdty:xcode` | Exchange code (freeform — e.g. `MUTF`, `NYSEARCA`, `NASDAQ`) | `export:` metadata, constructed as `"XCODE:SYMBOL"` where SYMBOL is `cmdty:id`. Omitted when `cmdty:xcode` is absent. |
| `cmdty:slots` → `user_symbol` | Display ticker (may differ from `cmdty:id`) | `ticker:` metadata |
| — | `export:` beancount metadata | For CURRENCY-space commodities: always `export: "CASH"`. For securities: `export: "XCODE:SYMBOL"` when `cmdty:xcode` is present; omitted otherwise. |

### Example

```xml
<gnc:commodity version="2.0.0">
  <cmdty:space>Vanguard</cmdty:space>
  <cmdty:id>VBMPX</cmdty:id>
  <cmdty:name>Vanguard Total Bond Market Index Fund Admiral Shares</cmdty:name>
  <cmdty:fraction>10000</cmdty:fraction>
</gnc:commodity>
```

```beancount
1900-01-01 commodity VBMPX
  name: "Vanguard Total Bond Market Index Fund Admiral Shares"
  exchange: "Vanguard"
```

---

## `gnc:pricedb` → `price` directives

**Namespaces used:** `price:`, `cmdty:`, `ts:`

The `<gnc:pricedb>` contains a flat list of `<price>` entries. Each maps to one Beancount `price` directive.

### Field mapping

| GnuCash field | Notes | Beancount target |
|---|---|---|
| `price:id` | GUID (internal key) | Dropped — no equivalent |
| `price:commodity` → `cmdty:id` | The thing being priced | Commodity symbol on the `price` line |
| `price:currency` → `cmdty:id` | The quote currency | Price amount currency |
| `price:time` → `ts:date` | Full timestamp (`YYYY-MM-DD HH:MM:SS +0000`) | Date portion only (`YYYY-MM-DD`); Beancount has no intra-day time |
| `price:value` | Rational `numerator/denominator` | Computed decimal: `numerator ÷ denominator` |
| `price:source` | Origin string (`user:price`, `user:xfer-dialog`, …) | Dropped, or `source:` metadata |
| `price:type` | Classification (`transaction`, …) | Dropped, or `type:` metadata |

### Rational number representation

GnuCash stores all numeric values as exact rationals (e.g., `26479/20000`). These must be converted to decimals for Beancount, preserving precision appropriate to the commodity's `cmdty:fraction`.

### Example

```xml
<price>
  <price:commodity><cmdty:space>CURRENCY</cmdty:space><cmdty:id>GBP</cmdty:id></price:commodity>
  <price:currency><cmdty:space>CURRENCY</cmdty:space><cmdty:id>USD</cmdty:id></price:currency>
  <price:time><ts:date>2026-01-07 10:59:00 +0000</ts:date></price:time>
  <price:value>331/250</price:value>
</price>
```

```beancount
2026-01-07 price GBP  1.324 USD
```

---

## `gnc:account` → `open` directive

**Namespaces used:** `act:`, `cmdty:`, `slot:`

Accounts form a tree via `act:parent` references, but are stored flat. The full Beancount account name must be reconstructed by walking the parent chain from root to leaf, joining `act:name` segments with `:`.

### Account type mapping

The schema defines 20 `act:type` values. Beancount requires one of five root prefixes:

| GnuCash `act:type` | Beancount root | Notes |
|---|---|---|
| `ROOT` | — | Synthetic root; not emitted as an account |
| `ASSET` | `Assets` | Generic asset grouping |
| `BANK` | `Assets` | Checking/savings accounts |
| `CHECKING` | `Assets` | Checking account subtype — same mapping as `BANK` |
| `SAVINGS` | `Assets` | Savings account subtype — same mapping as `BANK` |
| `CASH` | `Assets` | Physical cash |
| `RECEIVABLE` | `Assets` | Accounts receivable |
| `STOCK` | `Assets` | Individual securities |
| `MUTUAL` | `Assets` | Mutual funds / ETFs |
| `MONEYMRKT` | `Assets` | Money market account — same mapping as `MUTUAL` |
| `CURRENCY` | `Assets` | Foreign-currency holding account |
| `LIABILITY` | `Liabilities` | Generic liability |
| `CREDIT` | `Liabilities` | Credit cards |
| `CREDITLINE` | `Liabilities` | Revolving line of credit — same mapping as `CREDIT` |
| `PAYABLE` | `Liabilities` | Accounts payable |
| `EQUITY` | `Equity` | Retained earnings, opening balances |
| `INCOME` | `Income` | Revenue accounts |
| `EXPENSE` | `Expenses` | Expenditure accounts |
| `TRADING` | — | GnuCash trading accounts; only present when `options/Accounts/Use Trading Accounts = "t"`; no direct Beancount equivalent — see open decisions |
| `NONE` | — | Unset/unknown type; flag for manual review |

### Field mapping

| GnuCash field | Notes | Beancount target |
|---|---|---|
| `act:name` + ancestor chain | Hierarchy reconstructed from `act:parent` | Colon-joined account name, e.g., `Assets:Chase:Checking` |
| `act:type` | See table above | Determines the first path segment |
| `act:commodity` → `cmdty:id` | Account's native currency/commodity | Optional currency constraint on `open`: `open Date Account SYMBOL` |
| `act:commodity-scu` | Smallest commodity unit | Informs decimal precision, not directly emitted |
| `act:id` | GUID (used to resolve `act:parent` and split references) | Dropped from output |
| `act:description` | Free-text description | `description:` metadata on `open`, or a `note` directive |
| `act:code` | Account number / institution code | `account-number:` metadata |
| `act:slots` → `placeholder: "true"` | Non-postable grouping account | Open normally; Beancount allows posting to any open account |
| `act:slots` → `notes` | Account notes | `note:` metadata on `open`, or separate `note` directive |
| `act:slots` → `equity-type: "opening-balance"` | Marks the opening-balance equity account | Map to `Equity:Opening-Balances` by convention |
| `act:slots` → `reconcile-info` | Last reconcile date/interval | No Beancount equivalent; drop |
| `act:slots` → `import-map-bayes` | Bayesian auto-categorization hints | No Beancount equivalent; drop |
| `act:slots` → `balance-limit` | Soft balance floor/ceiling | No Beancount equivalent; drop |
| `act:lots` | Container for `gnc:lot` children | See Lot section below |

### Account name sanitization

Beancount account name components must begin with a capital letter or digit and contain only letters, digits, and `-`. GnuCash names may contain spaces, parentheses, and other punctuation. Sanitization rules:

1. Capitalize the first letter of each component.
2. Replace spaces with `-`.
3. Strip or replace characters outside `[A-Za-z0-9-]`.
4. Ensure no component is empty.

### Example

```xml
<gnc:account version="2.0.0">
  <act:name>Chase Total Checking (2930)</act:name>
  <act:type>BANK</act:type>
  <act:commodity><cmdty:space>CURRENCY</cmdty:space><cmdty:id>USD</cmdty:id></act:commodity>
  <act:description>Checking Account</act:description>
  <act:code>2930</act:code>
  <act:parent type="guid"><!-- Current Assets --></act:parent>
</gnc:account>
```

```beancount
2000-01-01 open Assets:Current-Assets:Chase-Total-Checking-2930  USD
  description: "Checking Account"
  account-number: "2930"
```

---

## `gnc:transaction` → transaction directive

**Namespaces used:** `trn:`, `split:`, `cmdty:`, `ts:`, `slot:`

Each `<gnc:transaction>` becomes one Beancount transaction. Its child `<trn:split>` elements become postings.

### Transaction field mapping

| GnuCash field | Notes | Beancount target |
|---|---|---|
| `trn:date-posted` → `ts:date` | Effective date | Transaction date (`YYYY-MM-DD`) |
| `trn:description` | Free text — functions as payee or narration | Narration string (quoted). If it matches a known payee pattern, split into `"Payee" "Narration"` |
| `trn:currency` → `cmdty:id` | Transaction's balancing currency | Implicit — Beancount infers from postings; used to validate `split:value` columns |
| `trn:id` | GUID | Dropped, or `gnucash-id:` metadata |
| `trn:date-entered` → `ts:date` | Entry timestamp | Dropped, or `entered:` metadata |
| `trn:num` | Check/reference number (rarely populated) | `check-ref:` metadata, or prepend to narration |
| `trn:slots` → `notes` | Transaction memo | Second string in `"Payee" "Narration"`, or `note:` metadata |
| `trn:slots` → `date-posted` (gdate) | Canonical local date without time | Use in preference to the timestamp in `trn:date-posted` |

### Flag mapping

GnuCash has no transaction-level status flag equivalent to Beancount's `*`/`!`. Use `*` for all transactions; if any split has `split:reconciled-state = n` (unreconciled), consider using `!`. Transactions where any split carries `v` (voided) require special handling — see open decisions.

### Split → posting field mapping

| GnuCash field | Notes | Beancount target |
|---|---|---|
| `split:account` (GUID) | Account reference | Resolved to full Beancount account name |
| `split:value` | Rational — amount in transaction currency (`trn:currency`) | Cash leg of the posting amount |
| `split:quantity` | Rational — units in the account's own commodity | Commodity units when different from `split:value` (securities, foreign currency) |
| `split:memo` | Per-split free text | `; inline comment` or `memo:` posting metadata |
| `split:action` | Label: `Buy`, `Sell`, `Div`, `Int`, `Reinvest`, … | `action:` posting metadata |
| `split:reconciled-state` | `n` = unreconciled, `c` = cleared, `y` = reconciled, `f` = fiscally closed (period close), `v` = voided | `reconciled:` posting metadata; `y`/`c`/`f` may inform `balance` assertions; `v` requires special handling — see open decisions |
| `split:reconcile-date` | Timestamp when split was reconciled | `reconcile-date:` posting metadata, or drop |
| `split:id` | GUID | Dropped, or `gnucash-id:` metadata |
| `split:lot` (GUID) | Cost-lot reference | Drives `{cost}` or `{cost, date, "label"}` annotation on the posting |
| `split:slots` | KVP metadata on the individual split | Posting-level metadata; usually drop |

### Value vs. quantity: detecting commodity postings

When `split:value ≠ split:quantity` (after normalizing for different denominators), the account holds a non-currency commodity and the posting needs a cost or price annotation:

- **Buy** (`split:action = "Buy"`): `N SYMBOL {price USD}` where `price = |value| / |quantity|`
- **Sell** (`split:action = "Sell"`): `−N SYMBOL {cost USD}` — cost is looked up from the matching lot
- **Currency transfer** (both value and quantity are in currency but differ): `N CCY1 @ rate CCY2`

### Amount interpolation

GnuCash guarantees all transactions balance (sum of `split:value` = 0 in `trn:currency`). Beancount allows eliding one posting's amount; use this only if it simplifies capital-gains handling (leave the Income leg implicit).

### Example — simple cash transaction

```xml
<gnc:transaction version="2.0.0">
  <trn:currency><cmdty:id>USD</cmdty:id></trn:currency>
  <trn:date-posted><ts:date>2025-01-02 10:59:00 +0000</ts:date></trn:date-posted>
  <trn:description>Park Slope Food Coop</trn:description>
  <trn:splits>
    <trn:split>
      <split:value>13425/100</split:value>
      <split:quantity>13425/100</split:quantity>
      <split:account type="guid"><!-- Expenses:Food:Groceries --></split:account>
    </trn:split>
    <trn:split>
      <split:value>-13425/100</split:value>
      <split:quantity>-13425/100</split:quantity>
      <split:account type="guid"><!-- Assets:Chase:Checking --></split:account>
    </trn:split>
  </trn:splits>
</gnc:transaction>
```

```beancount
2025-01-02 * "Park Slope Food Coop"
  Expenses:Food:Groceries    134.25 USD
  Assets:Chase:Checking     -134.25 USD
```

### Example — security sale (value ≠ quantity)

```xml
<trn:split>
  <split:action>Sell</split:action>
  <split:value>-359195/100</split:value>      <!-- USD proceeds -->
  <split:quantity>-35919500/10000</split:quantity>  <!-- shares -->
  <split:account type="guid"><!-- Assets:US:Vanguard:VBMPX --></split:account>
  <split:lot type="guid">cb0b...</split:lot>
</trn:split>
<trn:split>
  <split:value>359195/100</split:value>
  <split:quantity>359195/100</split:quantity>
  <split:account type="guid"><!-- Assets:Chase:Checking --></split:account>
</trn:split>
```

```beancount
2025-01-01 * "Vanguard Sell"
  Assets:US:Vanguard:VBMPX    -3591.95 VBMPX {cost USD}  ; lot resolved from gnc:lot
  Assets:Chase:Checking     3591.95 USD
  Income:Capital-Gains                                 ; elided — auto-calculated
```

---

## `gnc:lot` → cost lot annotation

**Namespaces used:** `lot:`

Lots are stored as children of `<act:lots>` inside a `<gnc:account>`. They record investment cost-basis groupings. Splits reference lots via `<split:lot type="guid">`.

### Field mapping

| GnuCash field | Notes | Beancount target |
|---|---|---|
| `lot:id` (GUID) | Internal key — referenced by `split:lot` | Used during conversion to look up lot metadata; not emitted |
| `lot:slots` → `title` | Human label (`"Lot 0"`, …) | Lot label string in `{cost, "label"}` |
| `lot:slots` → `notes` | Free text | `lot-note:` metadata on the opening posting, or dropped |

The lot's **cost per unit** is not stored in the lot itself — it is derived from the `split:value / split:quantity` ratio of the first (opening) split that references that lot's GUID.

### Beancount lot annotation

```beancount
; Opening buy — establishes lot
2017-03-28 * "Buy"
  Assets:Vanguard:SO    110.00 SO {22.7309 USD, 2017-03-28, "Lot 0"}
  Assets:Chase:Checking  -2500.40 USD
```

---

## Slot system → metadata

**Namespace:** `slot:`

Slots are GnuCash's general-purpose key-value store, attached to books, accounts, transactions, commodities, and lots. They map to Beancount metadata lines (`key: value`), placed indented under the relevant directive.

### Type mapping

| `slot:value type` | GnuCash value | Beancount metadata value |
|---|---|---|
| `string` | UTF-8 text | Quoted string: `"text"` |
| `integer` | 64-bit int | Bare number: `42` |
| `double` | IEEE 754 float | Decimal number: `3.14` |
| `guid` | Hex GUID string | Quoted string (or drop if internal reference) |
| `gdate` → `<gdate>` | `YYYY-MM-DD` | Date literal: `2025-01-02` |
| `frame` | Nested slot map | Flatten with dotted keys (`parent.child: value`) or drop |

### Commonly mapped slots

| Slot key | Attached to | Beancount handling |
|---|---|---|
| `notes` | account, transaction | `note:` metadata or `note` directive |
| `placeholder` | account | Open the account normally; Beancount has no placeholder concept |
| `equity-type: "opening-balance"` | account | Name the account `Equity:Opening-Balances` by convention |
| `date-posted` (gdate) | transaction | Use as the canonical transaction date (drop timestamp from `trn:date-posted`) |
| `reconcile-info` | account | Drop |
| `import-map-bayes` | account/split | Drop |
| `balance-limit` | account | Drop |
| `color`, `tab-color` | account | Drop |
| `user_symbol` | commodity | `ticker:` metadata |
| `title` | lot | Lot label in `{..., "label"}` |

---

## `book:slots` → `option` directives and file header

**Namespace:** `book:`

The book-level slots hold GnuCash application settings. Most have no Beancount equivalent and are dropped. The relevant ones:

| GnuCash slot | Beancount equivalent |
|---|---|
| `options/Accounts/Use Trading Accounts` | If `"t"`: enable `beancount.plugins.auto_accounts` or trading account conventions |
| `options/Business/Company Name` | `option "title" "Company Name"` |
| `options/Business/Fancy Date Format` | Drop (Beancount always uses ISO 8601) |
| `features/*` | Drop (GnuCash-internal compatibility flags) |
| `counters/*` | Drop |
| `counter_formats/*` | Drop |

---

## Entities with no Beancount equivalent

The following GnuCash namespaces cover its business-accounting module. Plain Beancount has no matching constructs. They should be either dropped or converted to `note` directives or `custom` directives if preservation is needed.

| GnuCash namespace | Entity | Suggested handling |
|---|---|---|
| `cust:` | Customers | Drop or `custom "gnc-customer" ...` |
| `vendor:` | Vendors | Drop or `custom "gnc-vendor" ...` |
| `employee:` | Employees | Drop |
| `invoice:` | Invoices | Drop or `note` on receivable/payable account |
| `entry:` | Invoice line items | Drop |
| `order:` | Purchase orders | Drop |
| `job:` | Client jobs | Drop |
| `billterm:` | Billing terms | Drop |
| `taxtable:` / `tte:` | Tax tables | Drop |
| `sx:` | Scheduled transactions | Drop or `custom "scheduled" ...` |
| `bgt:` | Budgets | Drop or `custom "budget" ...` |
| `recurrence:` | Recurrence rules (for `sx:`) | Drop |
| `addr:` | Postal address | Drop |
| `owner:` | Customer/vendor owner reference | Drop |
| `fs:` | Financial statements config | Drop |

---

## Conversion summary

```
gnc-v2 document
└── gnc:book
    ├── gnc:commodity  →  commodity directive (one per non-currency instrument)
    ├── gnc:pricedb
    │   └── price      →  price directive (one per price entry)
    ├── gnc:account    →  open directive (one per account, date = earliest transaction)
    │   └── act:lots
    │       └── gnc:lot  →  cost lot metadata (resolved onto postings)
    └── gnc:transaction →  * transaction (one per transaction)
        └── trn:split   →  posting (one per split)
```
