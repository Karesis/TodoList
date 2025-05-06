/*
 * todo - A simple command-line todo list manager
 * Copyright (C) 2025 杨亦锋
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <https://www.gnu.org/licenses/>.
 */

// My first standalone project, started on May 6th,2025.
// TodoList (command-line tool named 'todo'). With any luck, this app will help me scrape through my midterms.

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef enum {
	ADD,
	LIST,
	HELP,
	CLEAR,
	UNKNOWN
} CommandType;

CommandType get_command_type(const char*);
void add(int, const char*, const char*);
void list(int);
void help(const char*);
void clear(int);

int main(int argc, char* argv[]) {
    if (argc < 2) { 
        fprintf(stderr, "No command provided. Use '%s help' for usage.\n", argv[0]);
		exit(1);
    } else if (argc > 3) {
		fprintf(stderr, "Too many args are given.Use '%s help' for help.\n", argv[0]);
		exit(1);
	}

	CommandType command = get_command_type(argv[1]);
	
	switch (command) {
		case ADD:
			add(argc, argv[2], argv[0]);
			break;
		
		case LIST:
			list(argc);
			break;

		case HELP:
			help(argv[0]);
			break;
		
		case CLEAR:
			clear(argc);
			break;
		
		case UNKNOWN:
		default:
			fprintf(stderr, "Unknown command: '%s'. Use help for usage.\n", argv[1]);
		exit(1);
	}

    return 0; 
}	

CommandType get_command_type(const char* command_str) {
    if (strcmp(command_str, "add") == 0) {
        return ADD;
    } else if (strcmp(command_str, "list") == 0) {
        return LIST;
    } else if (strcmp(command_str, "help") == 0) {
        return HELP;
	} else if (strcmp(command_str, "clear") == 0) {
		return CLEAR;
    } else {
        return UNKNOWN;
    }
}

void add(int argc, const char* task, const char* app_name)
{
	if (argc < 3) {
		fprintf(stderr, "Usage: %s add \"<task description>\"\n", app_name);
		exit(1);
	}

	FILE* fp = fopen("list.txt", "a");
	if (fp == NULL) {
		perror("Error: Couldn't open list.txt for adding");
		exit(1);
	}
	fprintf(fp, "%s\n", task); 
	fclose(fp);
	printf("Task added: %s\n", task);
}

void list(int argc)
{
	if (argc > 2) {
		fprintf(stderr, "The list command cannot be followed by any arguments.\n");
		exit(1);
	}
    FILE* fp = fopen("list.txt", "r");
    if (fp == NULL) {
        fprintf(stderr, "Todo list is empty or cannot be opened.\n");
        exit(1); 
    }

    char line_buffer[256];
    int task_number = 1;

    printf("\n--- Your Todo List ---\n");
    while (fgets(line_buffer, sizeof(line_buffer), fp) != NULL) {
        printf("%d. %s", task_number++, line_buffer);
    }
    printf("--- End of List ---\n\n");

    fclose(fp);
}

void help(const char* app_name)
{
	printf("Todo List Application\n" 
           "Usage:\n" \
           "  %s add \"<task description>\"  - Adds a new task\n" 
           "  %s list                      - Lists all tasks\n" 
           "  %s help                      - Shows this help message\n"
           "  %s clear                     - Clear all tasks\n", 
           app_name, app_name, app_name, app_name);
}

void clear(int argc) 
{
	if (argc > 2) {
		fprintf(stderr, "The clear command cannot be followed by any arguments.\n");
		exit(1);
	}
	FILE* fp = fopen("list.txt", "w");
	if (fp == NULL) {
		perror("Error clearing tasks");
		exit(1);
	}
	fclose(fp);
	printf("All tasks cleared successfully.\n");
}
