"""
db_utils.py

Reusable database connection helpers for the Superstore SQLite database.

This module wraps the same connection logic used throughout SQL_Task2.ipynb
(sqlite3 and SQLAlchemy) into functions that can be imported instead of
rewritten in every script or notebook that needs to talk to the database.

Usage:
    from db_utils import get_connection, get_engine, run_query

    conn = get_connection()
    df = run_query("SELECT * FROM superstore LIMIT 10;", conn)
"""

import sqlite3
import pandas as pd
from sqlalchemy import create_engine

DB_PATH = "superstore.db"


def get_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    """
    Open a sqlite3 connection to the Superstore database.

    Parameters
    ----------
    db_path : str
        Path to the SQLite database file. Defaults to "superstore.db"
        in the current working directory, matching the rest of the project.

    Returns
    -------
    sqlite3.Connection
        An open connection. The caller is responsible for closing it
        (or it can simply be reused for the lifetime of a script/notebook).
    """
    conn = sqlite3.connect(db_path)
    return conn


def get_engine(db_path: str = DB_PATH):
    """
    Create a SQLAlchemy engine pointed at the Superstore database.

    Using SQLAlchemy instead of a raw sqlite3 connection is useful if the
    project ever moves from SQLite to PostgreSQL or MySQL, since pd.read_sql()
    treats both connection types identically.

    Parameters
    ----------
    db_path : str
        Path to the SQLite database file.

    Returns
    -------
    sqlalchemy.engine.Engine
    """
    engine = create_engine(f"sqlite:///{db_path}")
    return engine


def run_query(query: str, conn, params: tuple = None) -> pd.DataFrame:
    """
    Run a SQL query against an open connection and return the result
    as a pandas DataFrame.

    Parameters
    ----------
    query : str
        The SQL query to execute.
    conn : sqlite3.Connection or sqlalchemy.engine.Engine
        An open connection, from get_connection() or get_engine().
    params : tuple, optional
        Parameters to safely substitute into a parameterised query
        (using "?" placeholders), to avoid SQL injection.

    Returns
    -------
    pandas.DataFrame
    """
    if params is not None:
        return pd.read_sql(query, conn, params=params)
    return pd.read_sql(query, conn)


def load_dataframe_to_table(df: pd.DataFrame, table_name: str, conn, if_exists: str = "replace") -> None:
    """
    Load a pandas DataFrame into a database table.

    Parameters
    ----------
    df : pandas.DataFrame
        The data to load.
    table_name : str
        Name of the destination table.
    conn : sqlite3.Connection
        An open connection.
    if_exists : str
        Behaviour if the table already exists: "replace", "append", or "fail".
        Defaults to "replace" so the table always reflects the latest data.
    """
    df.to_sql(table_name, conn, if_exists=if_exists, index=False)
    print(f"Loaded {len(df)} rows into table '{table_name}'.")


if __name__ == "__main__":
    # Quick manual check that the module works on its own.
    conn = get_connection()
    result = run_query("SELECT name FROM sqlite_master WHERE type='table';", conn)
    print("Tables in database:")
    print(result)
    conn.close()
