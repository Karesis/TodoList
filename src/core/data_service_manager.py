# src/core/data_service_manager.py
import csv
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, List, Optional, Dict, Literal, Final, Set

from database import db_operations
from database.database_setup import get_db_connection, DATABASE_PATH

_ALLOWED_TABLE_OPERATIONS: Final[Set[str]] = {
    "tasks", "projects", "events", "goals", "notes", "tags",
    "task_tags", "reminders", "settings"
}

class DataServiceManager:
    _export_dir: Path
    _backup_dir: Path

    def __init__(
        self,
        export_base_dir: Optional[Path] = None,
        backup_base_dir: Optional[Path] = None
    ) -> None:
        home_path: Path = Path.home()
        app_data_root_name: str = "TimeManagerApp"

        default_exports_path: Path = home_path / app_data_root_name / "Exports"
        default_backups_path: Path = home_path / app_data_root_name / "Backups"

        self._export_dir = export_base_dir if export_base_dir else default_exports_path
        self._backup_dir = backup_base_dir if backup_base_dir else default_backups_path

        self._export_dir.mkdir(parents=True, exist_ok=True)
        self._backup_dir.mkdir(parents=True, exist_ok=True)

    def export_table_to_csv(self, table_name: str) -> Optional[Path]:
        if table_name not in _ALLOWED_TABLE_OPERATIONS:
            return None

        conn: Optional[sqlite3.Connection] = None
        try:
            conn = get_db_connection()
            cursor: sqlite3.Cursor = conn.cursor()
            query: str = f"SELECT * FROM {table_name}"
            rows: List[Dict[str, Any]] = db_operations.fetch_all_rows(cursor, query)

            if not rows:
                return None

            column_headers: List[str] = list(rows[0].keys())
            
            timestamp: str = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_name: str = f"{table_name}_export_{timestamp}.csv"
            file_path: Path = self._export_dir / file_name

            with open(file_path, "w", newline="", encoding="utf-8") as csv_file:
                writer = csv.writer(csv_file)
                writer.writerow(column_headers)
                for row_dict in rows:
                    writer.writerow([row_dict.get(header) for header in column_headers])
            
            return file_path
        except (sqlite3.Error, IOError, IndexError):
            return None
        finally:
            if conn:
                conn.close()

    def export_all_data_to_json(self) -> Optional[Path]:
        all_database_data: Dict[str, List[Dict[str, Any]]] = {}
        conn: Optional[sqlite3.Connection] = None
        try:
            conn = get_db_connection()
            cursor: sqlite3.Cursor = conn.cursor()
            
            tables_query: str = "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';"
            cursor.execute(tables_query)
            table_rows_raw: List[sqlite3.Row] = cursor.fetchall()
            table_names: List[str] = [row["name"] for row in table_rows_raw]

            for table_name in table_names:
                data_query: str = f"SELECT * FROM {table_name}"
                table_content: List[Dict[str, Any]] = db_operations.fetch_all_rows(cursor, data_query)
                all_database_data[table_name] = table_content
            
            if not all_database_data:
                return None

            timestamp: str = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_name: str = f"full_database_export_{timestamp}.json"
            file_path: Path = self._export_dir / file_name

            with open(file_path, "w", encoding="utf-8") as json_file:
                json.dump(all_database_data, json_file, indent=4, ensure_ascii=False)
            
            return file_path
        except (sqlite3.Error, IOError):
            return None
        finally:
            if conn:
                conn.close()

    def import_data_from_csv(
        self,
        table_name: str,
        file_path: Path,
        strategy: Literal["append", "replace"] = "append"
    ) -> bool:
        if table_name not in _ALLOWED_TABLE_OPERATIONS:
            return False
        if not file_path.exists() or not file_path.is_file():
            return False

        conn: Optional[sqlite3.Connection] = None
        try:
            conn = get_db_connection()
            cursor: sqlite3.Cursor = conn.cursor()

            if strategy == "replace":
                delete_statement: str = f"DELETE FROM {table_name}"
                db_operations.run_write_statement(cursor, delete_statement)
            
            with open(file_path, "r", newline="", encoding="utf-8") as csv_file:
                reader = csv.reader(csv_file)
                try:
                    header: List[str] = next(reader)
                except StopIteration:
                    if strategy == "replace": conn.rollback()
                    return False 

                if not header:
                    if strategy == "replace": conn.rollback()
                    return False
                
                placeholders: str = ", ".join(["?"] * len(header))
                insert_statement: str = f"INSERT INTO {table_name} ({', '.join(header)}) VALUES ({placeholders})"
                
                imported_row_count: int = 0
                for row_values in reader:
                    if len(row_values) != len(header):
                        continue 
                    
                    processed_row_values: List[Optional[str]] = [
                        None if val == "" else val for val in row_values
                    ]
                    try:
                        db_operations.run_write_statement(cursor, insert_statement, tuple(processed_row_values))
                        imported_row_count += 1
                    except sqlite3.IntegrityError:
                        continue 
            
            conn.commit()
            return True if strategy == "replace" or imported_row_count > 0 else False
        except (sqlite3.Error, IOError, csv.Error):
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()

    def backup_database(self) -> Optional[Path]:
        timestamp: str = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file_name: str = f"timemanager_backup_{timestamp}.db"
        backup_file_path: Path = self._backup_dir / backup_file_name

        source_db_conn: Optional[sqlite3.Connection] = None
        backup_target_db_conn: Optional[sqlite3.Connection] = None
        try:
            source_db_conn = sqlite3.connect(str(DATABASE_PATH))
            backup_target_db_conn = sqlite3.connect(str(backup_file_path))
            source_db_conn.backup(backup_target_db_conn)
            return backup_file_path
        except sqlite3.Error:
            if backup_file_path.exists():
                try:
                    backup_file_path.unlink(missing_ok=True)
                except OSError:
                    pass
            return None
        finally:
            if source_db_conn:
                source_db_conn.close()
            if backup_target_db_conn:
                backup_target_db_conn.close()

    def restore_database(self, backup_file_path: Path) -> bool:
        if not backup_file_path.exists() or not backup_file_path.is_file():
            return False

        backup_source_db_conn: Optional[sqlite3.Connection] = None
        main_db_target_conn: Optional[sqlite3.Connection] = None
        
        try:
            backup_source_db_conn = sqlite3.connect(str(backup_file_path))
            main_db_target_conn = sqlite3.connect(str(DATABASE_PATH))
            backup_source_db_conn.backup(main_db_target_conn)
            return True
        except sqlite3.Error:
            return False
        finally:
            if backup_source_db_conn:
                backup_source_db_conn.close()
            if main_db_target_conn:
                main_db_target_conn.close()
