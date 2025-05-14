# src/core/project_manager.py
import sqlite3
from datetime import datetime
from typing import List, Optional, Dict, Any, TypedDict, Final, Set, Literal, Tuple, Union

from ..database import db_operations
from ..database.database_setup import get_db_connection

_SENTINEL = object()

class ProjectData(TypedDict):
    id: int
    name: str
    description: Optional[str]
    created_at: str
    updated_at: str

# Placeholder for TaskData, assuming it will be defined in task_manager.py
# and imported like: from .task_manager import TaskData
_TaskDataPlaceholder = Dict[str, Any]


_VALID_PROJECT_SORT_COLUMNS: Final[Set[str]] = {
    "id", "name", "created_at", "updated_at"
}
_DEFAULT_PROJECT_SORT_COLUMN: Final[str] = "created_at"
_VALID_SORT_ORDERS: Final[Set[Literal["ASC", "DESC"]]] = {"ASC", "DESC"} # Re-used
_DEFAULT_SORT_ORDER: Final[Literal["ASC", "DESC"]] = "ASC"


class ProjectManager:
    def __init__(self) -> None:
        pass

    def _to_iso_string(self, dt_object: datetime) -> str:
        return dt_object.isoformat(sep=" ", timespec="seconds")

    def add_project(
        self,
        name: str,
        description: Optional[str] = None
    ) -> Optional[int]:
        conn: Optional[sqlite3.Connection] = None
        now_iso: str = self._to_iso_string(datetime.now())
        sql: str = """
        INSERT INTO projects (name, description, created_at, updated_at)
        VALUES (?, ?, ?, ?)
        """
        params: Tuple[Any, ...] = (name, description, now_iso, now_iso)

        try:
            conn = get_db_connection()
            cursor: sqlite3.Cursor = conn.cursor()
            project_id: Optional[int] = db_operations.run_insert_statement(cursor, sql, params)
            conn.commit()
            return project_id
        except sqlite3.Error:
            if conn:
                conn.rollback()
            return None
        finally:
            if conn:
                conn.close()

    def get_project(self, project_id: int) -> Optional[ProjectData]:
        conn: Optional[sqlite3.Connection] = None
        sql: str = "SELECT id, name, description, created_at, updated_at FROM projects WHERE id = ?"
        try:
            conn = get_db_connection()
            cursor: sqlite3.Cursor = conn.cursor()
            row: Optional[Dict[str, Any]] = db_operations.fetch_single_row(cursor, sql, (project_id,))
            return ProjectData(**row) if row else None
        except sqlite3.Error:
            return None
        finally:
            if conn:
                conn.close()

    def get_all_projects(
        self,
        sort_by: str = _DEFAULT_PROJECT_SORT_COLUMN,
        sort_order: Literal["ASC", "DESC"] = _DEFAULT_SORT_ORDER
    ) -> List[ProjectData]:
        conn: Optional[sqlite3.Connection] = None
        
        actual_sort_by: str = sort_by if sort_by in _VALID_PROJECT_SORT_COLUMNS else _DEFAULT_PROJECT_SORT_COLUMN
        actual_sort_order: Literal["ASC", "DESC"] = sort_order if sort_order in _VALID_SORT_ORDERS else _DEFAULT_SORT_ORDER
        
        sql: str = f"SELECT id, name, description, created_at, updated_at FROM projects ORDER BY {actual_sort_by} {actual_sort_order}"
        
        try:
            conn = get_db_connection()
            cursor: sqlite3.Cursor = conn.cursor()
            rows: List[Dict[str, Any]] = db_operations.fetch_all_rows(cursor, sql)
            return [ProjectData(**row) for row in rows]
        except sqlite3.Error:
            return []
        finally:
            if conn:
                conn.close()

    def update_project(
        self,
        project_id: int,
        name: Union[str, object] = _SENTINEL,
        description: Union[Optional[str], object] = _SENTINEL
    ) -> bool:
        conn: Optional[sqlite3.Connection] = None
        
        update_fields: List[str] = []
        params_list: List[Any] = []

        if name is not _SENTINEL:
            if isinstance(name, str):
                update_fields.append("name = ?")
                params_list.append(name)
            else: # Name is NOT NULL, must be string if provided
                return False

        if description is not _SENTINEL:
            update_fields.append("description = ?")
            params_list.append(description) 
        
        if not update_fields:
            return True

        update_fields.append("updated_at = ?")
        params_list.append(self._to_iso_string(datetime.now()))
        params_list.append(project_id)

        set_clause: str = ", ".join(update_fields)
        sql: str = f"UPDATE projects SET {set_clause} WHERE id = ?"

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

    def delete_project(self, project_id: int) -> bool:
        conn: Optional[sqlite3.Connection] = None
        now_iso: str = self._to_iso_string(datetime.now())
        
        sql_update_tasks: str = "UPDATE tasks SET project_id = NULL, updated_at = ? WHERE project_id = ?"
        sql_update_notes: str = "UPDATE notes SET project_id = NULL, updated_at = ? WHERE project_id = ?"
        sql_delete_project: str = "DELETE FROM projects WHERE id = ?"
        
        delete_success: bool = False
        try:
            conn = get_db_connection()
            cursor: sqlite3.Cursor = conn.cursor()
            
            db_operations.run_write_statement(cursor, sql_update_tasks, (now_iso, project_id))
            db_operations.run_write_statement(cursor, sql_update_notes, (now_iso, project_id))
            db_operations.run_write_statement(cursor, sql_delete_project, (project_id,))
            delete_success = cursor.rowcount > 0 # Based on project deletion
            
            conn.commit()
            return delete_success
        except sqlite3.Error:
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()

    def get_tasks_for_project(self, project_id: int) -> List[_TaskDataPlaceholder]:
        from .task_manager import TaskManager # Local import
        task_mgr = TaskManager()
        # This assumes TaskManager.get_all_tasks will be refactored to support
        # project_id_filter and return an appropriate data structure (e.g. List[TaskData])
        return task_mgr.get_all_tasks(project_id_filter=project_id)
