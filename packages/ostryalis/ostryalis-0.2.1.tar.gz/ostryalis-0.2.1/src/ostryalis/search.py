__all__ = ['search']

import sqlalchemy as sa
from .database import database


async def search(q=None, session=None):
    async with database.use_session(session) as session:
        result = await session.execute(
            sa.text('''
                SELECT
                    *
                FROM
                    object
                LIMIT
                    100
            ''')
        )
        for row in result:
            yield dict(row._mapping)
