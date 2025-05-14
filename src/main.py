# src/main.py
import sys
import sqlite3 # For specific database error handling
from typing import List, Final

from PyQt6.QtWidgets import QApplication, QMessageBox

# Assuming 'src' is in PYTHONPATH or this script is run from 'src' parent.
# Adjust imports if your execution context or project structure dictates otherwise.
from ui.main_window import MainWindow
from database.database_setup import initialize_database, get_db_path

APP_NAME: Final[str] = "Time & Task Manager"
ORGANIZATION_NAME: Final[str] = "YourOrganization" # Placeholder, customize as needed
# APP_VERSION: Final[str] = "1.0.0"


class TimeManagementApp(QApplication):
    def __init__(self, argv: List[str]) -> None:
        super().__init__(argv)
        self.setApplicationName(APP_NAME)
        self.setOrganizationName(ORGANIZATION_NAME)
        # self.setApplicationVersion(APP_VERSION)
        # Other application-wide settings or global error hooks can be set here.


def run_application() -> None:
    try:
        initialize_database()
        # For debugging, you might want to see the path:
        # print(f"Database initialized/checked at: {get_db_path()}")
    except FileNotFoundError as e:
        # This error means schema.sql is missing, app cannot run.
        error_message = QMessageBox()
        error_message.setIcon(QMessageBox.Icon.Critical)
        error_message.setWindowTitle("Application Startup Error")
        error_message.setText(
            "A critical file (database schema) is missing.\n"
            "The application cannot start."
        )
        error_message.setDetailedText(str(e))
        error_message.exec()
        sys.exit(1)
    except sqlite3.Error as e:
        # This handles errors during database table creation etc.
        error_message = QMessageBox()
        error_message.setIcon(QMessageBox.Icon.Critical)
        error_message.setWindowTitle("Database Initialization Error")
        error_message.setText(
            "Failed to initialize the application database.\n"
            "The application cannot start."
        )
        error_message.setDetailedText(f"Database error: {e}\nAt path: {get_db_path()}")
        error_message.exec()
        sys.exit(1)
    except Exception as e: # Catch any other unexpected error during critical init
        error_message = QMessageBox()
        error_message.setIcon(QMessageBox.Icon.Critical)
        error_message.setWindowTitle("Unexpected Startup Error")
        error_message.setText(
            "An unexpected error occurred during application initialization."
        )
        error_message.setDetailedText(str(e))
        error_message.exec()
        sys.exit(1)

    app: TimeManagementApp = TimeManagementApp(sys.argv)
    
    main_window: MainWindow = MainWindow()
    main_window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    run_application()
