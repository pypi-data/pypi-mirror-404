import pytest

from pathlib import Path
from shutil import copy2
import sqlalchemy as sa

@pytest.fixture()
def database(tmp_path):
    from ostryalis import Database
    dir = Path(__file__).resolve().parent
    copy2(dir / 'db' / 'main.db', tmp_path / 'main.db')
    return Database(cfg=lambda _key: str(tmp_path))

@pytest.fixture()
def session(database):
    with database.use_session() as session:
        yield session

def test_attach_before(database):
    database.attach('extra')
    with database.use_session() as session:
        result = [row[1] for row in session.execute(sa.text("PRAGMA database_list"))]
        assert result == ['main', 'extra']

def test_attach_after(database, session):
    database.attach('extra')
    result = [row[1] for row in session.execute(sa.text("PRAGMA database_list"))]
    assert result == ['main', 'extra']

def test_udf_object_id_type(session):
    result = session.execute(sa.text("SELECT object_id('type', 'type')"))
    assert result.one()[0] == 1

def test_udf_object_id_uuid(session):
    result = session.execute(sa.text("SELECT object_id('uuid', '2a730192-be8a-8e80-9604-915e7b0d513d')"))
    assert result.one()[0] == 300001
