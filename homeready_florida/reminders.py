from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from .models import PropertyProfile


@dataclass(slots=True)
class ReminderTask:
    due_date: date
    title: str
    channel: str


def generate_monthly_reminders(profile: PropertyProfile, start: date, months: int = 3, channel: str = "email") -> list[ReminderTask]:
    tasks: list[ReminderTask] = []
    for month_offset in range(months):
        month = ((start.month - 1 + month_offset) % 12) + 1
        year = start.year + ((start.month - 1 + month_offset) // 12)
        due = date(year, month, min(start.day, 28))
        tasks.extend(
            [
                ReminderTask(due, "Test generator", channel),
                ReminderTask(due, "Replace A/C filter", channel),
                ReminderTask(due, "Inspect storm shutters", channel),
            ]
        )

    if profile.occupancy_status == "seasonal":
        tasks.append(ReminderTask(start, "Confirm departure checklist", channel))

    return tasks
