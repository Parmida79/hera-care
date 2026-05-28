import os

import typer
import uvicorn
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.app import app
from app.db.database import create_db_and_tables, engine, drop_and_create_db
from app.models import SuperAdmin, Admin, Patient, Member
from app.utils import hash_password

load_dotenv()

cli = typer.Typer(name="Hera Care\n Make Your Life Happier")


def env_int(name: str, default: int) -> int:
    v = os.getenv(name)
    return default if v is None else int(v)


def env_bool(name: str, default: bool) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    return v.lower() in ("1", "true", "yes", "y", "on")


@cli.command()
def run(
    port: int = env_int("LOCAL_PORT", 8000),
    host: str = os.getenv("LOCAL_HOST", "127.0.0.1"),
    log_level: str = os.getenv("LOG_LEVEL", "info"),
    reload: bool = env_bool("RELOAD", False),
):
    """Run the FastAPI app with uvicorn."""
    uvicorn.run(
        "app.app:app",
        host=host,
        port=port,
        log_level=log_level,
        reload=reload,
    )


@cli.command()
def create_user(role: str, username: str, password: str):
    """Create a user."""
    role_mapper = {
        'super-admin': SuperAdmin,
        'admin': Admin,
        'patient': Patient,
    }

    create_db_and_tables(engine)
    with Session(engine) as session:
        class_name = role_mapper[role]
        user = class_name(
            username=username,
            role=role,
            hashed_password=hash_password(password),
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        typer.echo(f"created user with id:{user.id} role:{user.role}")


@cli.command()
def shell():
    """Open an interactive shell with objects auto-imported."""
    _vars = {
        "app": app,
        "Member": Member,
        "engine": engine,
        "cli": cli,
        "create_user": create_user,
        "select": select,
        "session": Session(engine),
    }
    typer.echo(f"Auto imports: {list(_vars.keys())}")
    try:
        from IPython import start_ipython
        start_ipython(argv=[], user_ns=_vars)
    except ImportError:
        import code
        code.InteractiveConsole(_vars).interact()


@cli.command()
def drop_and_create_database():
    """Drop and create the database."""
    drop_and_create_db(engine)


if __name__ == "__main__":
    cli()
