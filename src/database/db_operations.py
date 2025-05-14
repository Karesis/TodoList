import sqlite3
from typing import Any, List, Optional, Tuple, Dict

def fetch_single_row(
    cursor: sqlite3.Cursor, 
    query: str, 
    params: Optional[Tuple[Any, ...]] = None
) -> Optional[Dict[str, Any]]:
    cursor.execute(query, params or ())
    row: Optional[sqlite3.Row] = cursor.fetchone()
    # Assumes connection was set up with sqlite3.Row factory
    return dict(row) if row else None

def fetch_all_rows(
    cursor: sqlite3.Cursor, 
    query: str, 
    params: Optional[Tuple[Any, ...]] = None
) -> List[Dict[str, Any]]:
    cursor.execute(query, params or ())
    rows: List[sqlite3.Row] = cursor.fetchall()
    # Assumes connection was set up with sqlite3.Row factory
    return [dict(row) for row in rows]

def run_write_statement(
    cursor: sqlite3.Cursor, 
    statement: str, 
    params: Optional[Tuple[Any, ...]] = None
) -> None:
    cursor.execute(statement, params or ())

def run_insert_statement(
    cursor: sqlite3.Cursor, 
    statement: str, 
    params: Optional[Tuple[Any, ...]] = None
) -> Optional[int]:
    cursor.execute(statement, params or ())
    return cursor.lastrowid
