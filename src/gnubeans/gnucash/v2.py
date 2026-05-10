import re
import sys
import xml.etree.ElementTree as ET

from gnubeans.model import Book, Commodity

_GNC   = 'http://www.gnucash.org/XML/gnc'
_BOOK  = 'http://www.gnucash.org/XML/book'
_CMDTY = 'http://www.gnucash.org/XML/cmdty'
_SLOT  = 'http://www.gnucash.org/XML/slot'

_CURRENCY_SPACES = {'CURRENCY', 'ISO4217'}
_TEMPLATE_SPACE  = 'template'

# Characters valid in non-first, non-last positions per beancount spec
_INVALID_CHARS = re.compile(r"[^A-Z0-9'._-]")
# Punctuation characters that are invalid in first or last position
_EDGE_PUNCT = "-.'_"


def parse(xml: bytes, filename_stem: str) -> Book:
    root = ET.fromstring(xml)
    book_el = root.find(f'{{{_GNC}}}book')
    title = _company_name(book_el) or filename_stem
    commodities = _parse_commodities(book_el)
    return Book(title=title, commodities=commodities)


# --- commodities ------------------------------------------------------------

def _parse_commodities(book_el) -> list[Commodity]:
    result = []
    seen: dict[str, str] = {}  # beancount_id -> first original cmdty:id

    for el in book_el.findall(f'{{{_GNC}}}commodity'):
        space = _text(el, f'{{{_CMDTY}}}space')
        if space in _CURRENCY_SPACES or space == _TEMPLATE_SPACE:
            continue
        raw_id = _text(el, f'{{{_CMDTY}}}id')
        beancount_id, gnc_id = _sanitize_id(raw_id)

        if beancount_id in seen:
            print(
                f'WARNING: collision — "{seen[beancount_id]}" and "{raw_id}"'
                f' both produce the Beancount currency "{beancount_id}".'
                f' Assign distinct symbols in the plan.',
                file=sys.stderr,
            )

        seen.setdefault(beancount_id, raw_id)
        result.append(Commodity(
            space=space,
            id=beancount_id,
            name=_text(el, f'{{{_CMDTY}}}name'),
            user_symbol=_cmdty_user_symbol(el),
            gnc_id=gnc_id,
        ))

    # Tag all commodities whose beancount_id appears more than once
    colliding = {c.id for c in result
                 if sum(1 for x in result if x.id == c.id) > 1}
    for c in result:
        c.collision = c.id in colliding

    return result


def _sanitize_id(raw: str) -> tuple[str, str]:
    """Return (beancount_currency, original) where original is non-empty if sanitized."""
    # 1. Uppercase
    s = raw.upper()

    # 2. Replace characters outside [A-Z0-9'._-] with dashes
    s = _INVALID_CHARS.sub('-', s)

    # 3. Collapse consecutive dashes produced by replacement
    s = re.sub(r'-{2,}', '-', s)

    # 4. Strip leading/trailing punctuation (invalid at first/last position)
    s = s.strip(_EDGE_PUNCT)

    # 5. Guard against empty result
    if not s:
        s = 'C'

    # 6. First character must be a letter; prefix C if it is a digit
    if s[0].isdigit():
        s = 'C' + s

    # 7. Truncate to 24 characters
    s = s[:24]

    # 8. After truncation, last character must be [A-Z0-9]; strip if not
    s = s.rstrip(_EDGE_PUNCT)

    # 9. Final guard against empty result
    if not s:
        s = 'C'

    if s == raw:
        return raw, ''

    print(
        f'WARNING: commodity "{raw}" is not a valid Beancount symbol'
        f' — suggesting "{s}"',
        file=sys.stderr,
    )
    return s, raw


def _cmdty_user_symbol(commodity_el) -> str:
    slots_el = commodity_el.find(f'{{{_CMDTY}}}slots')
    if slots_el is None:
        return ''
    return _slot_string(slots_el, 'user_symbol')


# --- book slots -------------------------------------------------------------

def _company_name(book_el) -> str:
    slots_el = book_el.find(f'{{{_BOOK}}}slots')
    if slots_el is None:
        return ''
    frame = _slot_frame(slots_el, 'options')
    if frame is None:
        return ''
    frame = _slot_frame(frame, 'Business')
    if frame is None:
        return ''
    return _slot_string(frame, 'Company Name')


# --- slot helpers -----------------------------------------------------------

def _slot_frame(parent, key: str):
    for slot in parent.findall('slot'):
        k = slot.find(f'{{{_SLOT}}}key')
        v = slot.find(f'{{{_SLOT}}}value')
        if k is not None and k.text == key and v is not None and v.get('type') == 'frame':
            return v
    return None


def _slot_string(parent, key: str) -> str:
    for slot in parent.findall('slot'):
        k = slot.find(f'{{{_SLOT}}}key')
        v = slot.find(f'{{{_SLOT}}}value')
        if k is not None and k.text == key and v is not None and v.get('type') == 'string':
            return v.text or ''
    return ''


def _text(el, tag: str) -> str:
    child = el.find(tag)
    return child.text.strip() if child is not None and child.text else ''
