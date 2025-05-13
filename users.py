import json
from typing import Optional, Dict, List

class UserDict:
    def __init__(self) -> None:
        self.users_file: str = ".todolist.users"
        self.data: Dict[str, str] = {}
        self.current_user: Optional[str] = None

    def load(self) -> None:
        try:
            with open(self.users_file, "r", encoding="utf-8") as f:
                loaded_data = json.load(f)
                if isinstance(loaded_data, dict):
                    self.data = loaded_data
                else:
                    print(f"Warning: User data file '{self.users_file}' does not contain a valid dictionary. Starting fresh.")
                    self.data = {}
        except FileNotFoundError:
            print(f"Info: User data file '{self.users_file}' not found. A new one will be created if users are managed.")
            self.data = {}
        except json.JSONDecodeError:
            print(f"Warning: Could not decode JSON from '{self.users_file}'. File might be corrupted. Starting fresh.")
            self.data = {} 
        except Exception as e:
            print(f"An unexpected error occurred while loading user data: {e}")
            self.data = {} 

        self.current_user = None
        for user_name, status in self.data.items():
            if status == "signed":
                self.current_user = user_name
                break

    def save_data(self) -> None:
        try:
            with open(self.users_file, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=4, ensure_ascii=False) 
        except IOError as e:
            print(f"Error: Could not write user data to file '{self.users_file}': {e}")
        except Exception as e:
            print(f"An unexpected error occurred while saving user data: {e}")

    def add_user(self, user_name: str) -> None: 
        if user_name in self.data:
            print(f"User '{user_name}' already exists.") 
            return

        self.data[user_name] = "unsigned"
        print(f"User '{user_name}' added.")
        if self.current_user is None:
            self.change_user(user_name) 

    def change_user(self, user_name: str) -> None: 
        if user_name not in self.data:
            print(f"Error: User '{user_name}' does not exist. Please add the user first via 'user add {user_name}'.")
            return
        
        if self.current_user is not None and self.current_user in self.data:
            self.data[self.current_user] = "unsigned"
        
        self.data[user_name] = "signed"
        old_user = self.current_user
        self.current_user = user_name
        if old_user != self.current_user: 
             print(f"Current user changed to: {self.current_user}")
