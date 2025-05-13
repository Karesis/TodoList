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
    def render(self) -> str:
        if self.done:
            done_symble = "*"
        else:
            done_symble = "O"

        return self.content + f" {done_symble}"

    def __repr__(self) -> str:
        status = "Done" if self.done else "Pending"
        return (f"Task(content='{self.content}', "
                f"timestamp='{self.timestamp.isoformat()}', "
                f"status='{status}')")

class TaskList:
    def __init__(self, file_name: str) -> None:
        self.list: List[Task] = []
        self.file_name: str = file_name

    def load(self) -> None: 
        self.list.clear()

        try:
            with open(self.file_name, "r", encoding="utf-8") as f:
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

                self.list.append(task)

        except FileNotFoundError:
            print(f"Info: File '{self.file_name}' not found. Starting with an empty task list.")
        
        except json.JSONDecodeError:
            print(f"Warning: File '{self.file_name}' is empty or contains invalid JSON. "
                   "Starting with an empty task list.")

        except Exception as e:
            print(f"An unexpected error occurred while reading '{self.file_name}': {e}")


    def save(self) -> None:
        task_list_to_save: List[Task] = self.list

        try:
            list_of_dicts: List[Dict] = [task.to_dict() for task in task_list_to_save]

            with open(self.file_name, "w", encoding="utf-8") as f:
                json.dump(list_of_dicts, f, indent=4)

        except IOError as e:
            print(f"Error: Could not write to file '{self.file_name}': {e}")
        
        except Exception as e:
            print(f"An unexpected error occurred while writing to '{self.file_name}': {e}")

    def add(self, task_description: str) -> None:
        add_task: Task = Task(task_description)
        self.list.append(add_task)

    def delete(self, task_index: int) -> None:
        task_index -= 1

        try:
            removed_task = self.list.pop(task_index) 
            print(f"Deleted task: {removed_task.content}")

        except IndexError:
             print(f"Error: Invalid index {task_index}.")

    def done(self, task_index: int) -> None:
        task_index -= 1

        try:
            if not self.list[task_index].done:
                self.list[task_index].done = True
                print(f"Completed task: {self.list[task_index].content}")
            else:
                print(f"Task '{self.list[task_index].content}' was already marked as done.")

        except IndexError:
             print(f"Error: Invalid index {task_index}.")

    def __repr__(self) -> str:
        if not self.list:
            return "--- TodoList (is empty) ---"
        render = f"--- TodoList ---\n"
        
        for i, tas_item in enumerate(self.list):
            render += f"{i + 1}: {task_item.render()}\n"
            
        return render
