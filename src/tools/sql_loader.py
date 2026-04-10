"""SQL data loader — query SQLite/PostgreSQL databases.

Supports SELECT queries only (read-only access for safety).
"""

import sqlite3

import pandas as pd


def query_sql(db_path: str, query: str) -> pd.DataFrame:
    """Execute a SELECT query against a SQLite database.

    Args:
        db_path: Path to SQLite .db file.
        query: SQL query (SELECT only).

    Returns pandas DataFrame with query results.
    Raises ValueError if query is not a SELECT statement.
    """
    normalized = query.strip().upper()
    if not normalized.startswith("SELECT"):
        raise ValueError("Only SELECT queries are allowed for safety. Got: " + query[:50])

    conn = sqlite3.connect(db_path)
    try:
        df = pd.read_sql_query(query, conn)
    finally:
        conn.close()

    return df
