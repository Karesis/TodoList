# src/core/reminder_manager.py
import sqlite3
from datetime import datetime
from typing import List, Optional, Dict, Any, TypedDict, Final, Set, Literal, Tuple, Union

from ..database import db_operations
from ..database.database_setup import get_db_connection

_SENTINEL = object()

class ReminderData(TypedDict):
    id: int
    task_id: Optional[int]
    event_id: Optional[int]
    reminder_time: str
    message: Optional[str]
    status: str
    created_at: str
    updated_at: str

_VALID_REMINDER_STATUSES: Final[Set[str]] = {
    "pending", "triggered", "dismissed", "snoozed"
}
_VALID_REMINDER_SORT_COLUMNS: Final[Set[str]] = {
    "id", "task_id", "event_id", "reminder_time", "message", 
    "status", "created_at", "updated_at"
}
_DEFAULT_REMINDER_SORT_COLUMN: Final[str] = "reminder_time"
_VALID_SORT_ORDERS: Final[Set[Literal["ASC", "DESC"]]] = {"ASC", "DESC"}
_DEFAULT_SORT_ORDER: Final[Literal["ASC", "DESC"]] = "ASC"


class ReminderManager:
    def __init__(self) -> None:
        pass

    def _to_iso_string(self, dt_object: Union[datetime, str]) -> str:
        if isinstance(dt_object, datetime):
            return dt_object.isoformat(sep=" ", timespec="seconds")
        return dt_object 

    def add_reminder(
        self,
        reminder_time: Union[datetime, str],
        message: Optional[str] = None,
        task_id: Optional[int] = None,
        event_id: Optional[int] = None,
        status: str = "pending"
    ) -> Optional[int]:
        if status not in _VALID_REMINDER_STATUSES:
            return None

        conn: Optional[sqlite3.Connection] = None
        now_iso: str = self._to_iso_string(datetime.now())
        reminder_time_iso: str = self._to_iso_string(reminder_time)

        sql: str = """
        INSERT INTO reminders 
            (task_id, event_id, reminder_time, message, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        params: Tuple[Any, ...] = (
            task_id, event_id, reminder_time_iso, message, status, now_iso, now_iso
        )

        try:
            conn = get_db_connection()
            cursor: sqlite3.Cursor = conn.cursor()
            reminder_id: Optional[int] = db_operations.run_insert_statement(cursor, sql, params)
            conn.commit()
            return reminder_id
        except sqlite3.Error:
            if conn:
                conn.rollback()
            return None
        finally:
            if conn:
                conn.close()

    def get_reminder(self, reminder_id: int) -> Optional[ReminderData]:
        conn: Optional[sqlite3.Connection] = None
        sql: str = "SELECT * FROM reminders WHERE id = ?"
        try:
            conn = get_db_connection()
            cursor: sqlite3.Cursor = conn.cursor()
            row: Optional[Dict[str, Any]] = db_operations.fetch_single_row(cursor, sql, (reminder_id,))
            return ReminderData(**row) if row else None
        except sqlite3.Error:
            return None
        finally:
            if conn:
                conn.close()

    def get_all_reminders(
        self,
        sort_by: str = _DEFAULT_REMINDER_SORT_COLUMN,
        sort_order: Literal["ASC", "DESC"] = _DEFAULT_SORT_ORDER
    ) -> List[ReminderData]:
        conn: Optional[sqlite3.Connection] = None
        actual_sort_by: str = sort_by if sort_by in _VALID_REMINDER_SORT_COLUMNS else _DEFAULT_REMINDER_SORT_COLUMN
        actual_sort_order: Literal["ASC", "DESC"] = sort_order if sort_order in _VALID_SORT_ORDERS else _DEFAULT_SORT_ORDER
        
        sql: str = f"SELECT * FROM reminders ORDER BY {actual_sort_by} {actual_sort_order}"
        
        try:
            conn = get_db_connection()
            cursor: sqlite3.Cursor = conn.cursor()
            rows: List[Dict[str, Any]] = db_operations.fetch_all_rows(cursor, sql)
            return [ReminderData(**row) for row in rows]
        except sqlite3.Error:
            return []
        finally:
            if conn:
                conn.close()

    def update_reminder(
        self,
        reminder_id: int,
        reminder_time: Union[datetime, str, object] = _SENTINEL,
        message: Union[Optional[str], object] = _SENTINEL,
        status: Union[str, object] = _SENTINEL,
        task_id: Union[Optional[int], object] = _SENTINEL,
        event_id: Union[Optional[int], object] = _SENTINEL
    ) -> bool:
        conn: Optional[sqlite3.Connection] = None
        update_fields: List[str] = []
        params_list: List[Any] = []

        if reminder_time is not _SENTINEL:
            update_fields.append("reminder_time = ?")
            params_list.append(self._to_iso_string(reminder_time)) # type: ignore[arg-type]
        if message is not _SENTINEL:
            update_fields.append("message = ?")
            params_list.append(message)
        if status is not _SENTINEL:
            if isinstance(status, str) and status in _VALID_REMINDER_STATUSES:
                update_fields.append("status = ?")
                params_list.append(status)
            else:
                return False 
        if task_id is not _SENTINEL:
            update_fields.append("task_id = ?")
            params_list.append(task_id)
        if event_id is not _SENTINEL:
            update_fields.append("event_id = ?")
            params_list.append(event_id)

        if not update_fields:
            return True 

        update_fields.append("updated_at = ?")
        params_list.append(self._to_iso_string(datetime.now()))
        params_list.append(reminder_id)

        set_clause: str = ", ".join(update_fields)
        sql: str = f"UPDATE reminders SET {set_clause} WHERE id = ?"

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

    def update_reminder_status(self, reminder_id: int, status: str) -> bool:
        if status not in _VALID_REMINDER_STATUSES:
            return False
        return self.update_reminder(reminder_id, status=status)

    def get_pending_reminders(
        self, 
        before_time: Optional[Union[datetime, str]] = None
    ) -> List[ReminderData]:
        conn: Optional[sqlite3.Connection] = None
        query_parts: List[str] = ["SELECT * FROM reminders WHERE status = ?"]
        params_list: List[Any] = ["pending"]

        if before_time is not None:
            query_parts.append("AND reminder_time <= ?")
            params_list.append(self._to_iso_string(before_time))
        
        query_parts.append("ORDER BY reminder_time ASC")
        sql: str = " ".join(query_parts)

        try:
            conn = get_db_connection()
            cursor: sqlite3.Cursor = conn.cursor()
            rows: List[Dict[str, Any]] = db_operations.fetch_all_rows(cursor, sql, tuple(params_list))
            return [ReminderData(**row) for row in rows]
        except sqlite3.Error:
            return []
        finally:
            if conn:
                conn.close()

    def get_reminders_for_task(self, task_id: int) -> List[ReminderData]:
        conn: Optional[sqlite3.Connection] = None
        sql: str = "SELECT * FROM reminders WHERE task_id = ? ORDER BY reminder_time ASC"
        try:
            conn = get_db_connection()
            cursor: sqlite3.Cursor = conn.cursor()
            rows: List[Dict[str, Any]] = db_operations.fetch_all_rows(cursor, sql, (task_id,))
            return [ReminderData(**row) for row in rows]
        except sqlite3.Error:
            return []
        finally:
            if conn:
                conn.close()

    def get_reminders_for_event(self, event_id: int) -> List[ReminderData]:
        conn: Optional[sqlite3.Connection] = None
        sql: str = "SELECT * FROM reminders WHERE event_id = ? ORDER BY reminder_time ASC"
        try:
            conn = get_db_connection()
            cursor: sqlite3.Cursor = conn.cursor()
            rows: List[Dict[str, Any]] = db_operations.fetch_all_rows(cursor, sql, (event_id,))
            return [ReminderData(**row) for row in rows]
        except sqlite3.Error:
            return []
        finally:
            if conn:
                conn.close()

    def delete_reminder(self, reminder_id: int) -> bool:
        conn: Optional[sqlite3.Connection] = None
        sql: str = "DELETE FROM reminders WHERE id = ?"
        try:
            conn = get_db_connection()
            cursor: sqlite3.Cursor = conn.cursor()
            db_operations.run_write_statement(cursor, sql, (reminder_id,))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error:
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()

    def check_and_trigger_reminders(self) -> List[int]:
        now_iso: str = self._to_iso_string(datetime.now())
        due_reminders: List[ReminderData] = self.get_pending_reminders(before_time=now_iso)
        
        triggered_ids: List[int] = []
        if not due_reminders:
            return triggered_ids

        for reminder in due_reminders:
            success: bool = self.update_reminder_status(reminder["id"], "triggered")
            if success:
                triggered_ids.append(reminder["id"])
        
        return triggered_ids
