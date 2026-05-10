from gnubeans.model import Book

_COMMODITY_HEADER = """\
# commodities: Maps each GnuCash commodity to its Beancount output.
#
# Currency: the Beancount commodity identifier (beancount's term for any
#   commodity, not only monetary currencies). Becomes the token after the
#   date on the output commodity directive:  YYYY-MM-DD commodity <Currency>
#   GnuCash user_symbol is proposed as the default Currency when present;
#   cmdty:id otherwise. If cmdty:id is not a valid Beancount currency (e.g.
#   starts with a digit) it is sanitized (e.g. "1003057" -> "C1003057").
#
# gnc_cmdty_id: emitted automatically as beancount metadata when user_symbol
#   is present in the GnuCash data (user_symbol becomes the Currency and
#   cmdty:id is preserved) or when sanitization was applied. Commented
#   (but available to uncomment) when cmdty:id equals the Currency.
#
# gnc_user_symbol, gnc_cmdty_xcode: commented by default; uncomment to emit
#   as beancount metadata. Useful for preserving GnuCash source context if
#   you edit the Currency (e.g. GLD -> GOLD).
#
# export: (optional -- uncomment to include in beancount output)
#   Used by bean-report export_portfolio to generate OFX portfolio output.
#   Format: "EXCHANGE_CODE:TICKER"
#     EXCHANGE_CODE has no source in GnuCash data; must be supplied by the
#     user (e.g. MUTF for US mutual funds, NYSEARCA for NYSE Arca ETFs).
#     TICKER is GnuCash cmdty:id (see gnc_cmdty_id above).
#   MUTF prefix -> OFX BUYMF (mutual fund); all others -> OFX BUYSTOCK.
#   Special values:
#     "CASH"                  - convert holding to cash-equivalent at export
#     "IGNORE"                - exclude commodity from portfolio export
#     "MUTF:SYM (MONEY:USD)"  - money-market fund; treated as cash-equivalent
#   <EXCHANGE_CODE> is a placeholder; fill in or leave commented to omit.
#   Reference: bean-report <file.beancount> export_portfolio [--debug]
"""


def proposed_commodity_symbols(book: Book) -> dict[str, str]:
    """Return opinionated default {original_cmdty_id: proposed_beancount_currency}."""
    result = {}
    for c in book.commodities:
        original = c.gnc_id if c.gnc_id else c.id
        proposed = c.user_symbol if c.user_symbol else c.id
        result[original] = proposed
    return result


def commodity_plan_yaml(book: Book, confirmed: dict[str, str]) -> str:
    """Generate the commodities section of the plan YAML as a string."""
    lines = [_COMMODITY_HEADER, 'commodities:\n']

    for c in book.commodities:
        original = c.gnc_id if c.gnc_id else c.id
        currency = confirmed.get(original, c.user_symbol if c.user_symbol else c.id)

        if c.collision:
            lines.append(
                f'  {currency}:  # COLLISION — this symbol is shared by multiple'
                f' GnuCash commodities. Assign a unique symbol before applying.\n'
            )
        else:
            lines.append(f'  {currency}:\n')

        if original != currency:
            lines.append(f'    gnc_cmdty_id: "{original}"\n')
        else:
            lines.append(f'    # gnc_cmdty_id: "{original}"\n')

        if c.user_symbol:
            lines.append(f'    # gnc_user_symbol: "{c.user_symbol}"\n')

        lines.append(f'    # export: "<EXCHANGE_CODE>:{original}"\n')

    return ''.join(lines)
