import anyio
import typer
from rich.console import Console
from typer import Context
from wheke import get_container

from ._service import get_sqlmodel_service

cli = typer.Typer(short_help="SQLModel commands")
console = Console()


@cli.command()
def create_db(ctx: Context) -> None:
    container = get_container(ctx)
    service = get_sqlmodel_service(container)

    console.print("Creating database...")

    anyio.run(service.create_db)


@cli.command()
def drop_db(ctx: Context) -> None:
    container = get_container(ctx)
    service = get_sqlmodel_service(container)

    console.print("Droping database...")

    anyio.run(service.drop_db)
