# src/ui/views/project_view.py
import sqlite3
from datetime import datetime
from typing import List, Optional, Dict, Any, cast

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTextEdit,
    QDialog, QDialogButtonBox, QFormLayout, QMessageBox,
    QTreeWidget, QTreeWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt, QDateTime
from PyQt6.QtGui import QFont

from core import ProjectManager, TaskManager
from core.project_manager import ProjectData
# Placeholder for TaskData, assuming it will be defined in task_manager.py
# and imported like: from ...core.task_manager import TaskData
_TaskDataPlaceholder = Dict[str, Any] # Using this until TaskData is formally available

_SENTINEL = object()

class ProjectView(QWidget):
    project_manager: ProjectManager
    task_manager: TaskManager # For fetching tasks under projects
    add_project_button: QPushButton
    project_tree_widget: QTreeWidget

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.project_manager = ProjectManager()
        self.task_manager = TaskManager()
        self._init_ui()

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        title_label = QLabel("Project Management")
        font = title_label.font()
        font.setPointSize(24)
        font.setBold(True)
        title_label.setFont(font)
        title_label.setStyleSheet("margin-bottom: 10px;")
        main_layout.addWidget(title_label)

        action_layout = QHBoxLayout()
        self.add_project_button = QPushButton(" Add New Project")
        self.add_project_button.clicked.connect(self._show_add_project_dialog)
        action_layout.addWidget(self.add_project_button)
        action_layout.addStretch()
        main_layout.addLayout(action_layout)

        self.project_tree_widget = QTreeWidget()
        self.project_tree_widget.setHeaderLabels(["Name", "Status / Type", "Due Date"])
        self.project_tree_widget.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.project_tree_widget.header().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.project_tree_widget.header().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.project_tree_widget.itemDoubleClicked.connect(self._handle_item_double_click)
        main_layout.addWidget(self.project_tree_widget)

        self.setLayout(main_layout)
        self.refresh_view_content()

    def refresh_view_content(self) -> None:
        self.project_tree_widget.clear()
        try:
            projects: List[ProjectData] = self.project_manager.get_all_projects(sort_by="name")
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"Failed to load projects: {e}")
            projects = []

        task_status_map: Dict[str, str] = {
            "pending": "Pending", "in_progress": "In Progress", 
            "completed": "Completed", "cancelled": "Cancelled"
        }

        for project in projects:
            project_item = QTreeWidgetItem(self.project_tree_widget)
            project_item.setText(0, project["name"])
            project_item.setText(1, "Project") # Type identifier
            project_item.setData(0, Qt.ItemDataRole.UserRole, {"type": "project", "data": project})
            project_item.setExpanded(True)

            try:
                # Assuming TaskManager's get_all_tasks can filter by project_id
                # and will return List[_TaskDataPlaceholder] or eventually List[TaskData]
                tasks_for_project: List[_TaskDataPlaceholder] = \
                    self.task_manager.get_all_tasks(project_id_filter=project["id"])
            except sqlite3.Error as e:
                tasks_for_project = []
                error_item = QTreeWidgetItem(project_item)
                error_item.setText(0, f"Error loading tasks: {e}")
                error_item.setDisabled(True)
            
            for task in tasks_for_project:
                task_item = QTreeWidgetItem(project_item)
                task_item.setText(0, task.get("title", "Untitled Task"))
                task_item.setText(1, task_status_map.get(task.get("status", ""), task.get("status", "")))
                
                due_date_str: Optional[str] = task.get("due_date")
                display_due_date: str = "-"
                if due_date_str:
                    try:
                        dt_obj = QDateTime.fromString(due_date_str, "yyyy-MM-dd HH:mm:ss")
                        if not dt_obj.isValid():
                             dt_obj = QDateTime.fromString(due_date_str, Qt.DateFormat.ISODate) # Try full ISO
                        if not dt_obj.isValid():
                             dt_obj = QDateTime.fromString(due_date_str.split(" ")[0], "yyyy-MM-dd") # Try date part only

                        display_due_date = dt_obj.toString("yyyy-MM-dd HH:mm") if dt_obj.isValid() else due_date_str
                    except Exception:
                        display_due_date = due_date_str
                task_item.setText(2, display_due_date)
                task_item.setData(0, Qt.ItemDataRole.UserRole, {"type": "task", "data": task})
        
        for i in range(self.project_tree_widget.columnCount()):
             self.project_tree_widget.resizeColumnToContents(i)
        self.project_tree_widget.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)


    def _handle_item_double_click(self, item: QTreeWidgetItem, column: int) -> None:
        item_info: Optional[Any] = item.data(0, Qt.ItemDataRole.UserRole)
        if not item_info or not isinstance(item_info, dict):
            return
        
        item_type: Optional[str] = item_info.get("type")
        item_data: Optional[Dict[str, Any]] = item_info.get("data")

        if not item_data:
            return

        if item_type == "project":
            self._show_edit_project_dialog(cast(ProjectData, item_data))
        elif item_type == "task":
            # For now, show read-only details. Editing tasks might involve TaskDialog from task_view.
            QMessageBox.information(self, "Task Details", 
                                   f"Task: {item_data.get('title')}\n"
                                   f"Status: {item_data.get('status')}\n"
                                   f"Due: {item_data.get('due_date', '-')}")

    def _show_add_project_dialog(self) -> None:
        dialog = ProjectDialog(parent=self)
        if dialog.exec():
            project_input_data: Dict[str, Any] = dialog.get_project_input_data()
            try:
                new_project_id: Optional[int] = self.project_manager.add_project(
                    name=project_input_data["name"],
                    description=project_input_data.get("description")
                )
                if new_project_id is not None:
                    QMessageBox.information(self, "Success", f"Project '{project_input_data['name']}' added.")
                    self.refresh_view_content()
                else:
                    QMessageBox.warning(self, "Failed", "Failed to add project.")
            except sqlite3.Error as e:
                QMessageBox.critical(self, "Database Error", f"Error adding project: {e}")
            except Exception as e:
                QMessageBox.critical(self, "Application Error", f"An unexpected error occurred: {e}")

    def _show_edit_project_dialog(self, project_to_edit: ProjectData) -> None:
        project_id: int = project_to_edit["id"]
        
        try:
            current_project_data: Optional[ProjectData] = self.project_manager.get_project(project_id)
            if not current_project_data:
                QMessageBox.warning(self, "Error", f"Could not find Project ID {project_id}.")
                self.refresh_view_content()
                return
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"Failed to load project data: {e}")
            return

        dialog = ProjectDialog(parent=self, existing_project_data=current_project_data)
        if dialog.exec():
            updated_project_input_data: Dict[str, Any] = dialog.get_project_input_data()
            try:
                update_kwargs: Dict[str, Any] = {}
                if "name" in updated_project_input_data:
                    update_kwargs["name"] = updated_project_input_data["name"]
                if "description" in updated_project_input_data: # description is optional
                    update_kwargs["description"] = updated_project_input_data.get("description")

                success: bool = self.project_manager.update_project(project_id, **update_kwargs)
                if success:
                    QMessageBox.information(self, "Success", f"Project ID {project_id} updated.")
                    self.refresh_view_content()
                else:
                    QMessageBox.warning(self, "Failed", f"Failed to update Project ID {project_id}.")
            except sqlite3.Error as e:
                QMessageBox.critical(self, "Database Error", f"Error updating project: {e}")
            except Exception as e:
                QMessageBox.critical(self, "Application Error", f"An unexpected error occurred: {e}")


class ProjectDialog(QDialog):
    name_edit: QLineEdit
    description_edit: QTextEdit
    _existing_project_data: Optional[ProjectData]

    def __init__(self, parent: Optional[QWidget] = None, existing_project_data: Optional[ProjectData] = None) -> None:
        super().__init__(parent)
        self._existing_project_data = existing_project_data
        self.setWindowTitle("Edit Project" if existing_project_data else "Add New Project")
        self.setMinimumWidth(400)
        self._init_ui()
        if existing_project_data:
            self._populate_fields(existing_project_data)

    def _init_ui(self) -> None:
        layout = QFormLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        self.name_edit = QLineEdit()
        self.description_edit = QTextEdit()
        self.description_edit.setFixedHeight(100)

        layout.addRow("Project Name:", self.name_edit)
        layout.addRow("Description:", self.description_edit)

        self.button_box = QDialogButtonBox()
        self.button_box.addButton(QDialogButtonBox.StandardButton.Ok)
        self.button_box.addButton(QDialogButtonBox.StandardButton.Cancel)
        
        if self._existing_project_data:
            delete_button = self.button_box.addButton("Delete", QDialogButtonBox.ButtonRole.DestructiveRole)
            delete_button.clicked.connect(self._confirm_delete_project)
            
        self.button_box.accepted.connect(self._validate_and_accept)
        self.button_box.rejected.connect(self.reject)
        layout.addRow(self.button_box)

    def _populate_fields(self, project_data: ProjectData) -> None:
        self.name_edit.setText(project_data.get("name", ""))
        self.description_edit.setPlainText(project_data.get("description", ""))

    def _validate_and_accept(self) -> None:
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "Input Error", "Project name cannot be empty.")
            return
        self.accept()

    def _confirm_delete_project(self) -> None:
        if not self._existing_project_data:
            return

        project_id: int = self._existing_project_data["id"]
        project_name: str = self._existing_project_data.get("name", "Untitled Project")
        
        reply: QMessageBox.StandardButton = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete project \"{project_name}\" (ID: {project_id})?\n"
            f"This action will also update related tasks and notes, and cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            parent_view = cast(ProjectView, self.parent())
            try:
                success: bool = parent_view.project_manager.delete_project(project_id)
                if success:
                    QMessageBox.information(parent_view, "Success", f"Project ID {project_id} deleted.")
                    parent_view.refresh_view_content()
                    self.done(QDialog.DialogCode.Accepted)
                else:
                    QMessageBox.warning(parent_view, "Failed", f"Failed to delete Project ID {project_id}.")
            except sqlite3.Error as e:
                QMessageBox.critical(parent_view, "Database Error", f"Error deleting project: {e}")
            except Exception as e:
                 QMessageBox.critical(parent_view, "Application Error", f"An unexpected error occurred: {e}")


    def get_project_input_data(self) -> Dict[str, Any]:
        return {
            "name": self.name_edit.text().strip(),
            "description": self.description_edit.toPlainText().strip() or None,
        }
