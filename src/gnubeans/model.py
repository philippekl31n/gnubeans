from dataclasses import dataclass, field


@dataclass
class Commodity:
    space: str
    id: str
    name: str = ''
    ticker: str = ''  # from cmdty:slots/user_symbol


@dataclass
class Book:
    title: str
    commodities: list[Commodity] = field(default_factory=list)
