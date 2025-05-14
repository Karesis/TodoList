# Time Management App

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

## Description

The Time Management App is a desktop application designed for local, single-user time and task management. It helps users organize tasks, manage projects, track goals, schedule events, take notes, and set reminders, all within a clean and intuitive interface. This project has undergone significant refactoring to ensure a clear and maintainable codebase.

## Features

* **Task Management**: Create, update, delete, and view tasks with details like priority, due dates, and status.
* **Project Organization**: Group tasks under specific projects for better workflow management.
* **Goal Tracking**: Define and manage personal or professional goals with target dates and status updates.
* **Note Taking**: A simple interface for creating and managing notes, which can be linked to tasks or projects (future enhancement).
* **Event Scheduling**: A calendar-based view to schedule and manage events with start/end times and location details.
* **Reminders**: Set reminders for important tasks or events.
* **Customizable Themes**: Switch between light and dark themes for user preference.
* **Data Services**:
    * Export individual tables to CSV.
    * Export the entire database to a JSON file.
    * Import data from CSV files into tables.
    * Database backup and restore functionality.
* **Settings**: Basic application settings, including theme selection.

## Project Structure

The application is organized into several key directories within the `src/` folder:

* `src/core/`: Contains the core business logic, with dedicated managers for each entity (tasks, projects, goals, etc.).
* `src/database/`: Handles all database-related operations, including schema definition, setup, and low-level database interactions.
* `src/ui/`: Manages the graphical user interface, built with PyQt6. This includes:
    * `main_window.py`: The main application window and frame.
    * `navigation_config.py`: Configuration for UI navigation.
    * `views/`: Individual view components for each feature (tasks, schedule, etc.).
    * `styles/`: QSS stylesheets for theming (light and dark).
    * `dialogs/` (currently empty): Placeholder for common or complex dialogs.
    * `widgets/` (currently empty): Placeholder for custom reusable UI widgets.
* `src/main.py`: The main entry point for launching the application.
* `resources/` (currently empty): Intended for static assets like icons.

## Technology Stack

* **Programming Language**: Python 3.x
* **GUI Framework**: PyQt6
* **Database**: SQLite 3

## Design & Refactoring Principles

This project has been refactored with the following principles in mind:

* **Clear Structure**: A modular design with distinct layers for UI, core logic, and data access.
* **Type Hinting**: Comprehensive type annotations are used throughout the codebase for improved clarity, robustness, and maintainability.
* **Separation of Concerns**: User interface logic is kept separate from business logic, and business logic is distinct from data persistence.
* **Self-Documenting Code**: Emphasis is placed on meaningful naming for variables, functions, and classes, along with a clear code structure, minimizing the need for extensive comments.
* **Theming**: The UI supports light and dark themes through external QSS (Qt Style Sheets) files, allowing for easy customization of the application's appearance.

## Setup and Running

1.  **Prerequisites**:
    * Python (version 3.7 or higher is recommended).
    * `pip` (Python package installer).

2.  **Installation**:
    * Clone this repository (if applicable, or download the source code).
    * Install the required Python package (PyQt6):
        ```bash
        pip install PyQt6
        ```
    * (No other external libraries are required based on the current refactoring scope).

3.  **Running the Application**:
    * Navigate to the root directory of the project (e.g., `time_management_app/`).
    * Run the main script from the `src` directory:
        ```bash
        python src/main.py
        ```
    * On the first run, the application will automatically initialize the SQLite database (`timemanager.db`) within the `src/database/app_data/` directory.

## Directory Layout Overview

````

.
├── LICENSE
├── README.md
└── src
    ├── __init__.py
    ├── core
    │   ├── __init__.py
    │   ├── data_service_manager.py
    │   ├── goal_manager.py
    │   ├── note_manager.py
    │   ├── project_manager.py
    │   ├── reminder_manager.py
    │   ├── schedule_manager.py
    │   └── task_manager.py
    ├── database
    │   ├── __init__.py
    │   ├── database_setup.py
    │   ├── db_operations.py
    │   └── schema.sql
    ├── main.py
    └── ui
        ├── __init__.py
        ├── main_window.py
        ├── navigation_config.py
        ├── styles
        │   ├── dark.qss
        │   └── light.qss
        └── views
            ├── goal_view.py
            ├── note_view.py
            ├── project_view.py
            ├── reminder_view.py
            ├── schedule_view.py
            ├── settings_view.py
            └── task_view.py

````

## Contributing

This project values clean, well-typed, and maintainable code. If you wish to contribute:
* Please adhere to the established coding style (minimal comments, strong typing, separation of concerns).
* Ensure any new UI elements follow the "simple, modern, and intuitive" design philosophy.
* (Future: Add guidelines on running tests, submitting pull requests, etc.)

## License

This project is licensed under the Apache License 2.0.
You can find the full license text at: [https://www.apache.org/licenses/LICENSE-2.0](https://www.apache.org/licenses/LICENSE-2.0)
