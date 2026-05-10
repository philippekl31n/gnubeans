from dataclasses import dataclass, field


@dataclass
class Commodity:
    space: str
    id: str              # Beancount currency (sanitized if cmdty:id was invalid)
    name: str = ''
    user_symbol: str = '' # from cmdty:slots/user_symbol; proposed default currency
    gnc_id: str = ''     # original cmdty:id when sanitization was applied


@dataclass
class Book:
    title: str
    commodities: list[Commodity] = field(default_factory=list)
