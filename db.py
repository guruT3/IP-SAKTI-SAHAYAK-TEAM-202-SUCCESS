import logging
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)

try:
    import mysql.connector
    HAS_MYSQL = True
except ImportError:
    HAS_MYSQL = False


class SQLiteDictCursor:
    """Wrapper around sqlite3 cursor to mimic mysql dictionary cursor and %s placeholders."""
    def __init__(self, cursor):
        self.cursor = cursor

    def execute(self, query, params=None):
        # Convert %s placeholders to ? for sqlite3
        if params is not None:
            sqlite_query = query.replace("%s", "?")
            return self.cursor.execute(sqlite_query, params)
        return self.cursor.execute(query)

    def fetchone(self):
        row = self.cursor.fetchone()
        if row is None:
            return None
        # Convert sqlite3.Row or tuple to dict
        if isinstance(row, sqlite3.Row):
            return dict(row)
        cols = [col[0] for col in self.cursor.description]
        return dict(zip(cols, row))

    def fetchall(self):
        rows = self.cursor.fetchall()
        if not rows:
            return []
        cols = [col[0] for col in self.cursor.description]
        return [dict(zip(cols, r)) if not isinstance(r, sqlite3.Row) else dict(r) for r in rows]

    def close(self):
        self.cursor.close()


class SQLiteConnectionWrapper:
    """Wrapper around sqlite3 connection to mimic MySQL connection interface."""
    def __init__(self, conn):
        self.conn = conn

    def cursor(self, dictionary=False):
        c = self.conn.cursor()
        return SQLiteDictCursor(c)

    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()

    def close(self):
        self.conn.close()


def _get_sqlite_db():
    db_path = Path("data/app_fallback.db")
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    # Ensure users table exists
    with conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                referral_code TEXT
            )
        """)
    return SQLiteConnectionWrapper(conn)


def get_db():
    if HAS_MYSQL:
        try:
            return mysql.connector.connect(
                host="localhost",
                user="root",
                password="Guru2006@",
                database="ipsakti"
            )
        except Exception as e:
            logger.warning("MySQL connection failed (%s); falling back to local SQLite DB.", e)
            return _get_sqlite_db()
    return _get_sqlite_db()