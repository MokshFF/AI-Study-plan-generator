"""Validation Module for AI-Powered Personalized Study Plan Generator.

Problem ID: C20 - Bennett University Prompt Engineering Mini-Project
Separation of Concerns: Independent pure-Python input and output validation.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Set

# Standard recognized academic activity types
ALLOWED_ACTIVITIES: Set[str] = {
    "Theory",
    "Practice",
    "Revision",
    "Mock Test",
    "Problem Solving",
    "Note Review",
}


@dataclass
class SubjectInput:
    """Represents a student subject and its scheduled exam date."""
    name: str
    exam_date: str  # YYYY-MM-DD


@dataclass
class StudyPlanInput:
    """User input data model for the study planner."""
    start_date: str  # YYYY-MM-DD
    end_date: str  # YYYY-MM-DD
    subjects: List[SubjectInput]
    default_daily_minutes: int
    daily_overrides: Dict[str, int] = field(default_factory=dict)  # YYYY-MM-DD -> minutes
    weak_subjects: List[str] = field(default_factory=list)
    weak_topics: str = ""
    preferences: str = ""

    def get_budget_for_date(self, target_date: str) -> int:
        """Returns the minute budget for a specific date (overridden or default)."""
        return self.daily_overrides.get(target_date, self.default_daily_minutes)

    def get_date_range(self) -> List[str]:
        """Returns list of all ISO date strings in [start_date, end_date]."""
        start = datetime.strptime(self.start_date, "%Y-%m-%d").date()
        end = datetime.strptime(self.end_date, "%Y-%m-%d").date()
        cur = start
        dates = []
        while cur <= end:
            dates.append(cur.isoformat())
            cur += timedelta(days=1)
        return dates


@dataclass
class StudySession:
    """Individual study session in a daily plan."""
    subject: str
    activity: str
    task: str
    duration_minutes: int


@dataclass
class DaySchedule:
    """Schedule for a single calendar day."""
    date: str
    available_minutes: int
    used_minutes: int
    sessions: List[StudySession] = field(default_factory=list)


@dataclass
class ValidationResult:
    """Result of validation containing error messages, warnings, and parsed data."""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    schedule: List[DaySchedule] = field(default_factory=list)
    raw_json: Optional[Any] = None


def parse_date(date_str: str) -> Optional[date]:
    """Helper to parse YYYY-MM-DD date strings safely."""
    try:
        return datetime.strptime(date_str.strip(), "%Y-%m-%d").date()
    except (ValueError, AttributeError):
        return None


def validate_inputs(plan_input: StudyPlanInput) -> List[str]:
    """Validates user form inputs before invoking the Ollama model.

    Rules enforced:
    1. Start date and end date must be valid ISO dates.
    2. Start date must be <= end date (no reversed range).
    3. At least one subject must be provided.
    4. Subjects must not be blank or whitespace-only.
    5. Subjects must not have duplicate names (case-insensitive).
    6. Subject exam dates must be valid and >= start_date.
    7. Default daily minutes cannot be negative.
    8. Overridden minutes cannot be negative.
    9. Weak subjects must belong to the declared subject list.
    """
    errors: List[str] = []

    # 1 & 2. Date range validation
    start = parse_date(plan_input.start_date)
    end = parse_date(plan_input.end_date)
    if not start:
        errors.append(f"Invalid planning start date: '{plan_input.start_date}'. Must be YYYY-MM-DD.")
    if not end:
        errors.append(f"Invalid planning end date: '{plan_input.end_date}'. Must be YYYY-MM-DD.")

    if start and end and start > end:
        errors.append(
            f"Planning date range is reversed: start date ({plan_input.start_date}) "
            f"cannot be after end date ({plan_input.end_date})."
        )

    # 3, 4, 5, 6. Subjects validation
    if not plan_input.subjects:
        errors.append("At least one subject must be provided.")

    seen_subjects_lower: Set[str] = set()
    declared_subjects: Set[str] = set()

    for idx, subj in enumerate(plan_input.subjects, 1):
        clean_name = subj.name.strip()
        if not clean_name:
            errors.append(f"Subject #{idx} has a blank name.")
            continue

        lower_name = clean_name.lower()
        if lower_name in seen_subjects_lower:
            errors.append(f"Duplicate subject name detected: '{clean_name}'.")
        seen_subjects_lower.add(lower_name)
        declared_subjects.add(clean_name)

        exam_d = parse_date(subj.exam_date)
        if not exam_d:
            errors.append(
                f"Subject '{clean_name}' has an invalid exam date: '{subj.exam_date}'. Must be YYYY-MM-DD."
            )
        elif start and exam_d < start:
            errors.append(
                f"Subject '{clean_name}' has an exam date ({subj.exam_date}) before the planning start date ({plan_input.start_date})."
            )

    # 7 & 8. Daily budget validation
    if plan_input.default_daily_minutes < 0:
        errors.append(
            f"Default daily study budget cannot be negative (received {plan_input.default_daily_minutes} minutes)."
        )

    for o_date, o_mins in plan_input.daily_overrides.items():
        if o_mins < 0:
            errors.append(
                f"Date override for {o_date} cannot be negative (received {o_mins} minutes)."
            )

    # 9. Weak subjects validation
    for weak_sub in plan_input.weak_subjects:
        if weak_sub not in declared_subjects:
            errors.append(
                f"Unknown weak subject: '{weak_sub}' was not found in declared subjects list."
            )

    return errors


def validate_plan_output(
    raw_response: str,
    plan_input: StudyPlanInput,
) -> ValidationResult:
    """Validates the LLM generated response against strict study planning rules.

    Rules enforced:
    1. Reject malformed JSON.
    2. Must contain a 'schedule' list of daily entries.
    3. Missing or duplicate dates: Every calendar date in [start_date, end_date]
       must appear exactly once.
    4. Unknown subjects: Sessions can only use declared subjects.
    5. Non-positive durations: Session duration must be an integer > 0.
    6. Unrecognized activity types: Must belong to ALLOWED_ACTIVITIES.
    7. Sessions on zero-minute days: Days with 0 available minutes must have 0 sessions.
    8. Daily budget overruns: Total session duration on any date must not exceed
       the available daily budget.
    9. Post-exam scheduling: No session for subject S may be scheduled after S's exam date.
       * Date-level rule: Sessions on the exam date itself (session_date <= exam_date) ARE allowed.
    """
    errors: List[str] = []
    warnings: List[str] = []

    # 1. Reject malformed JSON
    clean_text = raw_response.strip()
    # Strip markdown code blocks if present (```json ... ```)
    if clean_text.startswith("```"):
        lines = clean_text.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        clean_text = "\n".join(lines).strip()

    try:
        data = json.loads(clean_text)
    except Exception as exc:
        return ValidationResult(
            is_valid=False,
            errors=[f"Malformed JSON output from model: {exc}"],
            warnings=[],
            schedule=[],
            raw_json=None,
        )

    if not isinstance(data, dict):
        return ValidationResult(
            is_valid=False,
            errors=["Root JSON response must be an object/dictionary containing a 'schedule' key."],
            warnings=[],
            schedule=[],
            raw_json=data,
        )

    schedule_list = data.get("schedule")
    if not isinstance(schedule_list, list):
        return ValidationResult(
            is_valid=False,
            errors=["Missing or invalid 'schedule' array in JSON response."],
            warnings=[],
            schedule=[],
            raw_json=data,
        )

    # Build reference lookup mappings
    expected_dates = plan_input.get_date_range()
    expected_dates_set = set(expected_dates)
    subject_map: Dict[str, SubjectInput] = {s.name.lower(): s for s in plan_input.subjects}
    exam_dates: Dict[str, date] = {
        s.name.lower(): datetime.strptime(s.exam_date, "%Y-%m-%d").date()
        for s in plan_input.subjects
        if parse_date(s.exam_date) is not None
    }
    allowed_activities_lower = {a.lower(): a for a in ALLOWED_ACTIVITIES}

    seen_dates: Set[str] = set()
    parsed_schedule: List[DaySchedule] = []

    # Track subject coverage for warnings
    subject_session_counts: Dict[str, int] = {s.name: 0 for s in plan_input.subjects}
    subject_total_minutes: Dict[str, int] = {s.name: 0 for s in plan_input.subjects}

    for day_idx, day_entry in enumerate(schedule_list, 1):
        if not isinstance(day_entry, dict):
            errors.append(f"Day entry #{day_idx} is not a valid JSON object.")
            continue

        day_date_str = day_entry.get("date")
        if not day_date_str or not isinstance(day_date_str, str):
            errors.append(f"Day entry #{day_idx} is missing a valid 'date' field.")
            continue

        day_date = parse_date(day_date_str)
        if not day_date:
            errors.append(f"Invalid date format in schedule: '{day_date_str}'. Expected YYYY-MM-DD.")
            continue

        # Check date range membership
        if day_date_str not in expected_dates_set:
            errors.append(
                f"Unexpected date '{day_date_str}' in schedule. Must be between {plan_input.start_date} and {plan_input.end_date}."
            )

        # Check duplicate date
        if day_date_str in seen_dates:
            errors.append(f"Duplicate date entry found in schedule: '{day_date_str}'.")
        seen_dates.add(day_date_str)

        # Daily budget check
        available_budget = plan_input.get_budget_for_date(day_date_str)
        sessions_raw = day_entry.get("sessions", [])

        if not isinstance(sessions_raw, list):
            errors.append(f"Day '{day_date_str}' has invalid 'sessions' field (must be a list).")
            sessions_raw = []

        day_sessions: List[StudySession] = []
        day_used_minutes = 0

        # Rule 7: Zero-minute days must have no study sessions
        if available_budget == 0 and len(sessions_raw) > 0:
            errors.append(
                f"Date {day_date_str} is configured as a rest day (0 available minutes), "
                f"but contains {len(sessions_raw)} study session(s)."
            )

        for s_idx, session_item in enumerate(sessions_raw, 1):
            if not isinstance(session_item, dict):
                errors.append(f"Date {day_date_str}, Session #{s_idx} is not a valid object.")
                continue

            raw_subject = session_item.get("subject", "")
            raw_activity = session_item.get("activity", "")
            raw_task = session_item.get("task", "")
            raw_duration = session_item.get("duration_minutes")

            # 4. Unknown subject
            clean_sub = str(raw_subject).strip()
            matched_subject = subject_map.get(clean_sub.lower())
            if not matched_subject:
                errors.append(
                    f"Date {day_date_str}, Session #{s_idx}: Unknown subject '{clean_sub}'. "
                    f"Allowed subjects are: {list(subject_map.values())[0].name if subject_map else ''}..."
                )
                canonical_subject_name = clean_sub
            else:
                canonical_subject_name = matched_subject.name

            # 5. Non-positive duration
            if not isinstance(raw_duration, int) or raw_duration <= 0:
                errors.append(
                    f"Date {day_date_str}, Session #{s_idx} for '{clean_sub}': "
                    f"Duration must be an integer > 0 minutes (got {raw_duration})."
                )
                valid_duration = 0
            else:
                valid_duration = raw_duration

            # 6. Unrecognized activity type
            clean_act = str(raw_activity).strip()
            matched_act = allowed_activities_lower.get(clean_act.lower())
            if not matched_act:
                errors.append(
                    f"Date {day_date_str}, Session #{s_idx}: Unrecognized activity type '{clean_act}'. "
                    f"Allowed activities: {sorted(list(ALLOWED_ACTIVITIES))}."
                )
                canonical_activity = clean_act
            else:
                canonical_activity = matched_act

            # 9. Post-exam scheduling check
            # Prototype Date-Level Rule: sessions on the exam date itself (session_date <= exam_date) ARE allowed.
            if matched_subject and matched_subject.name.lower() in exam_dates:
                exam_d = exam_dates[matched_subject.name.lower()]
                if day_date > exam_d:
                    errors.append(
                        f"Post-Exam Scheduling Violation on {day_date_str}: Study session for '{matched_subject.name}' "
                        f"is scheduled after its exam date ({exam_d.isoformat()}). "
                        f"(Note: Date-level rule permits study on or before exam day, but strictly forbids study after)."
                    )

            day_used_minutes += valid_duration
            if matched_subject:
                subject_session_counts[matched_subject.name] += 1
                subject_total_minutes[matched_subject.name] += valid_duration

            day_sessions.append(
                StudySession(
                    subject=canonical_subject_name,
                    activity=canonical_activity,
                    task=str(raw_task).strip(),
                    duration_minutes=valid_duration,
                )
            )

        # 8. Daily budget overrun
        if day_used_minutes > available_budget:
            errors.append(
                f"Budget Overrun on {day_date_str}: Total study duration ({day_used_minutes} min) "
                f"exceeds the available daily budget of {available_budget} minutes "
                f"(overrun of {day_used_minutes - available_budget} min)."
            )

        # Warnings for unused time (if budget > 0 and unused > 60 min)
        if available_budget > 0 and (available_budget - day_used_minutes) >= 60:
            warnings.append(
                f"Under-utilization on {day_date_str}: {available_budget - day_used_minutes} minutes "
                f"of available study time remained unallocated."
            )

        parsed_schedule.append(
            DaySchedule(
                date=day_date_str,
                available_minutes=available_budget,
                used_minutes=day_used_minutes,
                sessions=day_sessions,
            )
        )

    # 3. Missing dates check
    missing_dates = expected_dates_set - seen_dates
    if missing_dates:
        sorted_missing = sorted(list(missing_dates))
        errors.append(
            f"Missing date(s) in study plan: {', '.join(sorted_missing)}. "
            f"All {len(expected_dates)} dates in the planning window must be accounted for."
        )

    # Sort parsed schedule chronologically
    parsed_schedule.sort(key=lambda d: d.date)

    # Planning Warnings:
    # Check subjects with zero allocated time
    for subj_name, count in subject_session_counts.items():
        if count == 0:
            warnings.append(f"Subject '{subj_name}' has 0 scheduled study sessions across the entire plan.")

    # Check weak subjects priority
    for weak_sub in plan_input.weak_subjects:
        mins = subject_total_minutes.get(weak_sub, 0)
        if mins == 0:
            warnings.append(
                f"Weak Subject Warning: '{weak_sub}' was identified as a weak subject but received 0 study minutes."
            )

    is_valid = len(errors) == 0
    return ValidationResult(
        is_valid=is_valid,
        errors=errors,
        warnings=warnings,
        schedule=parsed_schedule,
        raw_json=data,
    )
