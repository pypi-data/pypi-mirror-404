import os
from pathlib import Path
from typing import Iterable, Mapping, Sequence

from sqlmodel import create_engine
from sqlmodel import SQLModel

if Path(".env").is_file():
    from dotenv import load_dotenv

    load_dotenv()


def db_connect_string():
    """Generate the DB connection string from different environment variables."""
    user = os.getenv("DB_USER", "dbuser")
    passwd = os.getenv("DB_PASSWD")
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", 3306)
    name = os.getenv("DB_NAME")

    return f"mysql+pymysql://{user}:{passwd}@{host}:{port}/{name}"


engine = create_engine(db_connect_string())


def init_db():
    SQLModel.metadata.create_all(engine)


def update_entry_fields(entry: SQLModel, update: Mapping) -> SQLModel:
    for field, value in update.items():
        if field in entry.__class__.model_fields:
            setattr(entry, field, value)
    return entry


def exclude_none(data: Mapping) -> dict:
    return {k: v for k, v in data.items() if v is not None}


def common_keys_equal(
    first: Mapping, second: Mapping, digits: int = 5, exclude_keys: Iterable = ()
) -> bool:
    """Compares the values of the common keys in two dictionaries. Returns True if all
    values are equal, False otherwise."""

    def equal(a, b):
        if isinstance(a, float) and isinstance(b, float):
            return round(a, digits) == round(b, digits)
        else:
            return a == b

    common_keys = set(first.keys()) & set(second.keys())
    return all(equal(first[k], second[k]) for k in common_keys - set(exclude_keys))


def index(items: Sequence, *, key: str) -> dict:
    """Returns a dictionary from a sequence of items with one of the items' field as
    key."""
    return {getattr(item, key): item for item in items}
