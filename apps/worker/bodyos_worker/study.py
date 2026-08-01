from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class StudyCheckpoint:
    day: int
    action: str


CHECKPOINTS = {
    3: StudyCheckpoint(3, "stage_summary"),
    8: StudyCheckpoint(8, "stage_summary"),
    15: StudyCheckpoint(15, "stage_summary"),
    16: StudyCheckpoint(16, "request_full_reconciliation"),
}


def checkpoint_for(start_date: date, current_date: date) -> StudyCheckpoint | None:
    day = (current_date - start_date).days + 1
    return CHECKPOINTS.get(day)
