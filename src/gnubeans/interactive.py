import re
from collections import defaultdict

from gnubeans.model import Book

# Beancount currency spec: starts with [A-Z], ends with [A-Z0-9],
# middle chars in [A-Z0-9'._-], total length 1–24.
_VALID_CURRENCY = re.compile(r"^[A-Z][A-Z0-9'._-]{0,22}[A-Z0-9]$|^[A-Z]$")


def find_symbol_collisions(confirmed: dict[str, str]) -> dict[str, list[str]]:
    """
    Return {currency: [original_id, ...]} for every currency that appears
    more than once in the confirmed mapping — i.e. collisions that must be
    resolved before rendering.
    """
    inverted: dict[str, list[str]] = defaultdict(list)
    for original, currency in confirmed.items():
        inverted[currency].append(original)
    return {sym: ids for sym, ids in inverted.items() if len(ids) > 1}


def is_valid_beancount_currency(value: str) -> bool:
    """Return True if value is a valid Beancount currency symbol (checked as-is)."""
    return bool(_VALID_CURRENCY.match(value.strip()))


def _validate_currency(value: str) -> bool | str:
    """questionary validate callback: return True or a human-readable error.

    Normalises to uppercase before checking so the user may type in any case.
    """
    v = value.strip().upper()
    if not v:
        return "Symbol cannot be empty"
    if is_valid_beancount_currency(v):
        return True
    return (
        f'"{v}" is not a valid Beancount symbol — '
        f'must start with a letter, end with a letter or digit, '
        f'contain only [A-Z0-9\'._-], and be at most 24 characters'
    )


def prompt_commodity_symbols(book: Book) -> dict[str, str]:
    """
    Present the commodity symbol batch-decision table and return confirmed symbols.

    Returns {original_cmdty_id: confirmed_beancount_currency}.
    Invalid replacements are rejected by the prompt and re-requested.
    """
    from rich.console import Console
    from rich.table import Table
    import questionary

    console = Console(stderr=True)

    rows = []
    for c in book.commodities:
        original = c.gnc_id if c.gnc_id else c.id
        proposed = c.user_symbol if c.user_symbol else c.id
        rows.append({'original': original, 'user_symbol': c.user_symbol, 'proposed': proposed})

    if not rows:
        return {}

    table = Table(show_header=True, header_style="bold")
    table.add_column("#", style="dim", width=4)
    table.add_column("cmdty:id")
    table.add_column("user_symbol")
    table.add_column("Proposed symbol")

    for i, row in enumerate(rows, 1):
        table.add_row(
            str(i),
            row['original'],
            row['user_symbol'] or '(not set)',
            row['proposed'],
        )

    console.print(table)

    confirmed = {row['original']: row['proposed'] for row in rows}

    answer = questionary.text(
        "Accept all, or enter row numbers to edit (e.g. 1,3):",
        default="",
    ).ask()

    if not answer or not answer.strip():
        pass
    else:
        for part in answer.split(','):
            part = part.strip()
            if not part.isdigit():
                continue
            idx = int(part) - 1
            if 0 <= idx < len(rows):
                row = rows[idx]
                new_val = questionary.text(
                    f'  Row {idx + 1} ({row["original"]}) — Beancount symbol:',
                    default=row['proposed'],
                    validate=_validate_currency,
                ).ask()
                if new_val and new_val.strip():
                    confirmed[row['original']] = new_val.strip().upper()

    # Re-prompt until all collisions are resolved
    while True:
        collisions = find_symbol_collisions(confirmed)
        if not collisions:
            break
        console.print(
            '\n[bold yellow]Unresolved collisions — assign a unique symbol for each:[/]'
        )
        for symbol, originals in collisions.items():
            console.print(f'  [red]{symbol}[/] is shared by: {originals}')
            for original in originals:
                new_val = questionary.text(
                    f'  New symbol for "{original}":',
                    default=confirmed[original],
                    validate=_validate_currency,
                ).ask()
                if new_val and new_val.strip():
                    confirmed[original] = new_val.strip().upper()

    return confirmed
