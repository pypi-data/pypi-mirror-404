import asyncio
import json
from typing import Optional

import typer

from inceptum import config

from .database import database
from .read import read as read_object
from .search import search as search_objects

app = typer.Typer(add_completion=False)


def _print(obj, *, as_json: bool) -> None:
    if as_json:
        typer.echo(json.dumps(obj, ensure_ascii=False))
    else:
        typer.echo(obj)


def _apply_attachments(attach: list[str]) -> None:
    """
    Register one or more attachment aliases (optionally with explicit paths).

    Accepted forms:
      - ALIAS            -> attaches {base_dir}/{ALIAS}.db
      - ALIAS=PATH       -> attaches PATH (relative paths become relative to base_dir)
    """
    for item in attach:
        item = item.strip()
        if not item:
            continue

        if "=" in item:
            alias, path = item.split("=", 1)
            alias = alias.strip()
            path = path.strip()
            if not alias:
                raise typer.BadParameter(f"Invalid --attach value {item!r}: missing alias before '='.")
            if not path:
                raise typer.BadParameter(f"Invalid --attach value {item!r}: missing path after '='.")
            database.attach(alias, path)
        else:
            database.attach(item)


@app.command("config")
def config_cmd() -> None:
    print(config("ostryalis"))


@app.command("read")
def read_cmd(
    a: str = typer.Argument(
        ...,
        help="Either a UUID (when --title is omitted) or a type title (when --title is provided).",
    ),
    title: Optional[str] = typer.Option(
        None,
        "--title",
        "-t",
        help="Object title; if provided, the first argument is treated as the type title.",
    ),
    attach: list[str] = typer.Option(
        [],
        "--attach",
        "-a",
        help="Attach an extra database. Repeatable. Use ALIAS or ALIAS=PATH.",
    ),
    json_output: bool = typer.Option(
        True,
        "--json/--no-json",
        help="Output as JSON.",
    ),
) -> None:
    async def _run():
        try:
            _apply_attachments(attach)
            row = await read_object(a, title=title, session=None)
            if row is None:
                raise typer.Exit(code=1)
            _print(row if json_output else json.dumps(row, ensure_ascii=False, indent=2), as_json=False)
        finally:
            await database.dispose()

    asyncio.run(_run())


@app.command("search")
def search_cmd(
    attach: list[str] = typer.Option(
        [],
        "--attach",
        "-a",
        help="Attach an extra database. Repeatable. Use ALIAS or ALIAS=PATH.",
    ),
    json_lines: bool = typer.Option(
        True,
        "--jsonl/--no-jsonl",
        help="Output as JSON Lines (one JSON object per line).",
    ),
) -> None:
    async def _run():
        try:
            _apply_attachments(attach)
            async for row in search_objects(q=None, session=None):
                if json_lines:
                    typer.echo(json.dumps(row, ensure_ascii=False))
                else:
                    typer.echo(json.dumps(row, ensure_ascii=False, indent=2))
        finally:
            await database.dispose()

    asyncio.run(_run())
