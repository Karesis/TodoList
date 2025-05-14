# src/ui/views/settings_view.py
from typing import Optional, TYPE_CHECKING

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PyQt6.QtGui import QFont

# For type hinting MainWindow to avoid circular import issues at runtime
if TYPE_CHECKING:
    from main_window import MainWindow


class SettingsView(QWidget):
    main_window: Optional['MainWindow']
    theme_button: QPushButton

    def __init__(self, parent: Optional[QWidget] = None, main_window_ref: Optional['MainWindow'] = None) -> None:
        super().__init__(parent)
        self.main_window = main_window_ref
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        title_label = QLabel("Settings")
        font = title_label.font()
        font.setPointSize(24)
        font.setBold(True)
        title_label.setFont(font)
        title_label.setStyleSheet("margin-bottom: 10px;")
        layout.addWidget(title_label)

        self.theme_button = QPushButton("Toggle Theme (Light/Dark)")
        if self.main_window and hasattr(self.main_window, "toggle_theme"):
            self.theme_button.clicked.connect(self.main_window.toggle_theme)
        else:
            self.theme_button.setEnabled(False)
        layout.addWidget(self.theme_button)
        
        layout.addStretch()
        self.setLayout(layout)

    def refresh_view_content(self) -> None:
        # This view currently has no dynamic content to refresh from a manager.
        pass
