# src/core/goal_manager.py
import sqlite3
from datetime import datetime
from typing import List, Optional, Dict, Any, TypedDict, Final, Set, Literal, Tuple, Union

from ..database import db_operations
from ..database.database_setup import get_db_connection

_SENTINEL = object()

class GoalData(TypedDict):
    id: int
    name: str
    description: Optional[str]
    target_date: Optional[str]
    status: str
    created_at: str
    updated_at: str

_VALID_GOAL_STATUSES: Final[Set[str]] = {"active", "completed", "archived"}
_VALID_GOAL_SORT_COLUMNS: Final[Set[str]] = {
    "id", "name", "target_date", "status", "created_at", "updated_at"
}
_VALID_SORT_ORDERS: Final[Set[Literal["ASC", "DESC"]]] = {"ASC", "DESC"}
_DEFAULT_GOAL_SORT_COLUMN: Final[str] = "created_at"
_DEFAULT_SORT_ORDER: Final[Literal["ASC", "DESC"]] = "ASC"


class GoalManager:
    def __init__(self) -> None:
        pass

    def _to_iso_string(self, dt_object: Optional[Union[datetime, str]]) -> Optional[str]:
        if isinstance(dt_object, datetime):
            return dt_object.isoformat(sep=" ", timespec="seconds")
        return dt_object # Handles None or str

    def add_goal(
        self,
        name: str,
        description: Optional[str] = None,
        target_date: Optional[Union[datetime, str]] = None,
        status: str = "active"
    ) -> Optional[int]:
        if status not in _VALID_GOAL_STATUSES:
            return None

        conn: Optional[sqlite3.Connection] = None
        now_iso: str = self._to_iso_string(datetime.now()) # type: ignore[arg-type]
        target_date_iso: Optional[str] = self._to_iso_string(target_date)

        sql: str = """
        INSERT INTO goals (name, description, target_date, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        params: Tuple[Any, ...] = (
            name, description, target_date_iso, status, now_iso, now_iso
        )

        try:
            conn = get_db_connection()
            cursor: sqlite3.Cursor = conn.cursor()
            goal_id: Optional[int] = db_operations.run_insert_statement(cursor, sql, params)
            conn.commit()
            return goal_id
        except sqlite3.Error:
            if conn:
                conn.rollback()
            return None
        finally:
            if conn:
                conn.close()

    def get_goal(self, goal_id: int) -> Optional[GoalData]:
        conn: Optional[sqlite3.Connection] = None
        sql: str = "SELECT * FROM goals WHERE id = ?"
        try:
            conn = get_db_connection()
            cursor: sqlite3.Cursor = conn.cursor()
            row: Optional[Dict[str, Any]] = db_operations.fetch_single_row(cursor, sql, (goal_id,))
            return GoalData(**row) if row else None
        except sqlite3.Error:
            return None
        finally:
            if conn:
                conn.close()

    def get_all_goals(
        self,
        status_filter: Optional[str] = None,
        sort_by: str = _DEFAULT_GOAL_SORT_COLUMN,
        sort_order: Literal["ASC", "DESC"] = _DEFAULT_SORT_ORDER
    ) -> List[GoalData]:
        conn: Optional[sqlite3.Connection] = None
        
        query_parts: List[str] = ["SELECT * FROM goals"]
        params_list: List[Any] = []

        if status_filter is not None:
            if status_filter in _VALID_GOAL_STATUSES:
                query_parts.append("WHERE status = ?")
                params_list.append(status_filter)

        actual_sort_by: str = sort_by if sort_by in _VALID_GOAL_SORT_COLUMNS else _DEFAULT_GOAL_SORT_COLUMN
        actual_sort_order: Literal["ASC", "DESC"] = sort_order if sort_order in _VALID_SORT_ORDERS else _DEFAULT_SORT_ORDER
        
        query_parts.append(f"ORDER BY {actual_sort_by} {actual_sort_order}")
        
        sql: str = " ".join(query_parts)
        
        try:
            conn = get_db_connection()
            cursor: sqlite3.Cursor = conn.cursor()
            rows: List[Dict[str, Any]] = db_operations.fetch_all_rows(cursor, sql, tuple(params_list))
            return [GoalData(**row) for row in rows]
        except sqlite3.Error:
            return []
        finally:
            if conn:
                conn.close()

    def update_goal(
        self,
        goal_id: int,
        name: Union[str, object] = _SENTINEL,
        description: Union[Optional[str], object] = _SENTINEL,
        target_date: Union[Optional[Union[datetime, str]], object] = _SENTINEL,
        status: Union[str, object] = _SENTINEL
    ) -> bool:
        conn: Optional[sqlite3.Connection] = None
        
        update_fields: List[str] = []
        params_list: List[Any] = []

        if name is not _SENTINEL and isinstance(name, str):
            update_fields.append("name = ?")
            params_list.append(name)
        
        if description is not _SENTINEL:
            update_fields.append("description = ?")
            params_list.append(description) # Can be None to set NULL
        
        if target_date is not _SENTINEL:
            update_fields.append("target_date = ?")
            params_list.append(self._to_iso_string(target_date)) # type: ignore[arg-type]

        if status is not _SENTINEL and isinstance(status, str):
            if status in _VALID_GOAL_STATUSES:
                update_fields.append("status = ?")
                params_list.append(status)
            else:
                return False 

        if not update_fields:
            return True 

        update_fields.append("updated_at = ?")
        params_list.append(self._to_iso_string(datetime.now())) # type: ignore[arg-type]
        params_list.append(goal_id)

        set_clause: str = ", ".join(update_fields)
        sql: str = f"UPDATE goals SET {set_clause} WHERE id = ?"

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

    def delete_goal(self, goal_id: int) -> bool:
        conn: Optional[sqlite3.Connection] = None
        sql: str = "DELETE FROM goals WHERE id = ?"
        try:
            conn = get_db_connection()
            cursor: sqlite3.Cursor = conn.cursor()
            db_operations.run_write_statement(cursor, sql, (goal_id,))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error:
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()
