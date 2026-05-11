#!/usr/bin/env python3
"""
Prototype: commodity batch-decision TUI using Textual.

Demonstrates the two-mode interaction defined in design-decisions.md:

  Row-selection mode  — Input has focus; ↑↓ scroll the DataTable viewport
                        one page; type a row number + Enter to fast-jump
                        and activate cell-edit mode.

  Cell-edit mode      — DataTable cursor is visible on the selected row;
                        Input shows the current value pre-filled; real-time
                        validation gives red error feedback on every keypress
                        and blocks Enter until the value is valid; ↑↓ move
                        to the adjacent row; Esc cancels and returns to
                        row-selection mode.

Run:  gnubeans-prototype
"""

from __future__ import annotations

import re
from collections import defaultdict

from rich.text import Text
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.validation import ValidationResult, Validator
from textual.widgets import DataTable, Footer, Input, Label

# ---------------------------------------------------------------------------
# Sample data — mirrors collision_demo.gnucash
# ---------------------------------------------------------------------------

COMMODITIES: list[dict] = [
    {"original": "AT&T",    "proposed": "AT-T",    "space": "NYSE",
     "name": "AT&T Inc"},
    {"original": "AT[T]",   "proposed": "AT-T",    "space": "NYSE",
     "name": "AT Capital Trust"},
    {"original": "VBMPX",   "proposed": "VBMPX",   "space": "Vanguard",
     "name": "Vanguard Total Bond Market Index Fund"},
    {"original": "1003057", "proposed": "C1003057", "space": "Vanguard",
     "name": "Vanguard Target Enrollment 2038"},
]

# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

_VALID = re.compile(r"^[A-Z][A-Z0-9'._-]{0,22}[A-Z0-9]$|^[A-Z]$")


class CurrencyValidator(Validator):
    def validate(self, value: str) -> ValidationResult:
        v = value.strip().upper()
        if not v:
            return self.failure("Symbol cannot be empty")
        if _VALID.match(v):
            return self.success()
        return self.failure(
            f'"{v}" is not a valid Beancount symbol '
            f"(letter start · letter/digit end · [A-Z0-9'._-] · max 24 chars)"
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _colliding_symbols(confirmed: dict[str, str]) -> set[str]:
    inv: dict[str, list[str]] = defaultdict(list)
    for orig, sym in confirmed.items():
        inv[sym].append(orig)
    return {sym for sym, origs in inv.items() if len(origs) > 1}


_HINT = {
    "select": "↑↓ pages · row number + Enter to edit · a accept all",
    "edit":   "Enter confirm · Esc cancel · ↑↓ move row",
}

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

class CommodityBatchDecision(App):

    CSS = """
    Screen {
        layout: vertical;
    }

    DataTable {
        height: 1fr;
    }

    #status {
        height: 1;
        padding: 0 1;
        color: $text-muted;
        background: $panel;
    }

    #input-row {
        height: 5;
        border-top: solid $accent;
        padding: 0 1;
    }

    #hint {
        height: 1;
        color: $text-muted;
        padding: 0 0 0 1;
    }

    Input {
        width: 1fr;
        margin-top: 1;
    }
    """

    BINDINGS = [
        Binding("up",       "navigate_up",   show=False, priority=True),
        Binding("down",     "navigate_down", show=False, priority=True),
        Binding("pageup",   "page_up",       show=False),
        Binding("pagedown", "page_down",     show=False),
        Binding("escape",   "do_escape",     show=False, priority=True),
        Binding("a",        "accept_all",    "Accept all"),
    ]

    def __init__(self, commodities: list[dict]) -> None:
        super().__init__()
        self._data = commodities
        self._confirmed: dict[str, str] = {
            c["original"]: c["proposed"] for c in commodities
        }
        self._mode = "select"
        self._edit_original: str | None = None

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------

    def compose(self) -> ComposeResult:
        yield DataTable(cursor_type="row", show_cursor=False)
        yield Label("", id="status")
        with Horizontal(id="input-row"):
            yield Label(_HINT["select"], id="hint")
            yield Input(placeholder="row number…", id="the-input")
        yield Footer()

    def on_mount(self) -> None:
        self._rebuild_table()
        self._refresh_status()
        self.query_one("#the-input", Input).focus()

    # ------------------------------------------------------------------
    # Table
    # ------------------------------------------------------------------

    def _rebuild_table(self) -> None:
        table = self.query_one(DataTable)
        colliding = _colliding_symbols(self._confirmed)
        table.clear(columns=True)
        table.add_columns("#", "cmdty:id", "name", "proposed symbol", "")
        for i, c in enumerate(self._data):
            sym = self._confirmed[c["original"]]
            clash = sym in colliding
            name = c["name"][:34] + ("…" if len(c["name"]) > 34 else "")
            table.add_row(
                str(i + 1),
                c["original"],
                name,
                Text(sym, style="bold red" if clash else "bold green"),
                Text("COLLISION", style="bold red") if clash else Text("✓", style="green"),
                key=c["original"],
            )

    def _refresh_status(self) -> None:
        unresolved = len(_colliding_symbols(self._confirmed))
        total = len(self._data)
        suffix = f" · {unresolved} unresolved" if unresolved else " · all resolved ✓"
        mode_tag = "editing" if self._mode == "edit" else "browsing"
        self.query_one("#status", Label).update(
            f"{total} commodities · {mode_tag}{suffix}"
        )

    # ------------------------------------------------------------------
    # Mode transitions
    # ------------------------------------------------------------------

    def _enter_edit(self, row_idx: int) -> None:
        c = self._data[row_idx]
        self._edit_original = c["original"]
        self._mode = "edit"

        table = self.query_one(DataTable)
        table.show_cursor = True
        table.move_cursor(row=row_idx)

        inp = self.query_one("#the-input", Input)
        inp.validators = [CurrencyValidator()]
        inp.value = self._confirmed[c["original"]]
        inp.placeholder = ""

        self.query_one("#hint", Label).update(_HINT["edit"])
        self._refresh_status()
        inp.focus()

    def _enter_select(self) -> None:
        self._mode = "select"
        self._edit_original = None

        table = self.query_one(DataTable)
        table.show_cursor = False

        inp = self.query_one("#the-input", Input)
        inp.validators = []
        inp.value = ""
        inp.placeholder = "row number…"

        self.query_one("#hint", Label).update(_HINT["select"])
        self._refresh_status()
        inp.focus()

    # ------------------------------------------------------------------
    # Input submitted
    # ------------------------------------------------------------------

    def on_input_submitted(self, event: Input.Submitted) -> None:
        value = event.value.strip()

        if self._mode == "select":
            if not value:
                self.action_accept_all()
                return
            if value.isdigit():
                idx = int(value) - 1
                if 0 <= idx < len(self._data):
                    self._enter_edit(idx)
                    return
            self.bell()

        elif self._mode == "edit":
            v = value.upper()
            if _VALID.match(v):
                self._confirmed[self._edit_original] = v
                self._rebuild_table()
                self._enter_select()

    # ------------------------------------------------------------------
    # Key actions
    # ------------------------------------------------------------------

    def action_navigate_up(self) -> None:
        table = self.query_one(DataTable)
        if self._mode == "select":
            table.scroll_page_up()
        else:
            new_row = max(0, table.cursor_row - 1)
            self._enter_edit(new_row)

    def action_navigate_down(self) -> None:
        table = self.query_one(DataTable)
        if self._mode == "select":
            table.scroll_page_down()
        else:
            new_row = min(len(self._data) - 1, table.cursor_row + 1)
            self._enter_edit(new_row)

    def action_page_up(self) -> None:
        self.query_one(DataTable).scroll_page_up()

    def action_page_down(self) -> None:
        self.query_one(DataTable).scroll_page_down()

    def action_do_escape(self) -> None:
        if self._mode == "edit":
            self._enter_select()
        else:
            self.exit(None)

    def action_accept_all(self) -> None:
        if _colliding_symbols(self._confirmed):
            self.bell()
            return
        self.exit(self._confirmed)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    from rich.console import Console
    from rich.table import Table as RichTable

    app = CommodityBatchDecision(COMMODITIES)
    result = app.run(inline=True)
    console = Console()

    if result:
        console.print()
        t = RichTable(title="Confirmed Beancount symbols")
        t.add_column("GnuCash cmdty:id")
        t.add_column("Beancount symbol")
        for c in COMMODITIES:
            orig = c["original"]
            sym = result[orig]
            note = f"  [dim](was {c['proposed']})[/dim]" if sym != c["proposed"] else ""
            t.add_row(orig, f"[bold green]{sym}[/bold green]{note}")
        console.print(t)
    else:
        console.print("\n[yellow]Cancelled.[/yellow]")


if __name__ == "__main__":
    main()
