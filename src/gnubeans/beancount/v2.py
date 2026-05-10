from gnubeans.model import Book, Commodity

_COMMODITY_DATE = '1900-01-01'


def render(book: Book) -> str:
    parts = [f'option "title" "{book.title}"\n']
    for commodity in book.commodities:
        parts.append('\n' + _render_commodity(commodity))
    return ''.join(parts)


def _render_commodity(c: Commodity) -> str:
    lines = [f'{_COMMODITY_DATE} commodity {c.id}\n']
    if c.name:
        lines.append(f'  name: "{c.name}"\n')
    lines.append(f'  gnc_namespace: "{c.space}"\n')
    return ''.join(lines)
