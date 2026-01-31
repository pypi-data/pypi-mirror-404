"""Command-line interface for IdentityPlanKit."""

import os
from pathlib import Path
from typing import TYPE_CHECKING, Annotated

import typer

if TYPE_CHECKING:
    from alembic.config import Config
from rich.console import Console
from rich.table import Table

app = typer.Typer(
    name="ipk",
    help="IdentityPlanKit CLI - Manage database migrations and more",
    add_completion=False,
)

# Database commands
db_app = typer.Typer(
    name="db",
    help="Database migration commands",
)
app.add_typer(db_app)

console = Console()


def load_env_file(env_file: Path | None = None) -> None:
    """
    Load environment variables from .env file.

    Args:
        env_file: Path to .env file. If None, looks for .env in current directory.
    """
    try:
        from dotenv import load_dotenv  # noqa: PLC0415
    except ImportError:
        if env_file:
            console.print(
                "[yellow]Warning:[/yellow] python-dotenv not installed. "
                "Install it with: pip install python-dotenv",
                style="yellow",
            )
        return

    if env_file:
        if not env_file.exists():
            console.print(
                f"[red]Error:[/red] Environment file not found: {env_file}",
                style="red",
            )
            raise typer.Exit(1)
        load_dotenv(env_file, override=True)
        console.print(f"[cyan]Loaded environment from:[/cyan] {env_file}")
    else:
        # Try to load from .env in current directory
        default_env = Path(".env")
        if default_env.exists():
            load_dotenv(default_env)
            console.print(f"[cyan]Loaded environment from:[/cyan] {default_env}")


def get_alembic_config() -> "Config":
    """Get Alembic config from installed package."""
    from alembic.config import Config  # noqa: PLC0415

    # Find alembic.ini in the installed package
    import identity_plan_kit  # noqa: PLC0415

    package_dir = Path(identity_plan_kit.__file__).parent.parent.parent
    alembic_ini = package_dir / "alembic.ini"

    if not alembic_ini.exists():
        console.print(
            "[red]Error:[/red] alembic.ini not found. "
            "Make sure identity-plan-kit is properly installed.",
            style="red",
        )
        raise typer.Exit(1)

    config = Config(str(alembic_ini))

    # Set script location to installed package
    alembic_dir = package_dir / "alembic"
    config.set_main_option("script_location", str(alembic_dir))

    # Get database URL from environment or fail
    db_url = os.environ.get("IPK_DATABASE_URL")
    if not db_url:
        console.print(
            "[red]Error:[/red] IPK_DATABASE_URL environment variable not set.\n"
            "Example: export IPK_DATABASE_URL=postgresql+asyncpg://user:pass@localhost/db",
            style="red",
        )
        raise typer.Exit(1)

    # Convert async URL to sync for Alembic
    if "+asyncpg" in db_url:
        db_url = db_url.replace("+asyncpg", "")

    config.set_main_option("sqlalchemy.url", db_url)

    return config


@db_app.command("upgrade")
def db_upgrade(
    revision: str = typer.Argument("head", help="Revision to upgrade to (default: head)"),
    sql: bool = typer.Option(False, "--sql", help="Show SQL without executing"),
    env_file: Annotated[
        Path | None,
        typer.Option("--env-file", "-e", help="Path to .env file"),
    ] = None,
) -> None:
    """
    Upgrade database to a later version.

    Examples:
        ipk db upgrade            # Upgrade to latest
        ipk db upgrade head       # Upgrade to latest
        ipk db upgrade +1         # Upgrade by 1 revision
        ipk db upgrade 001_initial  # Upgrade to specific revision
        ipk db upgrade --env-file .env.production  # Use specific env file
    """
    from alembic import command  # noqa: PLC0415

    load_env_file(env_file)

    try:
        config = get_alembic_config()
        if sql:
            command.upgrade(config, revision, sql=True)
        else:
            console.print(f"[cyan]Upgrading database to:[/cyan] {revision}")
            command.upgrade(config, revision)
            console.print("[green]✓[/green] Database upgraded successfully")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}", style="red")
        raise typer.Exit(1) from None


@db_app.command("downgrade")
def db_downgrade(
    revision: str = typer.Argument("-1", help="Revision to downgrade to (default: -1)"),
    sql: bool = typer.Option(False, "--sql", help="Show SQL without executing"),
    env_file: Annotated[
        Path | None,
        typer.Option("--env-file", "-e", help="Path to .env file"),
    ] = None,
) -> None:
    """
    Downgrade database to a previous version.

    WARNING: This may result in data loss!

    Examples:
        ipk db downgrade -1       # Downgrade by 1 revision
        ipk db downgrade base     # Downgrade to empty database
        ipk db downgrade 001_initial  # Downgrade to specific revision
    """
    from alembic import command  # noqa: PLC0415

    load_env_file(env_file)

    if not typer.confirm(
        "⚠️  Downgrading may result in data loss. Continue?",
        default=False,
    ):
        console.print("[yellow]Cancelled[/yellow]")
        raise typer.Exit(0)

    try:
        config = get_alembic_config()
        if sql:
            command.downgrade(config, revision, sql=True)
        else:
            console.print(f"[cyan]Downgrading database to:[/cyan] {revision}")
            command.downgrade(config, revision)
            console.print("[green]✓[/green] Database downgraded successfully")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}", style="red")
        raise typer.Exit(1) from None


@db_app.command("current")
def db_current(
    env_file: Annotated[
        Path | None,
        typer.Option("--env-file", "-e", help="Path to .env file"),
    ] = None,
) -> None:
    """Show current database revision."""
    from alembic import command  # noqa: PLC0415

    load_env_file(env_file)

    try:
        config = get_alembic_config()
        command.current(config, verbose=True)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}", style="red")
        raise typer.Exit(1) from None


@db_app.command("history")
def db_history(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed history"),
    env_file: Annotated[
        Path | None,
        typer.Option("--env-file", "-e", help="Path to .env file"),
    ] = None,
) -> None:
    """Show migration history."""
    from alembic import command  # noqa: PLC0415

    load_env_file(env_file)

    try:
        config = get_alembic_config()
        command.history(config, verbose=verbose)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}", style="red")
        raise typer.Exit(1) from None


@db_app.command("heads")
def db_heads(
    env_file: Annotated[
        Path | None,
        typer.Option("--env-file", "-e", help="Path to .env file"),
    ] = None,
) -> None:
    """Show current available heads in the script directory."""
    from alembic import command  # noqa: PLC0415

    load_env_file(env_file)

    try:
        config = get_alembic_config()
        command.heads(config, verbose=True)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}", style="red")
        raise typer.Exit(1) from None


@db_app.command("stamp")
def db_stamp(
    revision: str = typer.Argument("head", help="Revision to stamp"),
    env_file: Annotated[
        Path | None,
        typer.Option("--env-file", "-e", help="Path to .env file"),
    ] = None,
) -> None:
    """
    'Stamp' the revision table with the given revision.

    This doesn't run migrations, just marks the database as being at a specific version.
    Useful when you've manually applied schema changes or are migrating from a non-Alembic setup.

    Examples:
        ipk db stamp head         # Mark as current head
        ipk db stamp 001_initial  # Mark as specific revision
    """
    from alembic import command  # noqa: PLC0415

    load_env_file(env_file)

    try:
        config = get_alembic_config()
        console.print(f"[cyan]Stamping database with revision:[/cyan] {revision}")
        command.stamp(config, revision)
        console.print("[green]✓[/green] Database stamped successfully")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}", style="red")
        raise typer.Exit(1) from None


@db_app.command("revision")
def db_revision(
    message: str = typer.Option(..., "--message", "-m", help="Revision message"),
    autogenerate: bool = typer.Option(
        False, "--autogenerate", help="Auto-generate migration from model changes"
    ),
    env_file: Annotated[
        Path | None,
        typer.Option("--env-file", "-e", help="Path to .env file"),
    ] = None,
) -> None:
    """
    Create a new migration revision.

    Examples:
        ipk db revision -m "Add user table"
        ipk db revision -m "Add email column" --autogenerate
    """
    from alembic import command  # noqa: PLC0415

    load_env_file(env_file)

    try:
        config = get_alembic_config()
        console.print(f"[cyan]Creating new revision:[/cyan] {message}")
        command.revision(
            config,
            message=message,
            autogenerate=autogenerate,
        )
        console.print("[green]✓[/green] Revision created successfully")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}", style="red")
        raise typer.Exit(1) from None


@app.command("version")
def show_version() -> None:
    """Show IdentityPlanKit version."""
    from identity_plan_kit import __version__  # noqa: PLC0415

    console.print(f"IdentityPlanKit version: [cyan]{__version__}[/cyan]")


@app.command("info")
def show_info(
    env_file: Annotated[
        Path | None,
        typer.Option("--env-file", "-e", help="Path to .env file"),
    ] = None,
) -> None:
    """Show configuration and environment information."""
    from identity_plan_kit import __version__  # noqa: PLC0415

    load_env_file(env_file)

    table = Table(title="IdentityPlanKit Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Version", __version__)

    # Show database URL (masked)
    db_url = os.environ.get("IPK_DATABASE_URL", "[red]Not set[/red]")
    if db_url and db_url != "[red]Not set[/red]":
        # SECURITY FIX: Properly mask password using URL parsing
        from urllib.parse import urlparse, urlunparse  # noqa: PLC0415

        try:
            parsed = urlparse(db_url)
            if parsed.password:
                # Reconstruct URL with masked password
                netloc = parsed.hostname or ""
                if parsed.username:
                    netloc = f"{parsed.username}:***@{netloc}"
                if parsed.port:
                    netloc = f"{netloc}:{parsed.port}"
                masked_parsed = parsed._replace(netloc=netloc)
                db_url = urlunparse(masked_parsed)
        except (ValueError, AttributeError, TypeError):
            # Fallback: just indicate URL is set but can't be parsed
            db_url = "[database URL set but could not be parsed for display]"
    table.add_row("Database URL", db_url)

    # Show other config
    table.add_row("Secret Key", "***" if os.environ.get("IPK_SECRET_KEY") else "[red]Not set[/red]")
    table.add_row(
        "Environment",
        os.environ.get("IPK_ENVIRONMENT", "[yellow]Not set (defaults to production)[/yellow]"),
    )
    table.add_row(
        "Redis URL",
        os.environ.get("IPK_REDIS_URL", "[yellow]Not set (using in-memory)[/yellow]"),
    )

    console.print(table)


def main() -> None:
    """Main CLI entry point."""
    app()


if __name__ == "__main__":
    main()
