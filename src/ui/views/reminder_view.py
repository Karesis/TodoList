# src/ui/views/reminder_view.py
import sqlite3
from datetime import datetime
from typing import List, Optional, Dict, Any, cast

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QListWidget, QListWidgetItem, QPushButton, QHBoxLayout,
    QDialog, QFormLayout, QLineEdit, QComboBox, QDateTimeEdit, QDialogButtonBox, QMessageBox
)
from PyQt6.QtCore import Qt, QDateTime
from PyQt6.QtGui import QFont

from core import ReminderManager, TaskManager, ScheduleManager
from core.reminder_manager import ReminderData
# Assuming TaskData and EventData will be available from their respective managers
# from ...core.task_manager import TaskData
# from ...core.schedule_manager import EventData
_TaskDataPlaceholder = Dict[str, Any] # Temporary
_EventDataPlaceholder = Dict[str, Any] # Temporary

_SENTINEL = object()

# UI Display mapping for Reminder Statuses
_REMINDER_STATUS_DB_TO_DISPLAY: Dict[str, str] = {
    "pending": "Pending",
    "triggered": "Triggered",
    "dismissed": "Dismissed",
    "snoozed": "Snoozed" # Assuming snooze is a possible status from manager
}
_REMINDER_STATUS_DISPLAY_TO_DB: Dict[str, str] = {
    v: k for k, v in _REMINDER_STATUS_DB_TO_DISPLAY.items()
}


class ReminderView(QWidget):
    reminder_manager: ReminderManager
    task_manager: TaskManager
    schedule_manager: ScheduleManager
    add_reminder_button: QPushButton
    reminders_list_widget: QListWidget

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.reminder_manager = ReminderManager()
        self.task_manager = TaskManager()
        self.schedule_manager = ScheduleManager()
        self._init_ui()

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        title_label = QLabel("Reminders")
        font = title_label.font()
        font.setPointSize(24)
        font.setBold(True)
        title_label.setFont(font)
        title_label.setStyleSheet("margin-bottom: 10px;")
        main_layout.addWidget(title_label)

        action_layout = QHBoxLayout()
        self.add_reminder_button = QPushButton(" Add New Reminder")
        self.add_reminder_button.clicked.connect(self._show_add_reminder_dialog)
        action_layout.addWidget(self.add_reminder_button)
        action_layout.addStretch()
        main_layout.addLayout(action_layout)

        self.reminders_list_widget = QListWidget()
        self.reminders_list_widget.itemDoubleClicked.connect(self._handle_reminder_item_double_click)
        main_layout.addWidget(self.reminders_list_widget)

        self.setLayout(main_layout)
        self.refresh_view_content()

    def refresh_view_content(self) -> None:
        self.reminders_list_widget.clear()
        try:
            reminders: List[ReminderData] = self.reminder_manager.get_all_reminders(sort_by="reminder_time")
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"Failed to load reminders: {e}")
            reminders = []

        if not reminders:
            no_reminder_item = QListWidgetItem("No reminders set.")
            no_reminder_item.setFlags(no_reminder_item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            self.reminders_list_widget.addItem(no_reminder_item)
        else:
            for reminder in reminders:
                reminder_time_dt = QDateTime.fromString(reminder["reminder_time"], Qt.DateFormat.ISODate)
                time_str: str = reminder_time_dt.toString("yyyy-MM-dd hh:mm ap") if reminder_time_dt.isValid() else reminder["reminder_time"]
                
                item_text_parts: List[str] = [time_str]
                linked_item_info: str = ""

                task_id = reminder.get("task_id")
                event_id = reminder.get("event_id")

                if task_id is not None:
                    try:
                        task: Optional[_TaskDataPlaceholder] = self.task_manager.get_task(task_id) # type: ignore
                        linked_item_info = f"Task: {task['title']}" if task else f"Task ID: {task_id} (Not found)"
                    except sqlite3.Error:
                        linked_item_info = f"Task ID: {task_id} (Error loading)"
                elif event_id is not None:
                    try:
                        event: Optional[_EventDataPlaceholder] = self.schedule_manager.get_event(event_id) # type: ignore
                        linked_item_info = f"Event: {event['title']}" if event else f"Event ID: {event_id} (Not found)"
                    except sqlite3.Error:
                        linked_item_info = f"Event ID: {event_id} (Error loading)"
                
                if linked_item_info:
                    item_text_parts.append(linked_item_info)
                
                message: Optional[str] = reminder.get("message")
                if message:
                    item_text_parts.append(f"Msg: {message}")
                
                status_display: str = _REMINDER_STATUS_DB_TO_DISPLAY.get(reminder["status"], reminder["status"])
                item_text_parts.append(f"({status_display})")
                
                list_item = QListWidgetItem(" - ".join(item_text_parts))
                list_item.setData(Qt.ItemDataRole.UserRole, reminder)
                self.reminders_list_widget.addItem(list_item)

    def _handle_reminder_item_double_click(self, item: QListWidgetItem) -> None:
        reminder_data_any: Optional[Any] = item.data(Qt.ItemDataRole.UserRole)
        if reminder_data_any and isinstance(reminder_data_any, dict):
            self._show_edit_reminder_dialog(cast(ReminderData, reminder_data_any))

    def _show_add_reminder_dialog(self) -> None:
        dialog = ReminderDialog(
            parent=self,
            task_manager=self.task_manager,
            schedule_manager=self.schedule_manager
        )
        if dialog.exec():
            reminder_input_data: Dict[str, Any] = dialog.get_reminder_input_data()
            try:
                new_id: Optional[int] = self.reminder_manager.add_reminder(**reminder_input_data)
                if new_id is not None:
                    QMessageBox.information(self, "Success", f"Reminder added with ID: {new_id}.")
                    self.refresh_view_content()
                else:
                    QMessageBox.warning(self, "Failed", "Failed to add reminder.")
            except sqlite3.Error as e:
                QMessageBox.critical(self, "Database Error", f"Error adding reminder: {e}")
            except Exception as e:
                QMessageBox.critical(self, "Application Error", f"An unexpected error occurred: {e}")

    def _show_edit_reminder_dialog(self, reminder_to_edit: ReminderData) -> None:
        reminder_id: int = reminder_to_edit["id"]
        try:
            current_data: Optional[ReminderData] = self.reminder_manager.get_reminder(reminder_id)
            if not current_data:
                QMessageBox.warning(self, "Error", f"Reminder ID {reminder_id} not found.")
                self.refresh_view_content()
                return
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"Failed to load reminder data: {e}")
            return

        dialog = ReminderDialog(
            parent=self,
            existing_reminder_data=current_data,
            task_manager=self.task_manager,
            schedule_manager=self.schedule_manager
        )
        if dialog.exec():
            updated_data: Dict[str, Any] = dialog.get_reminder_input_data()
            try:
                success: bool = self.reminder_manager.update_reminder(reminder_id, **updated_data)
                if success:
                    QMessageBox.information(self, "Success", f"Reminder ID {reminder_id} updated.")
                    self.refresh_view_content()
                else:
                    QMessageBox.warning(self, "Failed", f"Failed to update Reminder ID {reminder_id}.")
            except sqlite3.Error as e:
                QMessageBox.critical(self, "Database Error", f"Error updating reminder: {e}")
            except Exception as e:
                QMessageBox.critical(self, "Application Error", f"An unexpected error occurred: {e}")


class ReminderDialog(QDialog):
    link_type_combo: QComboBox
    link_id_edit: QLineEdit
    reminder_datetime_edit: QDateTimeEdit
    message_edit: QLineEdit
    status_combo: QComboBox
    
    _existing_reminder_data: Optional[ReminderData]
    _task_manager: TaskManager
    _schedule_manager: ScheduleManager

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        existing_reminder_data: Optional[ReminderData] = None,
        task_manager: Optional[TaskManager] = None, # Make optional for robustness
        schedule_manager: Optional[ScheduleManager] = None # Make optional
    ) -> None:
        super().__init__(parent)
        self._existing_reminder_data = existing_reminder_data
        # These managers are needed for validation if linking is chosen
        if task_manager is None: raise ValueError("TaskManager instance is required for ReminderDialog")
        if schedule_manager is None: raise ValueError("ScheduleManager instance is required for ReminderDialog")
        self._task_manager = task_manager
        self._schedule_manager = schedule_manager
        
        self.setWindowTitle("Edit Reminder" if existing_reminder_data else "Add New Reminder")
        self.setMinimumWidth(450)
        self._init_ui()
        if existing_reminder_data:
            self._populate_fields(existing_reminder_data)

    def _init_ui(self) -> None:
        layout = QFormLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        self.link_type_combo = QComboBox()
        self.link_type_combo.addItems(["No Link", "Link to Task", "Link to Event"])
        
        self.link_id_edit = QLineEdit()
        self.link_id_edit.setPlaceholderText("Enter Task ID or Event ID if linked")
        
        self.reminder_datetime_edit = QDateTimeEdit(QDateTime.currentDateTime().addDays(1))
        self.reminder_datetime_edit.setCalendarPopup(True)
        self.reminder_datetime_edit.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        
        self.message_edit = QLineEdit()
        self.message_edit.setPlaceholderText("Optional reminder message")
        
        self.status_combo = QComboBox()
        self.status_combo.addItems(list(_REMINDER_STATUS_DISPLAY_TO_DB.keys()))

        layout.addRow("Link Type:", self.link_type_combo)
        layout.addRow("Link ID:", self.link_id_edit)
        layout.addRow("Reminder Time:", self.reminder_datetime_edit)
        layout.addRow("Message:", self.message_edit)
        layout.addRow("Status:", self.status_combo)

        self.button_box = QDialogButtonBox()
        self.button_box.addButton(QDialogButtonBox.StandardButton.Ok)
        self.button_box.addButton(QDialogButtonBox.StandardButton.Cancel)
        
        if self._existing_reminder_data:
            delete_button = self.button_box.addButton("Delete", QDialogButtonBox.ButtonRole.DestructiveRole)
            delete_button.clicked.connect(self._confirm_delete_reminder)
            
        self.button_box.accepted.connect(self._validate_and_accept)
        self.button_box.rejected.connect(self.reject)
        layout.addRow(self.button_box)

    def _populate_fields(self, reminder_data: ReminderData) -> None:
        task_id = reminder_data.get("task_id")
        event_id = reminder_data.get("event_id")

        if task_id is not None:
            self.link_type_combo.setCurrentIndex(1) # Link to Task
            self.link_id_edit.setText(str(task_id))
        elif event_id is not None:
            self.link_type_combo.setCurrentIndex(2) # Link to Event
            self.link_id_edit.setText(str(event_id))
        else:
            self.link_type_combo.setCurrentIndex(0) # No Link
            
        dt_str = reminder_data.get("reminder_time", "")
        if dt_str:
            q_dt = QDateTime.fromString(dt_str, Qt.DateFormat.ISODate) # Core manager stores ISO
            if q_dt.isValid(): self.reminder_datetime_edit.setDateTime(q_dt)
            
        self.message_edit.setText(reminder_data.get("message", ""))
        
        db_status: str = reminder_data.get("status", "pending")
        display_status_text: Optional[str] = None
        for d_text, mapped_db_status in _REMINDER_STATUS_DB_TO_DISPLAY.items():
            if mapped_db_status == db_status:
                display_status_text = d_text
                break
        if display_status_text:
             self.status_combo.setCurrentText(display_status_text)


    def _validate_and_accept(self) -> None:
        link_type_index: int = self.link_type_combo.currentIndex()
        link_id_str: str = self.link_id_edit.text().strip()
        
        if link_type_index > 0: # Task or Event linked
            if not link_id_str.isdigit():
                QMessageBox.warning(self, "Input Error", "Link ID must be a number.")
                return
            link_id = int(link_id_str)
            if link_type_index == 1: # Task
                if not self._task_manager.get_task(link_id):
                    QMessageBox.warning(self, "Input Error", f"Task ID {link_id} does not exist.")
                    return
            elif link_type_index == 2: # Event
                if not self._schedule_manager.get_event(link_id):
                    QMessageBox.warning(self, "Input Error", f"Event ID {link_id} does not exist.")
                    return
        
        current_display_status: str = self.status_combo.currentText()
        db_status: str = _REMINDER_STATUS_DISPLAY_TO_DB.get(current_display_status, "pending")

        if self.reminder_datetime_edit.dateTime() <= QDateTime.currentDateTime() and \
           db_status == "pending":
            reply: QMessageBox.StandardButton = QMessageBox.question(
                self, 
                "Confirm Reminder Time",
                "Reminder time is in the past or current time. Set as pending anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return
        self.accept()

    def _confirm_delete_reminder(self) -> None:
        if not self._existing_reminder_data: return

        reminder_id: int = self._existing_reminder_data["id"]
        parent_view = cast(ReminderView, self.parent())

        reply: QMessageBox.StandardButton = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to delete Reminder ID {reminder_id}? This cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                success: bool = parent_view.reminder_manager.delete_reminder(reminder_id)
                if success:
                    QMessageBox.information(parent_view, "Success", f"Reminder ID {reminder_id} deleted.")
                    parent_view.refresh_view_content()
                    self.done(QDialog.DialogCode.Accepted)
                else:
                    QMessageBox.warning(parent_view, "Failed", f"Failed to delete Reminder ID {reminder_id}.")
            except sqlite3.Error as e:
                QMessageBox.critical(parent_view, "Database Error", f"Error deleting reminder: {e}")
            except Exception as e:
                QMessageBox.critical(parent_view, "Application Error", f"An unexpected error occurred: {e}")


    def get_reminder_input_data(self) -> Dict[str, Any]:
        link_type_index: int = self.link_type_combo.currentIndex()
        link_id_str: str = self.link_id_edit.text().strip()
        
        task_id_val: Optional[int] = None
        event_id_val: Optional[int] = None

        if link_id_str.isdigit():
            link_id = int(link_id_str)
            if link_type_index == 1: task_id_val = link_id
            elif link_type_index == 2: event_id_val = link_id
        
        current_display_status: str = self.status_combo.currentText()
        db_status: str = _REMINDER_STATUS_DISPLAY_TO_DB.get(current_display_status, "pending")

        return {
            "task_id": task_id_val,
            "event_id": event_id_val,
            "reminder_time": self.reminder_datetime_edit.dateTime().toString(Qt.DateFormat.ISODate),
            "message": self.message_edit.text().strip() or None,
            "status": db_status
        }
