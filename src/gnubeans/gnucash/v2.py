import xml.etree.ElementTree as ET

from gnubeans.model import Book, Commodity

_GNC   = 'http://www.gnucash.org/XML/gnc'
_BOOK  = 'http://www.gnucash.org/XML/book'
_CMDTY = 'http://www.gnucash.org/XML/cmdty'
_SLOT  = 'http://www.gnucash.org/XML/slot'

_CURRENCY_SPACES = {'CURRENCY', 'ISO4217'}
_TEMPLATE_SPACE  = 'template'


def parse(xml: bytes, filename_stem: str) -> Book:
    root = ET.fromstring(xml)
    book_el = root.find(f'{{{_GNC}}}book')
    title = _company_name(book_el) or filename_stem
    commodities = _parse_commodities(book_el)
    return Book(title=title, commodities=commodities)


# --- commodities ------------------------------------------------------------

def _parse_commodities(book_el) -> list[Commodity]:
    result = []
    for el in book_el.findall(f'{{{_GNC}}}commodity'):
        space = _text(el, f'{{{_CMDTY}}}space')
        if space in _CURRENCY_SPACES or space == _TEMPLATE_SPACE:
            continue
        result.append(Commodity(
            space=space,
            id=_text(el, f'{{{_CMDTY}}}id'),
            name=_text(el, f'{{{_CMDTY}}}name'),
            ticker=_cmdty_user_symbol(el),
        ))
    return result


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
