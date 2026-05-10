"""Shared test helpers for building minimal gnc-v2 XML fixtures."""


_BOOK_OPEN = """\
<?xml version="1.0" encoding="utf-8" ?>
<gnc-v2
     xmlns:gnc="http://www.gnucash.org/XML/gnc"
     xmlns:book="http://www.gnucash.org/XML/book"
     xmlns:cd="http://www.gnucash.org/XML/cd"
     xmlns:cmdty="http://www.gnucash.org/XML/cmdty"
     xmlns:slot="http://www.gnucash.org/XML/slot">
<gnc:count-data cd:type="book">1</gnc:count-data>
<gnc:book version="2.0.0">
<book:id type="guid">4ad968fd0ff94c4591d32146e7c5d99f</book:id>
"""

_BOOK_CLOSE = """\
</gnc:book>
</gnc-v2>
"""


def commodity_xml(
    space: str,
    cmdty_id: str,
    name: str = "",
    user_symbol: str = "",
    quote_source: str = "",
) -> bytes:
    """Return minimal gnc-v2 XML containing exactly one commodity."""
    lines = [
        _BOOK_OPEN,
        '<gnc:commodity version="2.0.0">\n',
        f'  <cmdty:space>{space}</cmdty:space>\n',
        f'  <cmdty:id>{cmdty_id}</cmdty:id>\n',
    ]
    if name:
        lines.append(f'  <cmdty:name>{name}</cmdty:name>\n')
    lines.append('  <cmdty:fraction>10000</cmdty:fraction>\n')
    if quote_source:
        lines.append('  <cmdty:get_quotes/>\n')
        lines.append(f'  <cmdty:quote_source>{quote_source}</cmdty:quote_source>\n')
        lines.append('  <cmdty:quote_tz/>\n')
    if user_symbol:
        lines.append('  <cmdty:slots>\n')
        lines.append('    <slot>\n')
        lines.append('      <slot:key>user_symbol</slot:key>\n')
        lines.append(f'      <slot:value type="string">{user_symbol}</slot:value>\n')
        lines.append('    </slot>\n')
        lines.append('  </cmdty:slots>\n')
    lines.append('</gnc:commodity>\n')
    lines.append(_BOOK_CLOSE)
    return ''.join(lines).encode()
