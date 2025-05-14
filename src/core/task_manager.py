# src/core/task_manager.py
import sqlite3
from datetime import datetime
from typing import List, Optional, Dict, Any, TypedDict, Final, Set, Literal, Tuple, Union

from database import db_operations
from database.database_setup import get_db_connection

_SENTINEL = object()

class TaskData(TypedDict):
    id: int
    title: str
    description: Optional[str]
    priority: int
    due_date: Optional[str]
    status: str
    created_at: str
    updated_at: str
    project_id: Optional[int]
    parent_task_id: Optional[int]

_VALID_TASK_STATUSES: Final[Set[str]] = {
    "pending", "in_progress", "completed", "cancelled"
}
_VALID_TASK_PRIORITIES: Final[Set[int]] = {0, 1, 2}
_VALID_TASK_SORT_COLUMNS: Final[Set[str]] = {
    "id", "title", "priority", "due_date", "status", "created_at", "updated_at"
}
_DEFAULT_TASK_SORT_COLUMN: Final[str] = "created_at"
_VALID_SORT_ORDERS: Final[Set[Literal["ASC", "DESC"]]] = {"ASC", "DESC"}
_DEFAULT_SORT_ORDER: Final[Literal["ASC", "DESC"]] = "ASC"


class TaskManager:
    def __init__(self) -> None:
        pass

    def _to_iso_string(self, dt_object: Optional[Union[datetime, str]]) -> Optional[str]:
        if isinstance(dt_object, datetime):
            return dt_object.isoformat(sep=" ", timespec="seconds")
        return dt_object 

    def add_task(
        self,
        title: str,
        description: Optional[str] = None,
        priority: int = 0,
        due_date: Optional[Union[datetime, str]] = None,
        project_id: Optional[int] = None,
        parent_task_id: Optional[int] = None,
        status: str = "pending"
    ) -> Optional[int]:
        if status not in _VALID_TASK_STATUSES or priority not in _VALID_TASK_PRIORITIES:
            return None

        conn: Optional[sqlite3.Connection] = None
        now_iso: str = self._to_iso_string(datetime.now()) # type: ignore[arg-type] # datetime.now() is not Optional
        due_date_iso: Optional[str] = self._to_iso_string(due_date)

        sql: str = """
        INSERT INTO tasks 
            (title, description, priority, due_date, project_id, 
             parent_task_id, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params: Tuple[Any, ...] = (
            title, description, priority, due_date_iso, project_id,
            parent_task_id, status, now_iso, now_iso
        )

        try:
            conn = get_db_connection()
            cursor: sqlite3.Cursor = conn.cursor()
            task_id: Optional[int] = db_operations.run_insert_statement(cursor, sql, params)
            conn.commit()
            return task_id
        except sqlite3.Error:
            if conn:
                conn.rollback()
            return None
        finally:
            if conn:
                conn.close()

    def get_task(self, task_id: int) -> Optional[TaskData]:
        conn: Optional[sqlite3.Connection] = None
        sql: str = "SELECT * FROM tasks WHERE id = ?"
        try:
            conn = get_db_connection()
            cursor: sqlite3.Cursor = conn.cursor()
            row: Optional[Dict[str, Any]] = db_operations.fetch_single_row(cursor, sql, (task_id,))
            return TaskData(**row) if row else None
        except sqlite3.Error:
            return None
        finally:
            if conn:
                conn.close()

    def get_all_tasks(
        self,
        project_id_filter: Optional[int] = None,
        status_filter: Optional[str] = None,
        sort_by: str = _DEFAULT_TASK_SORT_COLUMN,
        sort_order: Literal["ASC", "DESC"] = _DEFAULT_SORT_ORDER
    ) -> List[TaskData]:
        conn: Optional[sqlite3.Connection] = None
        
        query_parts: List[str] = ["SELECT * FROM tasks"]
        params_list: List[Any] = []
        conditions: List[str] = []

        if project_id_filter is not None:
            conditions.append("project_id = ?")
            params_list.append(project_id_filter)
        if status_filter is not None:
            if status_filter in _VALID_TASK_STATUSES:
                conditions.append("status = ?")
                params_list.append(status_filter)

        if conditions:
            query_parts.append("WHERE")
            query_parts.append(" AND ".join(conditions))

        actual_sort_by: str = sort_by if sort_by in _VALID_TASK_SORT_COLUMNS else _DEFAULT_TASK_SORT_COLUMN
        actual_sort_order: Literal["ASC", "DESC"] = sort_order if sort_order in _VALID_SORT_ORDERS else _DEFAULT_SORT_ORDER
        
        query_parts.append(f"ORDER BY {actual_sort_by} {actual_sort_order}")
        
        sql: str = " ".join(query_parts)
        
        try:
            conn = get_db_connection()
            cursor: sqlite3.Cursor = conn.cursor()
            rows: List[Dict[str, Any]] = db_operations.fetch_all_rows(cursor, sql, tuple(params_list))
            return [TaskData(**row) for row in rows]
        except sqlite3.Error:
            return []
        finally:
            if conn:
                conn.close()

    def update_task(
        self,
        task_id: int,
        title: Union[str, object] = _SENTINEL,
        description: Union[Optional[str], object] = _SENTINEL,
        priority: Union[int, object] = _SENTINEL,
        due_date: Union[Optional[Union[datetime, str]], object] = _SENTINEL,
        status: Union[str, object] = _SENTINEL,
        project_id: Union[Optional[int], object] = _SENTINEL,
        parent_task_id: Union[Optional[int], object] = _SENTINEL
    ) -> bool:
        conn: Optional[sqlite3.Connection] = None
        update_fields: List[str] = []
        params_list: List[Any] = []

        if title is not _SENTINEL and isinstance(title, str):
            update_fields.append("title = ?")
            params_list.append(title)
        if description is not _SENTINEL:
            update_fields.append("description = ?")
            params_list.append(description)
        if priority is not _SENTINEL and isinstance(priority, int) and priority in _VALID_TASK_PRIORITIES:
            update_fields.append("priority = ?")
            params_list.append(priority)
        if due_date is not _SENTINEL:
            update_fields.append("due_date = ?")
            params_list.append(self._to_iso_string(due_date))
        if status is not _SENTINEL and isinstance(status, str) and status in _VALID_TASK_STATUSES:
            update_fields.append("status = ?")
            params_list.append(status)
        if project_id is not _SENTINEL:
            update_fields.append("project_id = ?")
            params_list.append(project_id)
        if parent_task_id is not _SENTINEL:
            update_fields.append("parent_task_id = ?")
            params_list.append(parent_task_id)

        if not update_fields:
            return True

        update_fields.append("updated_at = ?")
        params_list.append(self._to_iso_string(datetime.now())) # type: ignore[arg-type]
        params_list.append(task_id)

        set_clause: str = ", ".join(update_fields)
        sql: str = f"UPDATE tasks SET {set_clause} WHERE id = ?"

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

    def delete_task(self, task_id: int) -> bool:
        conn: Optional[sqlite3.Connection] = None
        sql: str = "DELETE FROM tasks WHERE id = ?"
        try:
            conn = get_db_connection()
            cursor: sqlite3.Cursor = conn.cursor()
            db_operations.run_write_statement(cursor, sql, (task_id,))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error:
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()

    def update_task_status(self, task_id: int, new_status: str) -> bool:
        if new_status not in _VALID_TASK_STATUSES:
            return False
        return self.update_task(task_id, status=new_status)
