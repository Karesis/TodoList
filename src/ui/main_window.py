# src/ui/main_window.py
import sys
from pathlib import Path
from typing import Dict, Optional, Final, List, Type

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem, QStackedWidget, QLabel,
    QApplication
)
from PyQt6.QtCore import Qt, QSize
# from PyQt6.QtGui import QIcon # Import QIcon if/when icons are used

# Import navigation configuration
from .navigation_config import NAV_ITEMS_CONFIG, VIEW_CLASS_REGISTRY, NavItemConfig

# Define base UI directory for resource loading
_UI_BASE_DIR: Final[Path] = Path(__file__).resolve().parent
_STYLES_DIR: Final[Path] = _UI_BASE_DIR / "styles"
_DEFAULT_THEME: Final[str] = "light"


class MainWindow(QMainWindow):
    nav_panel: QListWidget
    content_stack: QStackedWidget
    view_instances: Dict[str, QWidget]
    current_theme: str

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("时间与事务管理")
        self.setGeometry(100, 100, 1200, 800)

        self.current_theme = _DEFAULT_THEME
        self.view_instances = {}

        self._init_ui()
        self.load_styles(self.current_theme)

    def _init_ui(self) -> None:
        central_widget: QWidget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout: QHBoxLayout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.nav_panel = QListWidget()
        self.nav_panel.setObjectName("navPanel") # For QSS targeting
        self.nav_panel.setFixedWidth(220)
        main_layout.addWidget(self.nav_panel)

        self.content_stack = QStackedWidget()
        self.content_stack.setObjectName("contentStack") # For QSS targeting
        main_layout.addWidget(self.content_stack)

        self._setup_navigation()
        self.nav_panel.currentItemChanged.connect(self._on_navigation_changed)

        if self.nav_panel.count() > 0:
            self.nav_panel.setCurrentRow(0)

    def _setup_navigation(self) -> None:
        for item_config in NAV_ITEMS_CONFIG:
            nav_text: str = item_config["text"]
            view_identifier: str = item_config["identifier"]

            list_item: QListWidgetItem = QListWidgetItem(nav_text)
            list_item.setData(Qt.ItemDataRole.UserRole, view_identifier)
            self.nav_panel.addItem(list_item)

            view_class: Optional[Type[QWidget]] = VIEW_CLASS_REGISTRY.get(view_identifier)
            view_widget: QWidget

            if view_class:
                if view_identifier == "SettingsView": # Special case for SettingsView
                    view_widget = view_class(main_window_ref=self) # type: ignore
                else:
                    view_widget = view_class()
            else:
                view_widget = QLabel(f"视图 '{nav_text}' ({view_identifier}) 未实现")
                view_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            stack_index: int = self.content_stack.addWidget(view_widget)
            self.view_instances[view_identifier] = view_widget
            list_item.setData(Qt.ItemDataRole.UserRole + 1, stack_index)


    def _on_navigation_changed(
        self,
        current_item: Optional[QListWidgetItem],
        previous_item: Optional[QListWidgetItem] # Parameter provided by signal
    ) -> None:
        if not current_item:
            return

        stack_index: Optional[Any] = current_item.data(Qt.ItemDataRole.UserRole + 1)
        if stack_index is None or not isinstance(stack_index, int): # Basic type check
            return
            
        if 0 <= stack_index < self.content_stack.count():
            self.content_stack.setCurrentIndex(stack_index)
            current_widget: QWidget = self.content_stack.widget(stack_index)
            
            # Standardized refresh method call
            if hasattr(current_widget, "refresh_view_content") and \
               callable(getattr(current_widget, "refresh_view_content")):
                try:
                    getattr(current_widget, "refresh_view_content")()
                except Exception as e:
                    # In a real app, log this error
                    # print(f"Error refreshing view {current_widget}: {e}")
                    pass # Fail silently for now, or show a generic error message

    def load_styles(self, theme_name: str) -> None:
        self.current_theme = theme_name
        style_sheet_path: Path = _STYLES_DIR / f"{theme_name}.qss"
        
        fallback_style: str = """
            QMainWindow { background-color: #eeeeee; }
            QListWidget#navPanel { background-color: #f0f0f0; border-right: 1px solid #d0d0d0; }
            QLabel { color: #333333; }
        """
        
        qss_content: str = fallback_style
        if style_sheet_path.exists() and style_sheet_path.is_file():
            try:
                with open(style_sheet_path, "r", encoding="utf-8") as f:
                    qss_content = f.read()
            except IOError:
                # If reading fails, qss_content remains fallback_style
                # In a real app, log this error: print(f"Error reading stylesheet: {style_sheet_path}")
                pass
        # else: In a real app, log missing stylesheet: print(f"Stylesheet not found: {style_sheet_path}")
        
        self.setStyleSheet(qss_content)

    def toggle_theme(self) -> None:
        if self.current_theme == "light":
            self.load_styles("dark")
        else:
            self.load_styles("light")
