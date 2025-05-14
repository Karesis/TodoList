# src/database/database_setup.py
import sqlite3
from pathlib import Path
from typing import Final, Optional

_CURRENT_SCRIPT_DIR: Final[Path] = Path(__file__).resolve().parent
DATABASE_DIR: Final[Path] = _CURRENT_SCRIPT_DIR / "app_data"
DATABASE_NAME: Final[str] = "timemanager.db"
DATABASE_PATH: Final[Path] = DATABASE_DIR / DATABASE_NAME
_SCHEMA_FILE_PATH: Final[Path] = _CURRENT_SCRIPT_DIR / "schema.sql"

def get_db_path() -> Path:
    return DATABASE_PATH

def get_db_connection() -> sqlite3.Connection:
    DATABASE_DIR.mkdir(parents=True, exist_ok=True)
    conn: sqlite3.Connection = sqlite3.connect(str(DATABASE_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def initialize_database() -> None:
    sql_schema: str
    try:
        with open(_SCHEMA_FILE_PATH, 'r', encoding='utf-8') as f:
            sql_schema = f.read()
    except FileNotFoundError:
        print(f"CRITICAL: Schema file not found at '{_SCHEMA_FILE_PATH}'. Database cannot be initialized.")
        raise
    
    conn: Optional[sqlite3.Connection] = None
    try:
        conn = get_db_connection()
        cursor: sqlite3.Cursor = conn.cursor()
        cursor.executescript(sql_schema)
        conn.commit()
    except sqlite3.Error as e:
        print(f"ERROR: Failed to initialize database schema from '{_SCHEMA_FILE_PATH}': {e}")
        if conn:
            conn.rollback() 
        raise
    finally:
        if conn:
            conn.close()

