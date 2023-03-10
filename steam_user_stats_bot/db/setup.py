import logging
import os
from contextlib import contextmanager
from logging import getLogger
from pathlib import Path
from time import sleep
from typing import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.session import Session

from alembic import command, script
from alembic.config import Config
from alembic.runtime import migration

from ..config import DB_DIR, DB_URL
from .schema import StatsBotDBBase

PROJECT_DIR = Path(__file__).parent.parent

logger = getLogger("init_db")


def create_db_dir():
    db_dir = os.path.dirname(DB_DIR)
    if not os.path.exists(db_dir):
        os.mkdir(db_dir)


# set up engine
create_db_dir()
engine = create_engine(DB_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)


@contextmanager
def session_context() -> Generator[Session, None, None]:
    """
    session_context() provides a managed session to the database that is automatically
    closed when the context is exited. This is the preferred method of accessing the
    database.
    """
    global SessionLocal
    sess = SessionLocal()
    try:
        yield sess
    finally:
        sess.close()


# Adapted from https://alembic.sqlalchemy.org/en/latest/cookbook.html#test-current-database-revision-is-at-head-s
def db_is_at_head(alembic_cfg: Config) -> bool:
    directory = script.ScriptDirectory.from_config(alembic_cfg)
    with engine.begin() as connection:
        context = migration.MigrationContext.configure(connection)
        return set(context.get_current_heads()) == set(directory.get_heads())


def connect(session: Session) -> bool:
    try:
        session.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Error connecting to database: {e}")
        return False


def init_db():
    # Wait for database to connect
    max_retry = 10
    wait_seconds = 1

    with session_context() as session:
        while True:
            if connect(session):
                logger.info("Database connection established.")
                break

            logger.error(f"Database connection failed. Retrying in {wait_seconds} seconds...")
            max_retry -= 1

            sleep(wait_seconds)

            if max_retry == 0:
                raise ConnectionError("Database connection failed - exiting application.")

        alembic_cfg = Config(str(PROJECT_DIR / "alembic.ini"))
        if db_is_at_head(alembic_cfg):
            logger.debug("Migration not needed.")
        else:
            logger.info("Migration needed. Performing migration...")
            command.upgrade(alembic_cfg, "head")


if __name__ == "__main__":
    init_db()
