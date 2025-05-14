# src/ui/views/task_view.py
import sqlite3
from datetime import datetime
from typing import List, Optional, Dict, Any, cast, Final, Set, Union

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTextEdit,
    QDialog, QDialogButtonBox, QFormLayout, QComboBox, QMessageBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView
)
from PyQt6.QtCore import Qt, QDateTime
from PyQt6.QtGui import QFont

from ...core import TaskManager
from ...core.task_manager import TaskData, _VALID_TASK_STATUSES, _VALID_TASK_PRIORITIES

_SENTINEL = object()

# UI Display mappings
_TASK_PRIORITY_MAP_DB_TO_DISPLAY: Final[Dict[int, str]] = {
    0: "Low", 1: "Medium", 2: "High"
}
_TASK_PRIORITY_MAP_DISPLAY_TO_DB: Final[Dict[str, int]] = {
    "Low (0)": 0, "Medium (1)": 1, "High (2)": 2
}

_TASK_STATUS_MAP_DB_TO_DISPLAY: Final[Dict[str, str]] = {
    "pending": "Pending",
    "in_progress": "In Progress",
    "completed": "Completed",
    "cancelled": "Cancelled"
}
_TASK_STATUS_MAP_DISPLAY_TO_DB: Final[Dict[str, str]] = {
    v: k for k, v in _TASK_STATUS_MAP_DB_TO_DISPLAY.items()
}


class TaskView(QWidget):
    task_manager: TaskManager
    add_task_button: QPushButton
    task_table: QTableWidget

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.task_manager = TaskManager()
        self._init_ui()

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        title_label = QLabel("Task Management")
        font = title_label.font()
        font.setPointSize(24)
        font.setBold(True)
        title_label.setFont(font)
        title_label.setStyleSheet("margin-bottom: 10px;")
        main_layout.addWidget(title_label)

        action_layout = QHBoxLayout()
        self.add_task_button = QPushButton(" Add New Task")
        self.add_task_button.clicked.connect(self._show_add_task_dialog)
        action_layout.addWidget(self.add_task_button)
        action_layout.addStretch()
        main_layout.addLayout(action_layout)

        self.task_table = QTableWidget()
        self.task_table.setColumnCount(6)
        self.task_table.setHorizontalHeaderLabels(["ID", "Title", "Priority", "Due Date", "Status", "Actions"])
        self.task_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch) # Title column
        self.task_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.task_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.task_table.setAlternatingRowColors(True)
        main_layout.addWidget(self.task_table)

        self.setLayout(main_layout)
        self.refresh_view_content()

    def refresh_view_content(self) -> None:
        self.task_table.setRowCount(0)
        try:
            tasks: List[TaskData] = self.task_manager.get_all_tasks()
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"Failed to load tasks: {e}")
            tasks = []

        for row_idx, task in enumerate(tasks):
            self.task_table.insertRow(row_idx)
            self.task_table.setItem(row_idx, 0, QTableWidgetItem(str(task["id"])))
            self.task_table.setItem(row_idx, 1, QTableWidgetItem(task["title"]))
            
            priority_display = _TASK_PRIORITY_MAP_DB_TO_DISPLAY.get(task["priority"], "Unknown")
            self.task_table.setItem(row_idx, 2, QTableWidgetItem(priority_display))
            
            due_date_str: Optional[str] = task.get("due_date")
            display_due_date: str = "-"
            if due_date_str:
                try:
                    dt_obj = QDateTime.fromString(due_date_str, "yyyy-MM-dd HH:mm:ss")
                    if not dt_obj.isValid():
                         dt_obj = QDateTime.fromString(due_date_str, Qt.DateFormat.ISODate)
                    if not dt_obj.isValid(): # Try date part only if full datetime fails
                         dt_obj = QDateTime.fromString(due_date_str.split(" ")[0], "yyyy-MM-dd")
                    display_due_date = dt_obj.toString("yyyy-MM-dd HH:mm") if dt_obj.isValid() else due_date_str
                except Exception:
                    display_due_date = due_date_str 
            self.task_table.setItem(row_idx, 3, QTableWidgetItem(display_due_date))
            
            status_display = _TASK_STATUS_MAP_DB_TO_DISPLAY.get(task["status"], task["status"])
            self.task_table.setItem(row_idx, 4, QTableWidgetItem(status_display))
            
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(0,0,0,0)
            actions_layout.setSpacing(5)

            edit_button = QPushButton("Edit")
            edit_button.setProperty("task_id", task["id"])
            edit_button.clicked.connect(self._show_edit_task_dialog)
            actions_layout.addWidget(edit_button)

            delete_button = QPushButton("Delete")
            delete_button.setProperty("task_id", task["id"])
            delete_button.clicked.connect(self._confirm_delete_task)
            actions_layout.addWidget(delete_button)
            
            actions_layout.addStretch()
            self.task_table.setCellWidget(row_idx, 5, actions_widget)

        self.task_table.resizeColumnsToContents()
        self.task_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        if self.task_table.columnCount() > 5:
            self.task_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)


    def _show_add_task_dialog(self) -> None:
        dialog = TaskDialog(parent=self)
        if dialog.exec():
            task_input_data: Dict[str, Any] = dialog.get_task_input_data()
            try:
                new_task_id: Optional[int] = self.task_manager.add_task(**task_input_data)
                if new_task_id is not None:
                    QMessageBox.information(self, "Success", f"Task '{task_input_data['title']}' added.")
                    self.refresh_view_content()
                else:
                    QMessageBox.warning(self, "Failed", "Failed to add task.")
            except sqlite3.Error as e:
                QMessageBox.critical(self, "Database Error", f"Error adding task: {e}")
            except Exception as e:
                QMessageBox.critical(self, "Application Error", f"An unexpected error occurred: {e}")

    def _show_edit_task_dialog(self) -> None:
        sender_button = self.sender()
        if not isinstance(sender_button, QPushButton): return
        
        task_id_any: Any = sender_button.property("task_id")
        if task_id_any is None: return
        task_id = int(task_id_any)

        try:
            current_task_data: Optional[TaskData] = self.task_manager.get_task(task_id)
            if not current_task_data:
                QMessageBox.warning(self, "Error", f"Task ID {task_id} not found.")
                self.refresh_view_content() # Refresh if task was deleted elsewhere
                return
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"Failed to load task data: {e}")
            return

        dialog = TaskDialog(parent=self, existing_task_data=current_task_data)
        if dialog.exec():
            updated_task_data: Dict[str, Any] = dialog.get_task_input_data()
            try:
                success: bool = self.task_manager.update_task(task_id, **updated_task_data)
                if success:
                    QMessageBox.information(self, "Success", f"Task ID {task_id} updated.")
                    self.refresh_view_content()
                else:
                    QMessageBox.warning(self, "Failed", f"Failed to update Task ID {task_id}.")
            except sqlite3.Error as e:
                QMessageBox.critical(self, "Database Error", f"Error updating task: {e}")
            except Exception as e:
                 QMessageBox.critical(self, "Application Error", f"An unexpected error occurred: {e}")

    def _confirm_delete_task(self) -> None:
        sender_button = self.sender()
        if not isinstance(sender_button, QPushButton): return

        task_id_any: Any = sender_button.property("task_id")
        if task_id_any is None: return
        task_id = int(task_id_any)

        reply: QMessageBox.StandardButton = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to delete Task ID {task_id}? This action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                success: bool = self.task_manager.delete_task(task_id)
                if success:
                    QMessageBox.information(self, "Success", f"Task ID {task_id} deleted.")
                    self.refresh_view_content()
                else:
                    QMessageBox.warning(self, "Failed", f"Failed to delete Task ID {task_id}.")
            except sqlite3.Error as e:
                QMessageBox.critical(self, "Database Error", f"Error deleting task: {e}")
            except Exception as e:
                 QMessageBox.critical(self, "Application Error", f"An unexpected error occurred: {e}")


class TaskDialog(QDialog):
    title_edit: QLineEdit
    description_edit: QTextEdit
    priority_combo: QComboBox
    due_date_edit: QLineEdit
    status_combo: QComboBox
    project_id_edit: QLineEdit
    # parent_task_id_edit: QLineEdit # Not implemented in this dialog UI

    _existing_task_data: Optional[TaskData]

    def __init__(self, parent: Optional[QWidget] = None, existing_task_data: Optional[TaskData] = None) -> None:
        super().__init__(parent)
        self._existing_task_data = existing_task_data
        self.setWindowTitle("Edit Task" if existing_task_data else "Add New Task")
        self.setMinimumWidth(450)
        self._init_ui()
        if existing_task_data:
            self._populate_fields(existing_task_data)

    def _init_ui(self) -> None:
        layout = QFormLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        self.title_edit = QLineEdit()
        self.description_edit = QTextEdit()
        self.description_edit.setFixedHeight(100)
        
        self.priority_combo = QComboBox()
        self.priority_combo.addItems(list(_TASK_PRIORITY_MAP_DISPLAY_TO_DB.keys()))
        
        self.due_date_edit = QLineEdit()
        self.due_date_edit.setPlaceholderText("YYYY-MM-DD HH:MM:SS or YYYY-MM-DD (Optional)")
        
        self.status_combo = QComboBox()
        self.status_combo.addItems(list(_TASK_STATUS_MAP_DISPLAY_TO_DB.keys()))
        
        self.project_id_edit = QLineEdit()
        self.project_id_edit.setPlaceholderText("Optional Project ID (number)")

        layout.addRow("Title:", self.title_edit)
        layout.addRow("Description:", self.description_edit)
        layout.addRow("Priority:", self.priority_combo)
        layout.addRow("Due Date:", self.due_date_edit)
        layout.addRow("Status:", self.status_combo)
        layout.addRow("Project ID:", self.project_id_edit)

        self.button_box = QDialogButtonBox()
        self.button_box.addButton(QDialogButtonBox.StandardButton.Ok)
        self.button_box.addButton(QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self._validate_and_accept)
        self.button_box.rejected.connect(self.reject)
        layout.addRow(self.button_box)

    def _populate_fields(self, task_data: TaskData) -> None:
        self.title_edit.setText(task_data.get("title", ""))
        self.description_edit.setPlainText(task_data.get("description", ""))
        
        priority_val: int = task_data.get("priority", 0)
        for display_text, db_val in _TASK_PRIORITY_MAP_DISPLAY_TO_DB.items():
            if db_val == priority_val:
                self.priority_combo.setCurrentText(display_text)
                break
        
        self.due_date_edit.setText(task_data.get("due_date", ""))
        
        status_val: str = task_data.get("status", "pending")
        for display_text, db_val in _TASK_STATUS_MAP_DISPLAY_TO_DB.items():
            if db_val == status_val:
                self.status_combo.setCurrentText(display_text)
                break
                
        project_id_val = task_data.get("project_id")
        self.project_id_edit.setText(str(project_id_val) if project_id_val is not None else "")

    def _validate_and_accept(self) -> None:
        if not self.title_edit.text().strip():
            QMessageBox.warning(self, "Input Error", "Task title cannot be empty.")
            return
        
        due_date_str: str = self.due_date_edit.text().strip()
        if due_date_str:
            try:
                # Attempt to parse to validate format, but send string to manager
                datetime.strptime(due_date_str, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                try:
                    datetime.strptime(due_date_str, "%Y-%m-%d")
                except ValueError:
                    QMessageBox.warning(self, "Input Error", 
                                        "Due date format is invalid. Use YYYY-MM-DD HH:MM:SS or YYYY-MM-DD.")
                    return
        
        project_id_str: str = self.project_id_edit.text().strip()
        if project_id_str and not project_id_str.isdigit():
            QMessageBox.warning(self, "Input Error", "Project ID must be a number if provided.")
            return

        self.accept()

    def get_task_input_data(self) -> Dict[str, Any]:
        priority_display: str = self.priority_combo.currentText()
        status_display: str = self.status_combo.currentText()

        due_date_val: Optional[str] = self.due_date_edit.text().strip() or None
        
        project_id_str: str = self.project_id_edit.text().strip()
        project_id_val: Optional[int] = int(project_id_str) if project_id_str.isdigit() else None

        return {
            "title": self.title_edit.text().strip(),
            "description": self.description_edit.toPlainText().strip() or None,
            "priority": _TASK_PRIORITY_MAP_DISPLAY_TO_DB.get(priority_display, 0),
            "due_date": due_date_val,
            "status": _TASK_STATUS_MAP_DISPLAY_TO_DB.get(status_display, "pending"),
            "project_id": project_id_val,
            "parent_task_id": None # Not implemented in this dialog's UI
        }
