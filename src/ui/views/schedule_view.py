# src/ui/views/schedule_view.py
import sqlite3
from datetime import datetime # For default QDateTimeEdit values
from typing import List, Optional, Dict, Any, cast

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QCalendarWidget, QListWidget, QListWidgetItem,
    QDialog, QDialogButtonBox, QFormLayout, QLineEdit, QTextEdit,
    QDateTimeEdit, QCheckBox, QMessageBox
)
from PyQt6.QtCore import Qt, QDate, QDateTime, QTime
from PyQt6.QtGui import QFont

from ...core import ScheduleManager
from ...core.schedule_manager import EventData # Import TypedDict

_SENTINEL = object()

class ScheduleView(QWidget):
    schedule_manager: ScheduleManager
    calendar_widget: QCalendarWidget
    selected_date_label: QLabel
    add_event_button: QPushButton
    events_list_widget: QListWidget

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.schedule_manager = ScheduleManager()
        self._init_ui()

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        title_label = QLabel("Schedule & Events")
        font = title_label.font()
        font.setPointSize(24)
        font.setBold(True)
        title_label.setFont(font)
        title_label.setStyleSheet("margin-bottom: 10px;")
        main_layout.addWidget(title_label)

        content_layout = QHBoxLayout()
        main_layout.addLayout(content_layout)

        self.calendar_widget = QCalendarWidget()
        self.calendar_widget.setGridVisible(True)
        self.calendar_widget.clicked[QDate].connect(self._on_date_selected)
        content_layout.addWidget(self.calendar_widget, 2) # Calendar takes more space

        details_panel_layout = QVBoxLayout()
        details_panel_layout.setSpacing(10)
        content_layout.addLayout(details_panel_layout, 1) # Details panel takes less space

        self.selected_date_label = QLabel("No date selected")
        font_selected_date = self.selected_date_label.font()
        font_selected_date.setPointSize(16)
        font_selected_date.setBold(True)
        self.selected_date_label.setFont(font_selected_date)
        self.selected_date_label.setStyleSheet("margin-bottom: 5px;")
        details_panel_layout.addWidget(self.selected_date_label)

        self.add_event_button = QPushButton(" Add New Event")
        self.add_event_button.clicked.connect(self._show_add_event_dialog)
        details_panel_layout.addWidget(self.add_event_button)

        self.events_list_widget = QListWidget()
        self.events_list_widget.itemDoubleClicked.connect(self._handle_event_item_double_click)
        details_panel_layout.addWidget(self.events_list_widget)
        
        self.setLayout(main_layout)
        self._on_date_selected(self.calendar_widget.selectedDate()) # Initial load

    def _on_date_selected(self, date: QDate) -> None:
        self.selected_date_label.setText(f"Events for: {date.toString("yyyy-MM-dd")}")
        self.refresh_view_content(date)

    def refresh_view_content(self, date: Optional[QDate] = None) -> None:
        if date is None:
            date = self.calendar_widget.selectedDate()
        
        self.events_list_widget.clear()
        try:
            # ScheduleManager expects ISO strings for the period
            period_start_iso: str = date.toString(Qt.DateFormat.ISODate) + "T00:00:00"
            period_end_iso: str = date.toString(Qt.DateFormat.ISODate) + "T23:59:59"
            
            events: List[EventData] = self.schedule_manager.get_events_for_period(
                period_start_iso, period_end_iso
            )
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"Failed to load events: {e}")
            events = []

        if not events:
            no_event_item = QListWidgetItem("No events scheduled for this date.")
            no_event_item.setFlags(no_event_item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            self.events_list_widget.addItem(no_event_item)
        else:
            for event_data in events:
                start_dt = QDateTime.fromString(event_data["start_time"], "yyyy-MM-dd HH:mm:ss")
                end_dt = QDateTime.fromString(event_data["end_time"], "yyyy-MM-dd HH:mm:ss")
                
                time_format = "HH:mm"
                item_text: str
                if event_data.get("is_all_day") == 1: # Check for all_day
                    item_text = f"All-day: {event_data['title']}"
                else:
                    start_display = start_dt.toString(time_format) if start_dt.isValid() else "?"
                    end_display = end_dt.toString(time_format) if end_dt.isValid() else "?"
                    item_text = f"{start_display} - {end_display}: {event_data['title']}"
                
                list_item = QListWidgetItem(item_text)
                list_item.setData(Qt.ItemDataRole.UserRole, event_data)
                self.events_list_widget.addItem(list_item)
    
    def _handle_event_item_double_click(self, item: QListWidgetItem) -> None:
        event_data_any: Optional[Any] = item.data(Qt.ItemDataRole.UserRole)
        if event_data_any and isinstance(event_data_any, dict):
            self._show_edit_event_dialog(cast(EventData, event_data_any))

    def _show_add_event_dialog(self) -> None:
        selected_date: QDate = self.calendar_widget.selectedDate()
        dialog = EventDialog(parent=self, selected_date_for_new_event=selected_date)
        if dialog.exec():
            event_input_data: Dict[str, Any] = dialog.get_event_input_data()
            try:
                new_event_id: Optional[int] = self.schedule_manager.add_event(**event_input_data)
                if new_event_id is not None:
                    QMessageBox.information(self, "Success", f"Event '{event_input_data['title']}' added.")
                    self.refresh_view_content(selected_date)
                else:
                    QMessageBox.warning(self, "Failed", "Failed to add event.")
            except sqlite3.Error as e:
                QMessageBox.critical(self, "Database Error", f"Error adding event: {e}")
            except Exception as e:
                QMessageBox.critical(self, "Application Error", f"An unexpected error occurred: {e}")

    def _show_edit_event_dialog(self, event_to_edit: EventData) -> None:
        event_id: int = event_to_edit["id"]
        try:
            current_event_data: Optional[EventData] = self.schedule_manager.get_event(event_id)
            if not current_event_data:
                QMessageBox.warning(self, "Error", f"Event ID {event_id} not found.")
                self.refresh_view_content(self.calendar_widget.selectedDate())
                return
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"Failed to load event data: {e}")
            return

        dialog = EventDialog(parent=self, existing_event_data=current_event_data)
        if dialog.exec():
            updated_event_input_data: Dict[str, Any] = dialog.get_event_input_data()
            try:
                success: bool = self.schedule_manager.update_event(event_id, **updated_event_input_data)
                if success:
                    QMessageBox.information(self, "Success", f"Event ID {event_id} updated.")
                    self.refresh_view_content(self.calendar_widget.selectedDate())
                else:
                    QMessageBox.warning(self, "Failed", f"Failed to update Event ID {event_id}.")
            except sqlite3.Error as e:
                QMessageBox.critical(self, "Database Error", f"Error updating event: {e}")
            except Exception as e:
                 QMessageBox.critical(self, "Application Error", f"An unexpected error occurred: {e}")


class EventDialog(QDialog):
    title_edit: QLineEdit
    description_edit: QTextEdit
    start_datetime_edit: QDateTimeEdit
    end_datetime_edit: QDateTimeEdit
    all_day_checkbox: QCheckBox
    location_edit: QLineEdit
    
    _existing_event_data: Optional[EventData]
    _initial_date_for_new: QDate # Store initial date for reset

    def __init__(
        self, 
        parent: Optional[QWidget] = None, 
        existing_event_data: Optional[EventData] = None,
        selected_date_for_new_event: Optional[QDate] = None
    ) -> None:
        super().__init__(parent)
        self._existing_event_data = existing_event_data
        self._initial_date_for_new = selected_date_for_new_event or QDate.currentDate()

        self.setWindowTitle("Edit Event" if existing_event_data else "Add New Event")
        self.setMinimumWidth(450)
        self._init_ui()
        self._populate_fields()
        self._toggle_time_edits() # Initial setup based on checkbox

    def _init_ui(self) -> None:
        layout = QFormLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        self.title_edit = QLineEdit()
        self.description_edit = QTextEdit()
        self.description_edit.setFixedHeight(80)
        
        self.start_datetime_edit = QDateTimeEdit()
        self.start_datetime_edit.setCalendarPopup(True)
        
        self.end_datetime_edit = QDateTimeEdit()
        self.end_datetime_edit.setCalendarPopup(True)

        self.all_day_checkbox = QCheckBox("All-day event")
        self.all_day_checkbox.stateChanged.connect(self._toggle_time_edits)

        self.location_edit = QLineEdit()

        layout.addRow("Title:", self.title_edit)
        layout.addRow("Description:", self.description_edit)
        layout.addRow("Start Time:", self.start_datetime_edit)
        layout.addRow("End Time:", self.end_datetime_edit)
        layout.addRow("", self.all_day_checkbox)
        layout.addRow("Location (Optional):", self.location_edit)

        self.button_box = QDialogButtonBox()
        self.button_box.addButton(QDialogButtonBox.StandardButton.Ok)
        self.button_box.addButton(QDialogButtonBox.StandardButton.Cancel)
        reset_button = self.button_box.addButton("Reset", QDialogButtonBox.ButtonRole.ResetRole)
        reset_button.clicked.connect(self._reset_fields)
        
        if self._existing_event_data:
            delete_button = self.button_box.addButton("Delete", QDialogButtonBox.ButtonRole.DestructiveRole)
            delete_button.clicked.connect(self._confirm_delete_event)
            
        self.button_box.accepted.connect(self._validate_and_accept)
        self.button_box.rejected.connect(self.reject)
        layout.addRow(self.button_box)

    def _populate_fields(self) -> None:
        start_dt = QDateTime(self._initial_date_for_new, QTime(9, 0)) # Default 9 AM
        end_dt = start_dt.addSecs(3600) # Default 1 hour duration
        is_all_day_checked = False

        if self._existing_event_data:
            self.title_edit.setText(self._existing_event_data.get("title", ""))
            self.description_edit.setPlainText(self._existing_event_data.get("description", ""))
            self.location_edit.setText(self._existing_event_data.get("location", ""))
            is_all_day_checked = bool(self._existing_event_data.get("is_all_day", 0))
            
            start_iso = self._existing_event_data.get("start_time")
            end_iso = self._existing_event_data.get("end_time")
            
            if start_iso:
                parsed_start = QDateTime.fromString(start_iso, "yyyy-MM-dd HH:mm:ss")
                if parsed_start.isValid(): start_dt = parsed_start
            if end_iso:
                parsed_end = QDateTime.fromString(end_iso, "yyyy-MM-dd HH:mm:ss")
                if parsed_end.isValid(): end_dt = parsed_end
        
        self.start_datetime_edit.setDateTime(start_dt)
        self.end_datetime_edit.setDateTime(end_dt)
        self.all_day_checkbox.setChecked(is_all_day_checked)


    def _toggle_time_edits(self) -> None:
        is_all_day: bool = self.all_day_checkbox.isChecked()
        time_format: str = "yyyy-MM-dd" if is_all_day else "yyyy-MM-dd HH:mm"
        
        self.start_datetime_edit.setDisplayFormat(time_format)
        self.end_datetime_edit.setDisplayFormat(time_format)

        current_start_dt: QDateTime = self.start_datetime_edit.dateTime()
        current_end_dt: QDateTime = self.end_datetime_edit.dateTime()

        if is_all_day:
            current_start_dt.setTime(QTime(0, 0, 0))
            current_end_dt.setTime(QTime(23, 59, 59))
            if current_end_dt.date() < current_start_dt.date(): # Ensure end date is same or after
                current_end_dt.setDate(current_start_dt.date())
        # No specific time adjustment when unchecking, user can set specific times.
        
        self.start_datetime_edit.setDateTime(current_start_dt)
        self.end_datetime_edit.setDateTime(current_end_dt)

    def _reset_fields(self) -> None:
        self._populate_fields() # Re-populates based on existing_event_data or defaults
        self._toggle_time_edits()

    def _validate_and_accept(self) -> None:
        if not self.title_edit.text().strip():
            QMessageBox.warning(self, "Input Error", "Event title cannot be empty.")
            return
        
        start_dt: QDateTime = self.start_datetime_edit.dateTime()
        end_dt: QDateTime = self.end_datetime_edit.dateTime()

        if end_dt <= start_dt:
            QMessageBox.warning(self, "Input Error", "End time must be after start time.")
            return
        self.accept()

    def _confirm_delete_event(self) -> None:
        if not self._existing_event_data: return

        event_id: int = self._existing_event_data["id"]
        parent_view = cast(ScheduleView, self.parent())

        reply: QMessageBox.StandardButton = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to delete Event ID {event_id}? This action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                success: bool = parent_view.schedule_manager.delete_event(event_id)
                if success:
                    QMessageBox.information(parent_view, "Success", f"Event ID {event_id} deleted.")
                    parent_view.refresh_view_content(parent_view.calendar_widget.selectedDate())
                    self.done(QDialog.DialogCode.Accepted)
                else:
                    QMessageBox.warning(parent_view, "Failed", f"Failed to delete Event ID {event_id}.")
            except sqlite3.Error as e:
                QMessageBox.critical(parent_view, "Database Error", f"Error deleting event: {e}")
            except Exception as e:
                QMessageBox.critical(parent_view, "Application Error", f"An unexpected error occurred: {e}")

    def get_event_input_data(self) -> Dict[str, Any]:
        start_dt: QDateTime = self.start_datetime_edit.dateTime()
        end_dt: QDateTime = self.end_datetime_edit.dateTime()
        is_all_day_checked: bool = self.all_day_checkbox.isChecked()

        # Core manager expects "yyyy-MM-dd HH:mm:ss" strings
        dt_format_for_db: str = "yyyy-MM-dd HH:mm:ss"

        return {
            "title": self.title_edit.text().strip(),
            "description": self.description_edit.toPlainText().strip() or None,
            "start_time": start_dt.toString(dt_format_for_db),
            "end_time": end_dt.toString(dt_format_for_db),
            "is_all_day": 1 if is_all_day_checked else 0,
            "location": self.location_edit.text().strip() or None,
            "recurrence_rule": None # Not implemented in this dialog's UI
        }
