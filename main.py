import sys
import argparse
from task import TaskList # Assuming task.py is in the same directory

def main() -> None:
    parser = argparse.ArgumentParser(
        prog="todolist",
        description="A simple command-line to-do list application."
    )

    subparsers = parser.add_subparsers(
        dest="command",
        help="Available actions",
        required=True 
    )

    parser_add = subparsers.add_parser(
        "add", 
        help="Add a new task to the list. The description can contain multiple words."
    )
    parser_add.add_argument(
        "description_parts",
        metavar="DESCRIPTION",
        nargs="+",
        help="The content of the task to add."
    )

    parser_delete = subparsers.add_parser(
        "delete", 
        help="Delete a task by its number (1-based index)."
    )
    parser_delete.add_argument(
        "task_number",
        metavar="TASK_NUM",
        type=int,
        help="The number of the task to delete."
    )

    parser_done = subparsers.add_parser(
        "done", 
        help="Mark a task as done by its number (1-based index)."
    )
    parser_done.add_argument(
        "task_number",
        metavar="TASK_NUM",
        type=int,
        help="The number of the task to mark as done."
    )

    parser_list = subparsers.add_parser(
        "list", 
        help="Show all tasks in the list."
    )
    
    args = parser.parse_args()

    username = "karesis" 
    file_name = f".tasklist.{username}.json" 
    
    task_manager = TaskList(file_name)
    task_manager.load()

    action_taken = True 

    if args.command == "add":
        description = " ".join(args.description_parts)
        task_manager.add(description)
    elif args.command == "delete":
        task_manager.delete(args.task_number)
    elif args.command == "done":
        task_manager.done(args.task_number)
    elif args.command == "list":
        print(task_manager)
        action_taken = False 
    else:
        print(f"Error: Unknown command '{args.command}'. Use -h for help.")
        action_taken = False 
        sys.exit(1)
    
    if action_taken:
        task_manager.save()
        print(f"Task list '{file_name}' saved.")


if __name__ == "__main__":
    main()
