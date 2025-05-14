# src/core/schedule_manager.py
import sqlite3
from datetime import datetime
from typing import List, Optional, Dict, Any, TypedDict, Final, Set, Literal, Tuple, Union

from ..database import db_operations
from ..database.database_setup import get_db_connection

_SENTINEL = object()

class EventData(TypedDict):
    id: int
    title: str
    description: Optional[str]
    start_time: str
    end_time: str
    location: Optional[str]
    is_all_day: int 
    recurrence_rule: Optional[str]
    created_at: str
    updated_at: str

_VALID_EVENT_SORT_COLUMNS: Final[Set[str]] = {
    "id", "title", "start_time", "end_time", "created_at", "updated_at"
}
_DEFAULT_EVENT_SORT_COLUMN: Final[str] = "start_time"
_VALID_SORT_ORDERS: Final[Set[Literal["ASC", "DESC"]]] = {"ASC", "DESC"}
_DEFAULT_SORT_ORDER: Final[Literal["ASC", "DESC"]] = "ASC"
_VALID_BOOLEAN_INT_VALUES: Final[Set[int]] = {0, 1}


class ScheduleManager:
    def __init__(self) -> None:
        pass

    def _to_iso_string(self, dt_object: Union[datetime, str]) -> str:
        if isinstance(dt_object, datetime):
            return dt_object.isoformat(sep=" ", timespec="seconds")
        return dt_object

    def add_event(
        self,
        title: str,
        start_time: Union[datetime, str],
        end_time: Union[datetime, str],
        description: Optional[str] = None,
        location: Optional[str] = None,
        is_all_day: int = 0,
        recurrence_rule: Optional[str] = None
    ) -> Optional[int]:
        if is_all_day not in _VALID_BOOLEAN_INT_VALUES:
            return None

        conn: Optional[sqlite3.Connection] = None
        now_iso: str = self._to_iso_string(datetime.now())
        start_time_iso: str = self._to_iso_string(start_time)
        end_time_iso: str = self._to_iso_string(end_time)

        sql: str = """
        INSERT INTO events 
            (title, description, start_time, end_time, location, 
             is_all_day, recurrence_rule, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params: Tuple[Any, ...] = (
            title, description, start_time_iso, end_time_iso, location,
            is_all_day, recurrence_rule, now_iso, now_iso
        )

        try:
            conn = get_db_connection()
            cursor: sqlite3.Cursor = conn.cursor()
            event_id: Optional[int] = db_operations.run_insert_statement(cursor, sql, params)
            conn.commit()
            return event_id
        except sqlite3.Error:
            if conn:
                conn.rollback()
            return None
        finally:
            if conn:
                conn.close()

    def get_event(self, event_id: int) -> Optional[EventData]:
        conn: Optional[sqlite3.Connection] = None
        sql: str = "SELECT * FROM events WHERE id = ?"
        try:
            conn = get_db_connection()
            cursor: sqlite3.Cursor = conn.cursor()
            row: Optional[Dict[str, Any]] = db_operations.fetch_single_row(cursor, sql, (event_id,))
            return EventData(**row) if row else None
        except sqlite3.Error:
            return None
        finally:
            if conn:
                conn.close()

    def get_all_events(
        self,
        sort_by: str = _DEFAULT_EVENT_SORT_COLUMN,
        sort_order: Literal["ASC", "DESC"] = _DEFAULT_SORT_ORDER
    ) -> List[EventData]:
        conn: Optional[sqlite3.Connection] = None
        actual_sort_by: str = sort_by if sort_by in _VALID_EVENT_SORT_COLUMNS else _DEFAULT_EVENT_SORT_COLUMN
        actual_sort_order: Literal["ASC", "DESC"] = sort_order if sort_order in _VALID_SORT_ORDERS else _DEFAULT_SORT_ORDER
        
        sql: str = f"SELECT * FROM events ORDER BY {actual_sort_by} {actual_sort_order}"
        
        try:
            conn = get_db_connection()
            cursor: sqlite3.Cursor = conn.cursor()
            rows: List[Dict[str, Any]] = db_operations.fetch_all_rows(cursor, sql)
            return [EventData(**row) for row in rows]
        except sqlite3.Error:
            return []
        finally:
            if conn:
                conn.close()

    def get_events_for_period(
        self,
        period_start_time: Union[datetime, str],
        period_end_time: Union[datetime, str],
        sort_by: str = _DEFAULT_EVENT_SORT_COLUMN,
        sort_order: Literal["ASC", "DESC"] = _DEFAULT_SORT_ORDER
    ) -> List[EventData]:
        conn: Optional[sqlite3.Connection] = None
        period_start_iso: str = self._to_iso_string(period_start_time)
        period_end_iso: str = self._to_iso_string(period_end_time)

        sql_select_part: str = "SELECT * FROM events"
        sql_where_part: str = "WHERE start_time <= ? AND end_time >= ?"
        params_list: List[Any] = [period_end_iso, period_start_iso]

        actual_sort_by: str = sort_by if sort_by in _VALID_EVENT_SORT_COLUMNS else _DEFAULT_EVENT_SORT_COLUMN
        actual_sort_order: Literal["ASC", "DESC"] = sort_order if sort_order in _VALID_SORT_ORDERS else _DEFAULT_SORT_ORDER
        sql_order_part: str = f"ORDER BY {actual_sort_by} {actual_sort_order}"
        
        sql: str = f"{sql_select_part} {sql_where_part} {sql_order_part}"
        
        try:
            conn = get_db_connection()
            cursor: sqlite3.Cursor = conn.cursor()
            rows: List[Dict[str, Any]] = db_operations.fetch_all_rows(cursor, sql, tuple(params_list))
            return [EventData(**row) for row in rows]
        except sqlite3.Error:
            return []
        finally:
            if conn:
                conn.close()

    def update_event(
        self,
        event_id: int,
        title: Union[str, object] = _SENTINEL,
        description: Union[Optional[str], object] = _SENTINEL,
        start_time: Union[datetime, str, object] = _SENTINEL,
        end_time: Union[datetime, str, object] = _SENTINEL,
        location: Union[Optional[str], object] = _SENTINEL,
        is_all_day: Union[int, object] = _SENTINEL,
        recurrence_rule: Union[Optional[str], object] = _SENTINEL
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
        if start_time is not _SENTINEL:
            update_fields.append("start_time = ?")
            params_list.append(self._to_iso_string(start_time)) # type: ignore[arg-type]
        if end_time is not _SENTINEL:
            update_fields.append("end_time = ?")
            params_list.append(self._to_iso_string(end_time)) # type: ignore[arg-type]
        if location is not _SENTINEL:
            update_fields.append("location = ?")
            params_list.append(location)
        if is_all_day is not _SENTINEL:
            if isinstance(is_all_day, int) and is_all_day in _VALID_BOOLEAN_INT_VALUES:
                update_fields.append("is_all_day = ?")
                params_list.append(is_all_day)
            else:
                return False
        if recurrence_rule is not _SENTINEL:
            update_fields.append("recurrence_rule = ?")
            params_list.append(recurrence_rule)

        if not update_fields:
            return True

        update_fields.append("updated_at = ?")
        params_list.append(self._to_iso_string(datetime.now()))
        params_list.append(event_id)

        set_clause: str = ", ".join(update_fields)
        sql: str = f"UPDATE events SET {set_clause} WHERE id = ?"

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

    def delete_event(self, event_id: int) -> bool:
        conn: Optional[sqlite3.Connection] = None
        sql: str = "DELETE FROM events WHERE id = ?"
        try:
            conn = get_db_connection()
            cursor: sqlite3.Cursor = conn.cursor()
            db_operations.run_write_statement(cursor, sql, (event_id,))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error:
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()
