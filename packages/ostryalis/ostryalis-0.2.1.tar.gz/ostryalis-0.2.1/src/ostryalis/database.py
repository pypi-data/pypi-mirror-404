__all__ = ['Database', 'database']

from collections import defaultdict
from contextlib import asynccontextmanager
from pathlib import Path
import threading
from typing import Iterable

import sqlalchemy
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from inceptum import config


class Database:
    def __init__(self, *, cfg=None):
        self._config = cfg or config
        self._engine: AsyncEngine | None = None
        self._attachments: dict[str, str] = {}
        self._lock = threading.RLock()

    @property
    def engine(self) -> AsyncEngine:
        return self._get_engine()

    @asynccontextmanager
    async def use_session(self, session: AsyncSession | None = None, *, commit: bool = True):
        """
        If `session` is provided, it is reused and never committed/rolled back/closed
        by this context manager.

        If `session` is not provided, a new session is created; it is committed if
        `commit=True`, rolled back on exception, and always closed.
        """
        if session is not None:
            yield session
            return

        self._get_engine()  # make sure there is a self._session_factory
        new_session = self._session_factory()
        try:
            yield new_session
            if commit:
                await new_session.commit()
        except Exception:
            await new_session.rollback()
            raise
        finally:
            await new_session.close()

    def attach(self, alias: str, path: str | Path | None = None) -> str:
        """
        Register an attachment alias.

        If `path` is not provided, uses `{base_dir}/{alias}.db`.

        This only registers the mapping; actual ATTACH happens on connect.
        """
        if path is None:
            db_path = self._base_dir() / f"{alias}.db"
        else:
            db_path = Path(path).expanduser()
            if not db_path.is_absolute():
                # Relative paths become relative to base dir for predictability.
                db_path = self._base_dir() / db_path

        # Do not create the file here; ATTACH will create it if needed.
        db_path.parent.mkdir(parents=True, exist_ok=True)

        with self._lock:
            self._attachments.setdefault(alias, str(db_path))
        return alias

    async def dispose(self) -> None:
        with self._lock:
            if self._engine is not None:
                await self._engine.dispose()
                self._engine = None

    def _get_engine(self) -> AsyncEngine:
        with self._lock:
            if self._engine is not None:
                return self._engine

            base_dir = self._base_dir()
            db_url = f"sqlite+aiosqlite:///{base_dir / 'main.db'}"

            self._engine = create_async_engine(
                db_url,
                connect_args={"check_same_thread": False},
                future=True,
            )

            # Hook into the *sync* engine's connect event, so setup happens
            # automatically when DB-API connections are created.
            sqlalchemy.event.listen(
                self._engine.sync_engine,
                "connect",
                self._sqlite_on_connect,
            )

            self._session_factory = async_sessionmaker(
                bind=self._engine,
                autoflush=False,
                expire_on_commit=False,
            )

            return self._engine

    def _sqlite_on_connect(self, dbapi_connection, connection_record) -> None:
        """
        Runs on creation of a DB-API connection (via the sync engine that the async
        engine wraps). Safe place to do SQLite-specific connection setup.
        """
        with self._lock:
            aliases = list(self._attachments.keys())

        if aliases:
            self._sqlite_attach_aliases(dbapi_connection, aliases=aliases)

        _udf(dbapi_connection)

    def _sqlite_attach_aliases(self, dbapi_connection, *, aliases: Iterable[str]) -> None:
        cur = dbapi_connection.cursor()
        try:
            cur.execute("PRAGMA database_list")
            already = {row[1] for row in cur.fetchall()}

            for alias in aliases:
                if alias in already:
                    continue

                with self._lock:
                    path = self._attachments.get(alias)
                if path is None:
                    raise KeyError(f"Alias '{alias}' is not registered; call attach() first.")

                path_sql = path.replace("'", "''")  # prevent SQL injection
                cur.execute(f"ATTACH DATABASE '{path_sql}' AS {alias}")
        finally:
            cur.close()

    def _base_dir(self) -> Path:
        base_dir = Path(str(self._config("ostryalis.directory"))).expanduser()
        base_dir.mkdir(parents=True, exist_ok=True)
        return base_dir


def _udf(dbapi_connection):
    cache = defaultdict(dict)

    def object_id(type, name, prefix='main'):
        value = cache[type].get(name)
        if value is not None:
            return value

        if type == 'uuid':
            sql = f'''
                SELECT
                    id
                FROM
                    {prefix}.object
                WHERE
                    uuid = :uuid
            '''
            parameters = {'uuid': name}
        else:
            sql = f'''
                SELECT
                    o.id
                FROM
                    {prefix}.object o
                JOIN
                    {prefix}.object t on (t.id = o.type)
                WHERE
                    t.title = :type
                    and o.title = :name
            '''
            parameters = {'type': type, 'name': name}

        cursor = dbapi_connection.execute(sqlalchemy.text(sql), parameters)
        if row := cursor.fetchone():
            value = cache[type][name] = row[0]
            return value

    dbapi_connection.create_function('object_id', 2, object_id)
    dbapi_connection.create_function('object_id', 3, object_id)


database = Database()
