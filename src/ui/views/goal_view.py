# src/ui/views/goal_view.py
import sqlite3
from datetime import datetime
from typing import List, Optional, Dict, Any, cast, Final

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QLineEdit, QTextEdit,
    QDialog, QDialogButtonBox, QFormLayout, QMessageBox,
    QDateEdit, QComboBox
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont

from core import GoalManager # Using __init__.py for core imports
from core.goal_manager import GoalData # Import TypedDict

# Using constants from GoalManager if they were made available, 
# or redefine UI-specific mappings if necessary and keep them aligned.
# For now, we'll define UI specific maps and ensure they align with backend.
_GOAL_STATUS_DB_TO_DISPLAY: Final[Dict[str, str]] = {
    "active": "进行中",
    "completed": "已达成",
    "archived": "已归档"
}
_GOAL_STATUS_DISPLAY_TO_DB: Final[Dict[str, str]] = {
    v: k for k, v in _GOAL_STATUS_DB_TO_DISPLAY.items()
}

class GoalView(QWidget):
    goal_manager: GoalManager
    add_goal_button: QPushButton
    goals_list_widget: QListWidget

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.goal_manager = GoalManager()
        self._init_ui()

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        title_label = QLabel("目标追踪")
        font = title_label.font()
        font.setPointSize(24)
        font.setBold(True)
        title_label.setFont(font)
        title_label.setStyleSheet("margin-bottom: 10px;")
        main_layout.addWidget(title_label)

        action_layout = QHBoxLayout()
        self.add_goal_button = QPushButton(" 添加新目标")
        # self.add_goal_button.setStyleSheet("padding: 8px 15px; font-size: 14px;") # Prefer QSS file
        self.add_goal_button.clicked.connect(self._show_add_goal_dialog)
        action_layout.addWidget(self.add_goal_button)
        action_layout.addStretch()
        main_layout.addLayout(action_layout)

        self.goals_list_widget = QListWidget()
        # self.goals_list_widget.setStyleSheet("font-size: 14px; border: 1px solid #e0e0e0;") # Prefer QSS file
        self.goals_list_widget.itemDoubleClicked.connect(self._handle_goal_item_double_click)
        main_layout.addWidget(self.goals_list_widget)

        self.setLayout(main_layout)
        self.refresh_view_content()

    def refresh_view_content(self) -> None:
        self.goals_list_widget.clear()
        try:
            goals: List[GoalData] = self.goal_manager.get_all_goals(sort_by="target_date", sort_order="ASC")
        except sqlite3.Error as e:
            QMessageBox.critical(self, "数据库错误", f"加载目标列表失败: {e}")
            goals = []

        if not goals:
            no_goal_item = QListWidgetItem("当前没有设定目标。")
            no_goal_item.setFlags(no_goal_item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            self.goals_list_widget.addItem(no_goal_item)
        else:
            for goal in goals:
                target_date_str: str = "-"
                if goal.get("target_date"):
                    try:
                        q_date = QDate.fromString(goal["target_date"], Qt.DateFormat.ISODate)
                        target_date_str = q_date.toString("yyyy-MM-dd") if q_date.isValid() else goal["target_date"]
                    except: # Keep original if parsing fails
                         target_date_str = goal["target_date"] or "-"
                
                status_display: str = _GOAL_STATUS_DB_TO_DISPLAY.get(goal["status"], goal["status"])
                item_text: str = f"{goal['name']} (目标日期: {target_date_str}) - {status_display}"
                
                list_item = QListWidgetItem(item_text)
                list_item.setData(Qt.ItemDataRole.UserRole, goal) 
                self.goals_list_widget.addItem(list_item)

    def _handle_goal_item_double_click(self, item: QListWidgetItem) -> None:
        goal_data: Optional[Any] = item.data(Qt.ItemDataRole.UserRole)
        if goal_data and isinstance(goal_data, dict):
            # Ensure it's cast to GoalData for type safety if used directly
            self._show_edit_goal_dialog(cast(GoalData, goal_data))

    def _show_add_goal_dialog(self) -> None:
        dialog = GoalDialog(parent=self)
        if dialog.exec():
            goal_input_data: Dict[str, Any] = dialog.get_goal_input_data()
            try:
                new_goal_id: Optional[int] = self.goal_manager.add_goal(
                    name=goal_input_data["name"],
                    description=goal_input_data.get("description"),
                    target_date=goal_input_data.get("target_date"),
                    status=goal_input_data["status"]
                )
                if new_goal_id is not None:
                    QMessageBox.information(self, "成功", f"目标 '{goal_input_data['name']}' 添加成功。")
                    self.refresh_view_content()
                else:
                    QMessageBox.warning(self, "失败", "添加目标失败。")
            except sqlite3.Error as e:
                QMessageBox.critical(self, "数据库错误", f"添加目标时发生错误: {e}")
            except Exception as e: # Catch other potential errors like KeyError from dict
                QMessageBox.critical(self, "程序错误", f"添加目标时发生意外错误: {e}")


    def _show_edit_goal_dialog(self, goal_to_edit: GoalData) -> None:
        goal_id: int = goal_to_edit["id"]
        
        try:
            current_goal_data: Optional[GoalData] = self.goal_manager.get_goal(goal_id)
            if not current_goal_data:
                QMessageBox.warning(self, "错误", f"无法找到目标 ID {goal_id}。可能已被删除。")
                self.refresh_view_content()
                return
        except sqlite3.Error as e:
            QMessageBox.critical(self, "数据库错误", f"加载目标数据失败: {e}")
            return

        dialog = GoalDialog(parent=self, existing_goal_data=current_goal_data)
        if dialog.exec():
            updated_goal_input_data: Dict[str, Any] = dialog.get_goal_input_data()
            try:
                success: bool = self.goal_manager.update_goal(
                    goal_id=goal_id,
                    name=updated_goal_input_data["name"],
                    description=updated_goal_input_data.get("description"),
                    target_date=updated_goal_input_data.get("target_date"),
                    status=updated_goal_input_data["status"]
                )
                if success:
                    QMessageBox.information(self, "成功", f"目标 ID {goal_id} 更新成功。")
                    self.refresh_view_content()
                else:
                    QMessageBox.warning(self, "失败", f"更新目标 ID {goal_id} 失败（可能数据未变或目标不存在）。")
            except sqlite3.Error as e:
                QMessageBox.critical(self, "数据库错误", f"更新目标时发生错误: {e}")
            except Exception as e:
                 QMessageBox.critical(self, "程序错误", f"更新目标时发生意外错误: {e}")

class GoalDialog(QDialog):
    name_edit: QLineEdit
    description_edit: QTextEdit
    target_date_edit: QDateEdit
    status_combo: QComboBox
    
    _existing_goal_data: Optional[GoalData]

    def __init__(self, parent: Optional[QWidget] = None, existing_goal_data: Optional[GoalData] = None) -> None:
        super().__init__(parent)
        self._existing_goal_data = existing_goal_data
        self.setWindowTitle("编辑目标" if existing_goal_data else "添加新目标")
        self.setMinimumWidth(400)
        self._init_ui()
        if existing_goal_data:
            self._populate_fields(existing_goal_data)

    def _init_ui(self) -> None:
        layout = QFormLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        self.name_edit = QLineEdit()
        self.description_edit = QTextEdit()
        self.description_edit.setFixedHeight(100)
        
        self.target_date_edit = QDateEdit(QDate.currentDate().addMonths(1))
        self.target_date_edit.setCalendarPopup(True)
        self.target_date_edit.setDisplayFormat("yyyy-MM-dd")
        
        self.status_combo = QComboBox()
        self.status_combo.addItems(list(_GOAL_STATUS_DISPLAY_TO_DB.keys()))

        layout.addRow("目标名称:", self.name_edit)
        layout.addRow("目标描述:", self.description_edit)
        layout.addRow("目标日期:", self.target_date_edit)
        layout.addRow("状态:", self.status_combo)

        self.button_box = QDialogButtonBox()
        self.button_box.addButton(QDialogButtonBox.StandardButton.Ok)
        self.button_box.addButton(QDialogButtonBox.StandardButton.Cancel)
        
        if self._existing_goal_data:
            delete_button = self.button_box.addButton("删除", QDialogButtonBox.ButtonRole.DestructiveRole)
            delete_button.clicked.connect(self._confirm_delete_goal)
            
        self.button_box.accepted.connect(self._validate_and_accept)
        self.button_box.rejected.connect(self.reject)
        layout.addRow(self.button_box)

    def _populate_fields(self, goal_data: GoalData) -> None:
        self.name_edit.setText(goal_data.get("name", ""))
        self.description_edit.setPlainText(goal_data.get("description", ""))
        
        target_date_str: Optional[str] = goal_data.get("target_date")
        if target_date_str:
            q_date = QDate.fromString(target_date_str, Qt.DateFormat.ISODate)
            if q_date.isValid():
                self.target_date_edit.setDate(q_date)
        
        db_status: str = goal_data.get("status", "active")
        display_status: Optional[str] = None
        for d_status, mapped_db_status in _GOAL_STATUS_DISPLAY_TO_DB.items():
            if mapped_db_status == db_status:
                display_status = d_status
                break
        if display_status:
            self.status_combo.setCurrentText(display_status)


    def _validate_and_accept(self) -> None:
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "输入错误", "目标名称不能为空。")
            return
        self.accept()

    def _confirm_delete_goal(self) -> None:
        if not self._existing_goal_data:
            return

        goal_id: int = self._existing_goal_data["id"]
        goal_name: str = self._existing_goal_data["name"]
        
        reply: QMessageBox.StandardButton = QMessageBox.question(
            self, 
            "确认删除", 
            f"您确定要删除目标 \"{goal_name}\" (ID: {goal_id}) 吗？此操作无法撤销。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            parent_view = cast(GoalView, self.parent())
            try:
                success: bool = parent_view.goal_manager.delete_goal(goal_id)
                if success:
                    QMessageBox.information(parent_view, "成功", f"目标 ID {goal_id} 已删除。")
                    parent_view.refresh_view_content()
                    self.done(QDialog.DialogCode.Accepted) 
                else:
                    QMessageBox.warning(parent_view, "失败", f"删除目标 ID {goal_id} 失败。")
            except sqlite3.Error as e:
                QMessageBox.critical(parent_view, "数据库错误", f"删除目标时发生错误: {e}")
            except Exception as e:
                QMessageBox.critical(parent_view, "程序错误", f"删除目标时发生意外错误: {e}")


    def get_goal_input_data(self) -> Dict[str, Any]:
        selected_display_status: str = self.status_combo.currentText()
        db_status: str = _GOAL_STATUS_DISPLAY_TO_DB.get(selected_display_status, "active")
        
        target_date_qdate: QDate = self.target_date_edit.date()
        target_date_str: Optional[str] = None
        if target_date_qdate.isValid(): # Ensure date is not null date
             target_date_str = target_date_qdate.toString(Qt.DateFormat.ISODate)

        return {
            "name": self.name_edit.text().strip(),
            "description": self.description_edit.toPlainText().strip() or None,
            "target_date": target_date_str,
            "status": db_status
        }
