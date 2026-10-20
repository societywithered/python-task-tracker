#!/usr/bin/env python3
"""A small, persistent task manager for the command line."""

from __future__ import annotations

import json
import sys
from dataclasses import asdict, dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Optional

DATA_FILE = Path(__file__).with_name("tasks.json")
PRIORITIES = {"low": 1, "medium": 2, "high": 3}


@dataclass
class Task:
    id: int
    title: str
    priority: str = "medium"
    due_date: Optional[str] = None
    done: bool = False
    created_at: str = ""


def load_tasks() -> list[Task]:
    """Load tasks from disk, or start with an empty list."""
    if not DATA_FILE.exists():
        return []

    try:
        raw_tasks = json.loads(DATA_FILE.read_text(encoding="utf-8"))
        return [Task(**item) for item in raw_tasks]
    except (json.JSONDecodeError, TypeError, KeyError) as error:
        print(f"Could not read {DATA_FILE.name}: {error}", file=sys.stderr)
        return []


def save_tasks(tasks: list[Task]) -> None:
    """Save tasks safely, avoiding a half-written data file."""
    temporary_file = DATA_FILE.with_suffix(".tmp")
    temporary_file.write_text(
        json.dumps([asdict(task) for task in tasks], indent=2),
        encoding="utf-8",
    )
    temporary_file.replace(DATA_FILE)


def next_id(tasks: list[Task]) -> int:
    return max((task.id for task in tasks), default=0) + 1


def ask_due_date() -> Optional[str]:
    value = input("Due date (YYYY-MM-DD, or leave blank): ").strip()
    if not value:
        return None

    try:
        return date.fromisoformat(value).isoformat()
    except ValueError:
        print("That date doesn't look right. The task will have no due date.")
        return None


def add_task(tasks: list[Task]) -> None:
    title = input("Task title: ").strip()
    if not title:
        print("A task needs a title.")
        return

    priority = input("Priority (low/medium/high) [medium]: ").strip().lower()
    if not priority:
        priority = "medium"
    if priority not in PRIORITIES:
        print("Unknown priority; using medium.")
        priority = "medium"

    task = Task(
        id=next_id(tasks),
        title=title,
        priority=priority,
        due_date=ask_due_date(),
        created_at=datetime.now().isoformat(timespec="seconds"),
    )
    tasks.append(task)
    save_tasks(tasks)
    print(f"Added task #{task.id}.")


def format_task(task: Task) -> str:
    checkbox = "x" if task.done else " "
    due = f" | due {task.due_date}" if task.due_date else ""
    return (
        f"[{checkbox}] #{task.id:<3} "
        f"{task.title} "
        f"({task.priority}){due}"
    )


def list_tasks(
    tasks: list[Task],
    *,
    show_all: bool = False,
    sort_by_priority: bool = False,
) -> None:
    visible = tasks if show_all else [task for task in tasks if not task.done]

    if sort_by_priority:
        visible = sorted(
            visible,
            key=lambda task: (
                -PRIORITIES[task.priority],
                task.due_date or "9999-12-31",
            ),
        )
    else:
        visible = sorted(visible, key=lambda task: task.id)

    if not visible:
        print("Nothing to show.")
        return

    print()
    for task in visible:
        print(format_task(task))
    print(f"\n{len(visible)} task(s)")


def find_task(tasks: list[Task], task_id: int) -> Optional[Task]:
    return next((task for task in tasks if task.id == task_id), None)


def ask_task_id() -> Optional[int]:
    try:
        return int(input("Task ID: ").strip())
    except ValueError:
        print("Please enter a numeric task ID.")
        return None


def complete_task(tasks: list[Task]) -> None:
    list_tasks(tasks)
    task_id = ask_task_id()
    if task_id is None:
        return

    task = find_task(tasks, task_id)
    if task is None:
        print(f"No task with ID {task_id}.")
        return

    task.done = not task.done
    save_tasks(tasks)
    print(f"Marked task #{task.id} as {'done' if task.done else 'not done'}.")


def delete_task(tasks: list[Task]) -> None:
    list_tasks(tasks, show_all=True)
    task_id = ask_task_id()
    if task_id is None:
        return

    task = find_task(tasks, task_id)
    if task is None:
        print(f"No task with ID {task_id}.")
        return

    confirm = input(f"Delete “{task.title}”? (y/N): ").strip().lower()
    if confirm == "y":
        tasks.remove(task)
        save_tasks(tasks)
        print("Task deleted.")


def search_tasks(tasks: list[Task]) -> None:
    query = input("Search for: ").strip().casefold()
    matches = [task for task in tasks if query in task.title.casefold()]
    list_tasks(matches, show_all=True)


def show_overdue(tasks: list[Task]) -> None:
    today = date.today().isoformat()
    overdue = [
        task for task in tasks
        if not task.done and task.due_date and task.due_date < today
    ]
    if overdue:
        print("Overdue tasks:")
        list_tasks(overdue, show_all=True)
    else:
        print("You have no overdue tasks. Nice work!")


def print_menu() -> None:
    print(
        "\n=== TASK MANAGER ===\n"
        "1. Show open tasks\n"
        "2. Show all tasks\n"
        "3. Add a task\n"
        "4. Complete / reopen a task\n"
        "5. Delete a task\n"
        "6. Search tasks\n"
        "7. Show overdue tasks\n"
        "8. Show tasks by priority\n"
        "9. Quit"
    )


def main() -> None:
    tasks = load_tasks()
    actions = {
        "1": lambda: list_tasks(tasks),
        "2": lambda: list_tasks(tasks, show_all=True),
        "3": lambda: add_task(tasks),
        "4": lambda: complete_task(tasks),
        "5": lambda: delete_task(tasks),
        "6": lambda: search_tasks(tasks),
        "7": lambda: show_overdue(tasks),
        "8": lambda: list_tasks(tasks, sort_by_priority=True),
    }

    while True:
        print_menu()
        choice = input("Choose an option: ").strip()

        if choice == "9":
            print("See you next time.")
            break

        action = actions.get(choice)
        if action:
            action()
        else:
            print("Choose a number from 1 to 9.")


if __name__ == "__main__":
    main()