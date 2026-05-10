from gnubeans.model import Book


def prompt_commodity_symbols(book: Book) -> dict[str, str]:
    """
    Present the commodity symbol batch-decision table and return confirmed symbols.

    Returns {original_cmdty_id: confirmed_beancount_currency}.
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
        return confirmed

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
            ).ask()
            if new_val and new_val.strip():
                confirmed[row['original']] = new_val.strip().upper()

    return confirmed
