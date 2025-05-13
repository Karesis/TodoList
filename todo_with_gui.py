import tkinter as tk
import tkinter.messagebox as messagebox
import tkinter.font as tkFont
from task import Task, TaskList 

# -- Global Variables --
TASKS_DATA_FILE = ".todolist_data.json" 
task_list_manager = TaskList(TASKS_DATA_FILE)

# -- Functions --
def refresh_task_listbox():
    task_listbox.delete(0, tk.END) 
    if task_list_manager.list:
        for index, task_obj in enumerate(task_list_manager.list):
            done_marker = "[X]" if task_obj.done else "[ ]"
            display_text = f"{done_marker} {task_obj.content}" 
            task_listbox.insert(tk.END, display_text)
            if task_obj.done:
                task_listbox.itemconfig(index, {'fg': 'gray'}) 
            else:
                task_listbox.itemconfig(index, {'fg': 'black'}) 

def on_add_task_button_click():
    task_description = task_entry.get() 
    if not task_description:
        messagebox.showwarning("Input Error", "Task description cannot be empty.")
        return
    
    task_list_manager.add(task_description) 
    task_list_manager.save()                
    refresh_task_listbox()                  
    task_entry.delete(0, tk.END)            

def on_delete_task_button_click():
    selected_indices = task_listbox.curselection()
    if not selected_indices:
        messagebox.showwarning("No Selection", "Please select a task to delete.")
        return
    selected_index = selected_indices[0]
    task_content_to_delete = task_listbox.get(selected_index) 
    confirm = messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete this task?\n{task_content_to_delete}")
    if confirm:
        try:
            task_list_manager.delete(selected_index)
            task_list_manager.save()
            refresh_task_listbox()
        except IndexError:
             messagebox.showerror("Error", "Failed to delete task. It might have been already removed.")

def on_toggle_done_status_click():
    selected_indices = task_listbox.curselection()
    
    if not selected_indices:
        messagebox.showwarning("No Selection", "Please select a task to mark as done.")
        return
        
    selected_index = selected_indices[0] # 0-based index
    
    try:
        task_list_manager.change_status(selected_index) 
        
        task_list_manager.save()
        refresh_task_listbox()
        
    except IndexError:
        messagebox.showerror("Error", f"Cannot mark task: Invalid index {selected_index}.")
    except Exception as e:
        messagebox.showerror("Error", f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    # -- GUI Setup --
    root = tk.Tk()
    root.title("TodoList App - 0.1.4")
    root.geometry("700x600") 

    default_font_size = 15 
    app_font = tkFont.Font(size=default_font_size)
    label_font = tkFont.Font(size=default_font_size, weight="bold")
    button_font = tkFont.Font(size=default_font_size -1 )
    list_font = tkFont.Font(size=default_font_size)

    task_list_manager.load() 

    # -- Input Frame --
    input_frame = tk.Frame(root)
    input_frame.pack(pady=10, padx=10, fill=tk.X)
    instruction_label = tk.Label(input_frame, text="New Task:", font=label_font)
    instruction_label.pack(side=tk.LEFT, padx=(0, 5))
    task_entry = tk.Entry(input_frame, width=40, font=app_font) 
    task_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
    add_button = tk.Button(input_frame, text="Add Task", command=on_add_task_button_click, font=button_font)
    add_button.pack(side=tk.LEFT, padx=(5, 0))

    # -- List Frame --
    list_area_frame = tk.Frame(root) 
    list_area_frame.pack(pady=5, padx=10, fill=tk.BOTH, expand=True)
    scrollbar = tk.Scrollbar(list_area_frame, orient=tk.VERTICAL)
    task_listbox = tk.Listbox(list_area_frame, width=60, height=15, 
                               selectmode=tk.SINGLE, yscrollcommand=scrollbar.set, font=list_font)
    scrollbar.config(command=task_listbox.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y) 
    task_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True) 

    # -- Action Buttons Frame --
    action_frame = tk.Frame(root)
    action_frame.pack(pady=(5,10), padx=10, fill=tk.X, anchor='w')

    delete_button = tk.Button(action_frame, text="Delete Selected", command=on_delete_task_button_click, font=button_font)
    delete_button.pack(side=tk.LEFT, padx=5) 

    toggle_done_button = tk.Button(action_frame, text="Toggle Done/Pending", command=on_toggle_done_status_click, font=button_font)
    toggle_done_button.pack(side=tk.LEFT, padx=5)

    refresh_task_listbox() 
    # -- Start GUI --
    root.mainloop()
