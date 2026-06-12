"""Storage layer: Database + Repository."""

from app.storage.database import Database
from app.storage.repository import Repository
from app.utils.config import config

# Module-level singletons used across the app
_db: Database | None = None
_repo: Repository | None = None


def get_db() -> Database:
    global _db
    if _db is None:
        _db = Database(config.db_path)
    return _db


def get_repo() -> Repository:
    global _repo
    if _repo is None:
        _repo = Repository(get_db())
    return _repo
