#!/usr/bin/env python3
"""
Prototype: commodity batch-decision TUI.

Demonstrates the row-at-a-time navigation model:
  - Rich table re-renders after each edit showing live state
  - questionary text prompt with real-time validation (red errors on keypress)
  - Collision indicators in table; cannot accept while collisions remain
  - Empty input at the cell-edit prompt cancels the edit

Run from the project root:
    python scripts/tui_prototype.py

Note: Rich Live + questionary cannot share the terminal simultaneously, so the
table is re-printed above the prompt on each iteration rather than updating
in-place. True in-place cell editing would require Textual's DataTable widget.
"""

import re
from collections import defaultdict

from rich.console import Console
from rich.table import Table
from rich.text import Text
import questionary

# ---------------------------------------------------------------------------
# Sample commodity data — mirrors what parse() produces for collision_demo.gnucash
# ---------------------------------------------------------------------------

COMMODITIES = [
    {"original": "AT&T",    "proposed": "AT-T",    "space": "NYSE",     "name": "AT&T Inc"},
    {"original": "AT[T]",   "proposed": "AT-T",    "space": "NYSE",     "name": "AT Capital Trust"},
    {"original": "VBMPX",   "proposed": "VBMPX",   "space": "Vanguard", "name": "Vanguard Total Bond Market Index Fund"},
    {"original": "1003057", "proposed": "C1003057", "space": "Vanguard", "name": "Vanguard Target Enrollment 2038"},
]

# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

_VALID_CURRENCY = re.compile(r"^[A-Z][A-Z0-9'._-]{0,22}[A-Z0-9]$|^[A-Z]$")


def _validate(value: str) -> bool | str:
    v = value.strip().upper()
    if not v:
        return "Symbol cannot be empty"
    if _VALID_CURRENCY.match(v):
        return True
    return (
        f'"{v}" is not a valid Beancount symbol — '
        f'must start with a letter, end with letter/digit, '
        f'contain only [A-Z0-9\'._-], max 24 chars'
    )


# ---------------------------------------------------------------------------
# Collision detection
# ---------------------------------------------------------------------------

def _collisions(confirmed: dict[str, str]) -> dict[str, list[str]]:
    inv: dict[str, list[str]] = defaultdict(list)
    for orig, sym in confirmed.items():
        inv[sym].append(orig)
    return {sym: origs for sym, origs in inv.items() if len(origs) > 1}


# ---------------------------------------------------------------------------
# Table rendering
# ---------------------------------------------------------------------------

def _render_table(commodities: list[dict], confirmed: dict[str, str],
                  collision_syms: set[str]) -> Table:
    table = Table(show_header=True, header_style="bold", box=None, padding=(0, 1))
    table.add_column("#",           style="dim",   width=4,  no_wrap=True)
    table.add_column("cmdty:id",    style="",      min_width=12)
    table.add_column("name",        style="dim",   min_width=20)
    table.add_column("symbol",      style="bold",  min_width=14)
    table.add_column("status",      style="",      min_width=10)

    for i, c in enumerate(commodities, 1):
        sym = confirmed[c["original"]]
        if sym in collision_syms:
            sym_text  = Text(sym, style="bold red")
            status    = Text("COLLISION", style="bold red")
        else:
            sym_text  = Text(sym, style="bold green")
            status    = Text("✓", style="green")
        table.add_row(str(i), c["original"], c["name"], sym_text, status)

    return table


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

def main() -> None:
    console = Console()
    confirmed = {c["original"]: c["proposed"] for c in COMMODITIES}

    while True:
        coll   = _collisions(confirmed)
        c_syms = set(coll.keys())

        console.rule("[bold]Commodity symbols[/bold]")
        console.print(_render_table(COMMODITIES, confirmed, c_syms))

        if coll:
            for sym, origs in coll.items():
                console.print(
                    f"  [red]COLLISION[/red] [bold]{sym}[/bold] "
                    f"is shared by: {', '.join(repr(o) for o in origs)}"
                )
        console.print()

        # --- row selection ---------------------------------------------------
        answer = questionary.text(
            "Row number to edit, or Enter to accept all:",
            default="",
        ).ask()

        if answer is None:               # Ctrl+C
            console.print("\n[red]Cancelled.[/red]")
            return

        answer = answer.strip()

        if not answer:
            if coll:
                console.print("[red]Cannot accept — resolve collisions first.[/red]\n")
                continue
            break                        # done

        if not answer.isdigit() or not (1 <= int(answer) <= len(COMMODITIES)):
            console.print(f"[red]Enter a number between 1 and {len(COMMODITIES)}.[/red]\n")
            continue

        # --- cell edit -------------------------------------------------------
        idx      = int(answer) - 1
        c        = COMMODITIES[idx]
        original = c["original"]
        current  = confirmed[original]

        console.print(
            f"  Editing row {idx + 1}: [dim]{original}[/dim] "
            f"([italic]leave blank to cancel[/italic])"
        )

        new_val = questionary.text(
            f"  Symbol:",
            default=current,
            validate=_validate,
        ).ask()

        if new_val is None:              # Ctrl+C during edit
            console.print("[red]Cancelled.[/red]\n")
            return

        new_val = new_val.strip().upper()
        if new_val and new_val != current:
            confirmed[original] = new_val
        console.print()

    # --- summary -------------------------------------------------------------
    console.rule("[bold green]Accepted[/bold green]")
    for c in COMMODITIES:
        orig = c["original"]
        sym  = confirmed[orig]
        marker = "" if orig == sym else f"[dim](was {c['proposed']})[/dim]"
        console.print(f"  [bold]{orig}[/bold] → [bold green]{sym}[/bold green] {marker}")


if __name__ == "__main__":
    main()
