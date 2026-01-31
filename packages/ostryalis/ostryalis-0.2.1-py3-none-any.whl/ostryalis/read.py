__all__ = ['read']

import sqlalchemy as sa
from .database import database


async def read(a, title=None, session=None):
    async with database.use_session(session) as session:
        if title is not None:
            # assume a is a type
            sql = SQL_TYPE
            parameters = {
                'type': a,
                'title': title,
            }
        else:
            # assume a is an uuid
            sql = SQL_UUID
            parameters = {'uuid': a}

        result = await session.execute(sa.text(sql), parameters)
        row = result.one_or_none()
        if row:
            return dict(row._mapping)


SQL_UUID = '''
    SELECT
        *
    FROM
        object
    WHERE
        uuid = :uuid
'''


SQL_TYPE = '''
    SELECT
        o.*
    FROM
        object o
    JOIN
        object t on (t.id = o.type)
    WHERE
        t.title = :type
        and o.title = :title
'''
