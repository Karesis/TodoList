# src/ui/navigation_config.py
from typing import List, Dict, TypedDict, Type, Optional
from PyQt6.QtWidgets import QWidget

# It's better to import view classes here for type safety and clarity
# This also helps centralize view management if needed for other purposes.
from .views.task_view import TaskView
from .views.schedule_view import ScheduleView
from .views.project_view import ProjectView
from .views.goal_view import GoalView
from .views.note_view import NoteView
from .views.reminder_view import ReminderView
from .views.settings_view import SettingsView
# Example for placeholder views if they were to be implemented:
# from .views.dashboard_view import DashboardView
# from .views.data_service_view import DataServiceView

class NavItemConfig(TypedDict):
    text: str          # Text displayed in the navigation list
    identifier: str    # Unique string key to identify the view/module
    # icon_name: Optional[str] # Future: for QIcon.fromTheme() or resource path

# Navigation items: order defines display order in the navigation panel
NAV_ITEMS_CONFIG: List[NavItemConfig] = [
    # {"text": "仪表盘", "identifier": "DashboardView"},
    {"text": "任务管理", "identifier": "TaskView"},
    {"text": "日程安排", "identifier": "ScheduleView"},
    {"text": "提醒管理", "identifier": "ReminderView"},
    {"text": "项目管理", "identifier": "ProjectView"},
    {"text": "目标追踪", "identifier": "GoalView"},
    {"text": "笔记便签", "identifier": "NoteView"},
    # {"text": "数据服务", "identifier": "DataServiceView"},
    {"text": "设置", "identifier": "SettingsView"},
]

# Maps view identifiers from NAV_ITEMS_CONFIG to their respective widget classes
VIEW_CLASS_REGISTRY: Dict[str, Type[QWidget]] = {
    "TaskView": TaskView,
    "ScheduleView": ScheduleView,
    "ReminderView": ReminderView,
    "ProjectView": ProjectView,
    "GoalView": GoalView,
    "NoteView": NoteView,
    "SettingsView": SettingsView, # SettingsView might need special instantiation if it takes `main_window_ref`
    # "DashboardView": DashboardView,
    # "DataServiceView": DataServiceView,
}
