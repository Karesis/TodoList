# src/ui/views/note_view.py
import sqlite3
from datetime import datetime
from typing import List, Optional, Dict, Any, cast

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QLineEdit, QTextEdit,
    QDialog, QDialogButtonBox, QFormLayout, QMessageBox
)
from PyQt6.QtCore import Qt, QDateTime # QDateTime for parsing ISO strings
from PyQt6.QtGui import QFont

from ...core import NoteManager # Use __init__.py for core imports
from ...core.note_manager import NoteData # Import TypedDict

# Sentinel for distinguishing "not provided" from "None" in updates
_SENTINEL = object()


class NoteView(QWidget):
    note_manager: NoteManager
    add_note_button: QPushButton
    notes_list_widget: QListWidget

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.note_manager = NoteManager()
        self._init_ui()

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        title_label = QLabel("Notes")
        font = title_label.font()
        font.setPointSize(24)
        font.setBold(True)
        title_label.setFont(font)
        title_label.setStyleSheet("margin-bottom: 10px;")
        main_layout.addWidget(title_label)

        action_layout = QHBoxLayout()
        self.add_note_button = QPushButton(" Add New Note")
        # self.add_note_button.setStyleSheet("padding: 8px 15px; font-size: 14px;") # Prefer QSS
        self.add_note_button.clicked.connect(self._show_add_note_dialog)
        action_layout.addWidget(self.add_note_button)
        action_layout.addStretch()
        main_layout.addLayout(action_layout)

        self.notes_list_widget = QListWidget()
        # self.notes_list_widget.setStyleSheet("font-size: 14px; border: 1px solid #e0e0e0;") # Prefer QSS
        self.notes_list_widget.itemDoubleClicked.connect(self._handle_note_item_double_click)
        main_layout.addWidget(self.notes_list_widget)

        self.setLayout(main_layout)
        self.refresh_view_content()

    def refresh_view_content(self) -> None:
        self.notes_list_widget.clear()
        try:
            notes: List[NoteData] = self.note_manager.get_all_notes(sort_by="updated_at", sort_order="DESC")
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"Failed to load notes: {e}")
            notes = []

        if not notes:
            no_note_item = QListWidgetItem("No notes available.")
            no_note_item.setFlags(no_note_item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            self.notes_list_widget.addItem(no_note_item)
        else:
            for note in notes:
                title: str = note.get("title") or "Untitled Note"
                created_at_str: str = note.get("created_at", "")
                display_created_at: str = "Unknown time"
                if created_at_str:
                    try:
                        # Assuming created_at is in 'YYYY-MM-DD HH:MM:SS' format from core
                        dt = QDateTime.fromString(created_at_str, "yyyy-MM-dd HH:mm:ss")
                        if not dt.isValid(): # Try ISO with T separator
                             dt = QDateTime.fromString(created_at_str, Qt.DateFormat.ISODateWithMs)
                        if not dt.isValid(): # Try ISO without T separator (space)
                             dt = QDateTime.fromString(created_at_str, "yyyy-MM-dd HH:mm:ss.s")


                        if dt.isValid():
                            display_created_at = dt.toString("yyyy-MM-dd HH:mm")
                        else:
                            display_created_at = created_at_str 
                    except Exception:
                        display_created_at = created_at_str
                
                item_text: str = f"{title} - Created: {display_created_at}"
                list_item = QListWidgetItem(item_text)
                list_item.setData(Qt.ItemDataRole.UserRole, note)
                self.notes_list_widget.addItem(list_item)

    def _handle_note_item_double_click(self, item: QListWidgetItem) -> None:
        note_data_any: Optional[Any] = item.data(Qt.ItemDataRole.UserRole)
        if note_data_any and isinstance(note_data_any, dict):
            self._show_edit_note_dialog(cast(NoteData, note_data_any))

    def _show_add_note_dialog(self) -> None:
        dialog = NoteDialog(parent=self)
        if dialog.exec():
            note_input_data: Dict[str, Any] = dialog.get_note_input_data()
            try:
                new_note_id: Optional[int] = self.note_manager.add_note(
                    content=note_input_data["content"],
                    title=note_input_data.get("title"),
                    # task_id and project_id are not collected by this dialog version
                    task_id=note_input_data.get("task_id"), 
                    project_id=note_input_data.get("project_id")
                )
                if new_note_id is not None:
                    QMessageBox.information(self, "Success", f"Note '{note_input_data.get('title', 'Untitled')}' added.")
                    self.refresh_view_content()
                else:
                    QMessageBox.warning(self, "Failed", "Failed to add note.")
            except sqlite3.Error as e:
                QMessageBox.critical(self, "Database Error", f"Error adding note: {e}")
            except Exception as e:
                QMessageBox.critical(self, "Application Error", f"An unexpected error occurred: {e}")

    def _show_edit_note_dialog(self, note_to_edit: NoteData) -> None:
        note_id: int = note_to_edit["id"]
        
        try:
            current_note_data: Optional[NoteData] = self.note_manager.get_note(note_id)
            if not current_note_data:
                QMessageBox.warning(self, "Error", f"Could not find Note ID {note_id}. It might have been deleted.")
                self.refresh_view_content()
                return
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"Failed to load note data: {e}")
            return

        dialog = NoteDialog(parent=self, existing_note_data=current_note_data)
        if dialog.exec():
            updated_note_input_data: Dict[str, Any] = dialog.get_note_input_data()
            try:
                # Prepare data for update_note, only sending fields that are intended for update
                update_kwargs: Dict[str, Any] = {}
                if "title" in updated_note_input_data: # Check if field was in dialog data
                    update_kwargs["title"] = updated_note_input_data["title"]
                if "content" in updated_note_input_data:
                    update_kwargs["content"] = updated_note_input_data["content"]
                # Add task_id and project_id if dialog supports them
                if "task_id" in updated_note_input_data:
                     update_kwargs["task_id"] = updated_note_input_data["task_id"]
                if "project_id" in updated_note_input_data:
                     update_kwargs["project_id"] = updated_note_input_data["project_id"]


                success: bool = self.note_manager.update_note(note_id, **update_kwargs)
                
                if success:
                    QMessageBox.information(self, "Success", f"Note ID {note_id} updated successfully.")
                    self.refresh_view_content()
                else:
                    QMessageBox.warning(self, "Failed", f"Failed to update Note ID {note_id}.")
            except sqlite3.Error as e:
                QMessageBox.critical(self, "Database Error", f"Error updating note: {e}")
            except Exception as e:
                QMessageBox.critical(self, "Application Error", f"An unexpected error occurred: {e}")


class NoteDialog(QDialog):
    title_edit: QLineEdit
    content_edit: QTextEdit
    # task_id_edit: QLineEdit # If UI elements for these are added
    # project_id_edit: QLineEdit

    _existing_note_data: Optional[NoteData]

    def __init__(self, parent: Optional[QWidget] = None, existing_note_data: Optional[NoteData] = None) -> None:
        super().__init__(parent)
        self._existing_note_data = existing_note_data
        self.setWindowTitle("Edit Note" if existing_note_data else "Add New Note")
        self.setMinimumWidth(450)
        self.setMinimumHeight(300) 
        self._init_ui()
        if existing_note_data:
            self._populate_fields(existing_note_data)

    def _init_ui(self) -> None:
        layout = QFormLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        self.title_edit = QLineEdit()
        self.content_edit = QTextEdit()
        # self.task_id_edit = QLineEdit() # Add if task/project linking is desired in dialog
        # self.task_id_edit.setPlaceholderText("Optional Task ID")
        # self.project_id_edit = QLineEdit()
        # self.project_id_edit.setPlaceholderText("Optional Project ID")

        layout.addRow("Title:", self.title_edit)
        layout.addRow("Content:", self.content_edit)
        # layout.addRow("Task ID (Optional):", self.task_id_edit)
        # layout.addRow("Project ID (Optional):", self.project_id_edit)

        self.button_box = QDialogButtonBox()
        self.button_box.addButton(QDialogButtonBox.StandardButton.Ok)
        self.button_box.addButton(QDialogButtonBox.StandardButton.Cancel)
        
        if self._existing_note_data:
            delete_button = self.button_box.addButton("Delete", QDialogButtonBox.ButtonRole.DestructiveRole)
            delete_button.clicked.connect(self._confirm_delete_note)
            
        self.button_box.accepted.connect(self._validate_and_accept)
        self.button_box.rejected.connect(self.reject)
        layout.addRow(self.button_box)

    def _populate_fields(self, note_data: NoteData) -> None:
        self.title_edit.setText(note_data.get("title", ""))
        self.content_edit.setPlainText(note_data.get("content", ""))
        # task_id_val = note_data.get("task_id")
        # project_id_val = note_data.get("project_id")
        # self.task_id_edit.setText(str(task_id_val) if task_id_val is not None else "")
        # self.project_id_edit.setText(str(project_id_val) if project_id_val is not None else "")


    def _validate_and_accept(self) -> None:
        # Content is NOT NULL in schema, title can be.
        # Original code validated title, let's keep that for now.
        if not self.title_edit.text().strip() and not self.content_edit.toPlainText().strip() :
            QMessageBox.warning(self, "Input Error", "Note title or content cannot be empty.")
            return
        self.accept()

    def _confirm_delete_note(self) -> None:
        if not self._existing_note_data:
            return

        note_id: int = self._existing_note_data["id"]
        note_title: str = self._existing_note_data.get("title") or "Untitled"
        
        reply: QMessageBox.StandardButton = QMessageBox.question(
            self, 
            "Confirm Delete", 
            f"Are you sure you want to delete the note \"{note_title}\" (ID: {note_id})? This action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            parent_view = cast(NoteView, self.parent())
            try:
                success: bool = parent_view.note_manager.delete_note(note_id)
                if success:
                    QMessageBox.information(parent_view, "Success", f"Note ID {note_id} has been deleted.")
                    parent_view.refresh_view_content()
                    self.done(QDialog.DialogCode.Accepted) 
                else:
                    QMessageBox.warning(parent_view, "Failed", f"Failed to delete Note ID {note_id}.")
            except sqlite3.Error as e:
                QMessageBox.critical(parent_view, "Database Error", f"Error deleting note: {e}")
            except Exception as e:
                 QMessageBox.critical(parent_view, "Application Error", f"An unexpected error occurred: {e}")


    def get_note_input_data(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "title": self.title_edit.text().strip() or None, # Allow title to be None if empty
            "content": self.content_edit.toPlainText().strip(), # Content is NOT NULL
            # "task_id": None, # Default to None if UI elements are not active
            # "project_id": None
        }
        
        # Example if task_id/project_id inputs were active:
        # task_id_str = self.task_id_edit.text().strip()
        # data["task_id"] = int(task_id_str) if task_id_str.isdigit() else None
        # project_id_str = self.project_id_edit.text().strip()
        # data["project_id"] = int(project_id_str) if project_id_str.isdigit() else None
        
        # For now, as UI doesn't collect task_id/project_id, explicitly set to None or omit
        # to match manager's optional parameters if they default to None.
        # Current NoteManager.add_note allows them to be None.
        data["task_id"] = None
        data["project_id"] = None
        
        return data
