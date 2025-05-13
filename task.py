import os
import json
from datetime import datetime 
from typing import Optional, Dict, List

class Task:
    def __init__(self, 
                 task_description: str, 
                 timestamp: Optional[datetime] = None,
                 done: bool = False) -> None: 
        self.content: str = task_description

        if timestamp is None:
            self.timestamp: datetime = datetime.now() 
        else:
            self.timestamp: datetime = timestamp 

        self.done: bool = done 

    def to_dict(self) -> Dict:
        task_dir = {"content": self.content,
                    "timestamp": self.timestamp.isoformat(),
                    "done": self.done}
        return task_dir

    def __repr__(self) -> str:
        status = "Done" if self.done else "Pending"
        return (f"Task(content='{self.content}', "
                "timestamp='{self.timestamp.isoformat()}', "
                "status='{status}')")

def read_list(file_name: str) -> List[Task]:
    tasks_from_file: List[Task] = []
    try:
        with open(file_name, "r", encoding="utf-8") as f:
            list_of_dicts = json.load(f)

        for dict_task in list_of_dicts:
            timestamp_str = dict_task.get('timestamp')
            converted_timestamp: Optional[datetime] = None

            if timestamp_str:
                try:
                    converted_timestamp = datetime.fromisoformat(timestamp_str)
                except ValueError:
                    print(f"Warning: "
                           "Invalid timestamp format '{timestamp_str}' "
                           "for task '{dict_task.get('content')}'. "
                           "Using current time as fallback.")
                    converted_timestamp = datetime.now() 

            task = Task(task_description = dict_task.get('content', 'Missing description'),
                        timestamp = converted_timestamp, 
                        done = dict_task.get('done', False))

            tasks_from_file.append(task)

    except FileNotFoundError:
        print(f"Info: File '{file_name}' not found. Starting with an empty task list.")
    
    except json.JSONDecodeError:
        print(f"Warning: File '{file_name}' is empty or contains invalid JSON. "
               "Starting with an empty task list.")

    except Exception as e:
        print(f"An unexpected error occurred while reading '{file_name}': {e}")

    return tasks_from_file

def write_list(file_name: str, task_list_to_save: List[Task]) -> None:
    try:
        list_of_dicts: List[Dict] = [task.to_dict() for task in task_list_to_save]

        with open(file_name, "w", encoding="utf-8") as f:
            json.dump(list_of_dicts, f, indent=4)

    except IOError as e:
        print(f"Error: Could not write to file '{file_name}': {e}")
    
    except Exception as e:
        print(f"An unexpected error occurred while writing to '{file_name}': {e}")
