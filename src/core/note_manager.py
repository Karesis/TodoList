# src/core/note_manager.py
import sqlite3
from datetime import datetime
from typing import List, Optional, Dict, Any, TypedDict, Final, Set, Literal, Tuple, Union

from ..database import db_operations
from ..database.database_setup import get_db_connection

_SENTINEL = object()

class NoteData(TypedDict):
    id: int
    title: Optional[str]
    content: str
    created_at: str
    updated_at: str
    task_id: Optional[int]
    project_id: Optional[int]

_VALID_NOTE_SORT_COLUMNS: Final[Set[str]] = {
    "id", "title", "created_at", "updated_at"
}
_DEFAULT_NOTE_SORT_COLUMN: Final[str] = "created_at"
_VALID_SORT_ORDERS: Final[Set[Literal["ASC", "DESC"]]] = {"ASC", "DESC"} # Re-used
_DEFAULT_SORT_ORDER: Final[Literal["ASC", "DESC"]] = "ASC"


class NoteManager:
    def __init__(self) -> None:
        pass

    def _to_iso_string(self, dt_object: datetime) -> str: # Simplified: assumes datetime input for now_iso
        return dt_object.isoformat(sep=" ", timespec="seconds")

    def add_note(
        self,
        content: str,
        title: Optional[str] = None,
        task_id: Optional[int] = None,
        project_id: Optional[int] = None
    ) -> Optional[int]:
        conn: Optional[sqlite3.Connection] = None
        now_iso: str = self._to_iso_string(datetime.now())
        sql: str = """
        INSERT INTO notes (title, content, task_id, project_id, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        params: Tuple[Any, ...] = (
            title, content, task_id, project_id, now_iso, now_iso
        )

        try:
            conn = get_db_connection()
            cursor: sqlite3.Cursor = conn.cursor()
            note_id: Optional[int] = db_operations.run_insert_statement(cursor, sql, params)
            conn.commit()
            return note_id
        except sqlite3.Error:
            if conn:
                conn.rollback()
            return None
        finally:
            if conn:
                conn.close()

    def get_note(self, note_id: int) -> Optional[NoteData]:
        conn: Optional[sqlite3.Connection] = None
        sql: str = "SELECT id, title, content, created_at, updated_at, task_id, project_id FROM notes WHERE id = ?"
        try:
            conn = get_db_connection()
            cursor: sqlite3.Cursor = conn.cursor()
            row: Optional[Dict[str, Any]] = db_operations.fetch_single_row(cursor, sql, (note_id,))
            return NoteData(**row) if row else None
        except sqlite3.Error:
            return None
        finally:
            if conn:
                conn.close()

    def get_all_notes(
        self,
        task_id_filter: Optional[int] = None,
        project_id_filter: Optional[int] = None,
        sort_by: str = _DEFAULT_NOTE_SORT_COLUMN,
        sort_order: Literal["ASC", "DESC"] = _DEFAULT_SORT_ORDER
    ) -> List[NoteData]:
        conn: Optional[sqlite3.Connection] = None
        
        query_parts: List[str] = ["SELECT id, title, content, created_at, updated_at, task_id, project_id FROM notes"]
        params_list: List[Any] = []
        conditions: List[str] = []

        if task_id_filter is not None:
            conditions.append("task_id = ?")
            params_list.append(task_id_filter)
        if project_id_filter is not None:
            conditions.append("project_id = ?")
            params_list.append(project_id_filter)

        if conditions:
            query_parts.append("WHERE")
            query_parts.append(" AND ".join(conditions))

        actual_sort_by: str = sort_by if sort_by in _VALID_NOTE_SORT_COLUMNS else _DEFAULT_NOTE_SORT_COLUMN
        actual_sort_order: Literal["ASC", "DESC"] = sort_order if sort_order in _VALID_SORT_ORDERS else _DEFAULT_SORT_ORDER
        
        query_parts.append(f"ORDER BY {actual_sort_by} {actual_sort_order}")
        
        sql: str = " ".join(query_parts)
        
        try:
            conn = get_db_connection()
            cursor: sqlite3.Cursor = conn.cursor()
            rows: List[Dict[str, Any]] = db_operations.fetch_all_rows(cursor, sql, tuple(params_list))
            return [NoteData(**row) for row in rows]
        except sqlite3.Error:
            return []
        finally:
            if conn:
                conn.close()

    def update_note(
        self,
        note_id: int,
        title: Union[Optional[str], object] = _SENTINEL,
        content: Union[str, object] = _SENTINEL, # content is NOT NULL
        task_id: Union[Optional[int], object] = _SENTINEL,
        project_id: Union[Optional[int], object] = _SENTINEL
    ) -> bool:
        conn: Optional[sqlite3.Connection] = None
        
        update_fields: List[str] = []
        params_list: List[Any] = []

        if title is not _SENTINEL:
            update_fields.append("title = ?")
            params_list.append(title) 
        
        if content is not _SENTINEL:
            if isinstance(content, str): # Ensure content is provided if not sentinel
                 update_fields.append("content = ?")
                 params_list.append(content)
            else: # content must be a string if provided
                return False


        if task_id is not _SENTINEL:
            update_fields.append("task_id = ?")
            params_list.append(task_id) 
        
        if project_id is not _SENTINEL:
            update_fields.append("project_id = ?")
            params_list.append(project_id) 

        if not update_fields:
            return True

        update_fields.append("updated_at = ?")
        params_list.append(self._to_iso_string(datetime.now()))
        params_list.append(note_id)

        set_clause: str = ", ".join(update_fields)
        sql: str = f"UPDATE notes SET {set_clause} WHERE id = ?"

        try:
            conn = get_db_connection()
            cursor: sqlite3.Cursor = conn.cursor()
            db_operations.run_write_statement(cursor, sql, tuple(params_list))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error:
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()

    def delete_note(self, note_id: int) -> bool:
        conn: Optional[sqlite3.Connection] = None
        sql: str = "DELETE FROM notes WHERE id = ?"
        try:
            conn = get_db_connection()
            cursor: sqlite3.Cursor = conn.cursor()
            db_operations.run_write_statement(cursor, sql, (note_id,))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error:
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()
