from gnubeans.model import Book, Commodity

_COMMODITY_DATE = '1900-01-01'


def _check_collisions(book: Book, commodity_symbols: dict[str, str] | None) -> None:
    from collections import Counter
    from gnubeans.planner import proposed_commodity_symbols
    symbols = commodity_symbols if commodity_symbols is not None \
        else proposed_commodity_symbols(book)
    counts = Counter(symbols.values())
    colliding = [sym for sym, n in counts.items() if n > 1]
    if colliding:
        raise ValueError(
            f'collision: multiple commodities share the Beancount symbol(s) '
            f'{colliding}. Assign distinct symbols in the plan before rendering.'
        )


def render(book: Book, commodity_symbols: dict[str, str] | None = None) -> str:
    """
    Render a Book to beancount text.

    commodity_symbols maps original_cmdty_id -> confirmed_beancount_currency.
    When None, opinionated defaults are used (user_symbol if present, else
    sanitized cmdty:id).
    """
    _check_collisions(book, commodity_symbols)
    parts = [f'option "title" "{book.title}"\n']
    for commodity in book.commodities:
        parts.append('\n' + _render_commodity(commodity, commodity_symbols))
    return ''.join(parts)


def _render_commodity(c: Commodity, commodity_symbols: dict[str, str] | None) -> str:
    original = c.gnc_id if c.gnc_id else c.id
    if commodity_symbols is not None and original in commodity_symbols:
        currency = commodity_symbols[original]
    else:
        currency = c.user_symbol if c.user_symbol else c.id

    lines = [f'{_COMMODITY_DATE} commodity {currency}\n']
    if c.name:
        lines.append(f'  name: "{c.name}"\n')
    if c.space:
        lines.append(f'  gnc_namespace: "{c.space}"\n')
    if currency != original:
        lines.append(f'  gnc_cmdty_id: "{original}"\n')
    return ''.join(lines)
