import logging
from typing import Optional

from psycopg import AsyncCursor, sql
from psycopg.abc import Query, Params

logger = logging.getLogger(__name__)


def get_connection_encoding(conn):
    """Get connection encoding, with fallback for different psycopg versions."""
    try:
        from psycopg._encodings import pgconn_encoding
        return pgconn_encoding(conn.pgconn)
    except (ImportError, AttributeError):
        # Fallback for newer versions or when internal API is not available
        try:
            return conn.info.encoding
        except AttributeError:
            return 'utf-8'  # Safe default


class AsyncLoggingCursor(AsyncCursor):
    def mogrify_query(self, query: Query):
        if isinstance(query, str):
            msg = query
        elif isinstance(query, (sql.SQL, sql.Composed)):
            msg = query.as_string(self)
        elif isinstance(query, bytes):
            msg = query.decode(get_connection_encoding(self._conn), 'replace')
        else:
            msg = repr(query)
        return msg

    async def execute(self, query: Query, params: Optional[Params] = None, **kwargs):
        if logging.DEBUG >= logger.getEffectiveLevel():
            msg = self.mogrify_query(query)
            logger.debug(
                "Executing query (%s) with values %s", msg, params,
                extra={'action': "Query Execute"}
            )
        try:
            return await super().execute(query, params=params, **kwargs)
        except Exception:
            msg = self.mogrify_query(query)
            logger.exception(
                "Exception during query execution. Query (%s) with parameters %s.",
                msg, params,
                extra={'action': "Query Execute"},
                stack_info=True
            )
        else:
            # TODO: Possibly log execution time
            pass