import sys
import argparse
from task import TaskList
from users import UserDict

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

    parser_user_command = subparsers.add_parser(
        "user", 
        help="Manage users (add, switch, view current, list all)." 
    )
    user_action_subparsers = parser_user_command.add_subparsers(
        dest="user_action",
        help="Specific user actions",
        required=True
    )
    
    parser_user_add = user_action_subparsers.add_parser(
        "add", 
        help="Add a new user."
    )
    parser_user_add.add_argument(
        "username", 
        metavar="USERNAME", 
        type=str, 
        help="The name of the user to add."
    )
    
    parser_user_switch = user_action_subparsers.add_parser(
        "switch", 
        help="Switch the current active user."
    )
    parser_user_switch.add_argument(
        "username", 
        metavar="USERNAME", 
        type=str, 
        help="The name of the user to switch to."
    )
    
    parser_user_current = user_action_subparsers.add_parser(
        "current", 
        help="Show the current active user."
    )
    
    parser_user_list_all = user_action_subparsers.add_parser(
        "list", 
        help="List all known users."
    )

    args = parser.parse_args()
    user_manager = UserDict()
    user_manager.load()

    if args.command == "user":
        if args.user_action == "add":
            user_manager.add_user(args.username)
            user_manager.save_data() 
            print(f"User command 'add' for user '{args.username}' processed.")
        elif args.user_action == "switch":
            user_manager.change_user(args.username)
            user_manager.save_data()
            print(f"User command 'switch' to user '{args.username}' processed.")
        elif args.user_action == "current":
            current = user_manager.current_user
            if current:
                print(f"Current active user: {current}")
            else:
                print("No user is currently active.")
        elif args.user_action == "list":
            if user_manager.data:
                print("Known users:")
                for uname, status in user_manager.data.items():
                    marker = "[signed]" if status == "signed" else "[unsigned]"
                    print(f"  {uname} {marker}")
            else:
                print("No users found.")
        
    elif args.command in ["add", "delete", "done", "list"]:
        active_username = user_manager.current_user 
        if active_username is None:
            print("Error: No active user selected. Please use 'user switch <username>' or 'user add <username>' first.")
            sys.exit(1)

        task_list_file_name = f".tasklist.{active_username}.json"
        task_manager = TaskList(task_list_file_name)
        task_manager.load()

        action_taken_on_tasks = True

        if args.command == "add":
            description = " ".join(args.description_parts)
            task_manager.add(description)
        elif args.command == "delete":
            task_manager.delete(args.task_number)
        elif args.command == "done":
            task_manager.done(args.task_number)
        elif args.command == "list":
            print(task_manager)
            action_taken_on_tasks = False
        
        if action_taken_on_tasks:
            task_manager.save()
            print(f"Task list for '{active_username}' saved.")
    else:
        print(f"Error: Unhandled command '{args.command}'. Use -h for help.")
        sys.exit(1)

if __name__ == "__main__":
    main()
