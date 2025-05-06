# TodoList

A simple command-line todo list manager written in C. This is my first standalone project, started on May 6th, 2025.

## Why?

Well, mostly because I needed a straightforward way to keep track of things. With any luck, this little app will help me (and maybe you!) scrape through midterms or just manage daily tasks without any fuss.

## Features

* **Add tasks**: Add new items to your todo list.
* **List tasks**: View all current tasks.
* **Clear tasks**: Remove all tasks from the list.
* **Help**: Display usage information.

## Project Structure

Here's how the files are laid out:

```
.
├── LICENSE           # Contains the GNU GPLv3 License text
├── build             # Directory for the compiled executable and data file
│   ├── list.txt      # The file where tasks are stored (created/used here if running from root and executable is in build/)
│   └── todo          # The compiled executable
└── todo.c            # The C source code
```
*(Note: `list.txt` will be created/accessed in the directory from which you run the `./build/todo` executable. If you run it from the project root, `list.txt` will appear in the `build` directory as shown.)*

## Building

To build the project, you'll need a C compiler like GCC.

1.  Navigate to the project's root directory (where `todo.c` and `LICENSE` are).
2.  Run the following command in your terminal:

    ```bash
    # This command compiles todo.c and places the executable 'todo' into the 'build' directory.
    # Make sure the 'build' directory exists, or create it first: mkdir -p build
    gcc -o build/todo todo.c
    ```

## Usage

After building the project, the executable will be located at `build/todo`. You can run it from the project's root directory.

**Add a new task:**
```bash
./build/todo add "Your new awesome task description here"
```
Example: `./build/todo add "Finish README for TodoList"`

**List all tasks:**
```bash
./build/todo list
```

**Clear all tasks:**
This will remove all tasks from `list.txt`.
```bash
./build/todo clear
```

**Show help message:**
Displays the available commands and how to use them.
```bash
./build/todo help
```

## License

This project is licensed under the GNU General Public License v3.0.
A copy of the license is included in the `LICENSE` file in this repository.

---

Alright, that's the lowdown on this little app. This README was whipped up with a dash of AI assistance 'cause, you know, time's a bit tight with everything مبلغ (that's "everything" in Persian, just for kicks, though I actually mean "everything" as in, well, *everything*). Gotta manage those todos, not just write about 'em, right? 😉
