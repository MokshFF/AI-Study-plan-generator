"""Validation Module for AI-Powered Personalized Study Plan Generator.

Problem ID: C20 - Bennett University Prompt Engineering Mini-Project
Separation of Concerns: Independent pure-Python input and output validation.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple

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


def extract_and_parse_json(text: str) -> Optional[Any]:
    """Robust JSON extractor handling markdown code fences or conversational wrappers."""
    clean = text.strip()
    # 1. Direct parse
    try:
        return json.loads(clean)
    except Exception:
        pass

    # 2. Extract from markdown code fences ```json ... ``` or ``` ... ```
    if "```" in clean:
        pattern = r"```(?:json)?\s*([\s\S]*?)\s*```"
        matches = re.findall(pattern, clean, re.IGNORECASE)
        for m in matches:
            try:
                return json.loads(m.strip())
            except Exception:
                continue

    # 3. Bracket extraction: first '{' to last '}'
    first_brace = clean.find("{")
    last_brace = clean.rfind("}")
    if first_brace != -1 and last_brace > first_brace:
        snippet = clean[first_brace : last_brace + 1]
        try:
            return json.loads(snippet)
        except Exception:
            pass

    # 4. Array extraction: first '[' to last ']'
    first_bracket = clean.find("[")
    last_bracket = clean.rfind("]")
    if first_bracket != -1 and last_bracket > first_bracket:
        snippet = clean[first_bracket : last_bracket + 1]
        try:
            return json.loads(snippet)
        except Exception:
            pass

    return None


def extract_markdown_table_schedule(text: str) -> Optional[List[Dict[str, Any]]]:
    """Extracts schedule records from a markdown table (e.g. from V1 baseline)."""
    lines = [l.strip() for l in text.splitlines() if "|" in l]
    if len(lines) < 2:
        return None

    header_idx = -1
    headers: List[str] = []
    for idx, l in enumerate(lines):
        parts = [p.strip().lower() for p in l.split("|")[1:-1]]
        if any("date" in p for p in parts) and any("subject" in p for p in parts):
            header_idx = idx
            headers = parts
            break

    if header_idx == -1 or header_idx + 1 >= len(lines):
        return None

    date_col = next((i for i, h in enumerate(headers) if "date" in h), 0)
    subj_col = next((i for i, h in enumerate(headers) if "subject" in h), 1)
    task_col = next((i for i, h in enumerate(headers) if any(k in h for k in ["task", "topic", "description"])), 2)
    dur_col = next((i for i, h in enumerate(headers) if any(k in h for k in ["dur", "min", "time"])), 3)

    days_map: Dict[str, List[Dict[str, Any]]] = {}
    for l in lines[header_idx + 1:]:
        if "---" in l:
            continue
        parts = [p.strip() for p in l.split("|")[1:-1]]
        if len(parts) <= max(date_col, subj_col):
            continue
        d_raw = parts[date_col] if date_col < len(parts) else ""
        d_p = parse_date(d_raw)
        if not d_p:
            continue
        iso_d = d_p.isoformat()
        sub_raw = parts[subj_col] if subj_col < len(parts) else ""
        task_raw = parts[task_col] if task_col < len(parts) else "General Revision"
        dur_str = parts[dur_col] if dur_col < len(parts) else "60"
        m_dur = re.search(r"\d+", dur_str)
        dur_int = int(m_dur.group()) if m_dur else 60

        if iso_d not in days_map:
            days_map[iso_d] = []
        days_map[iso_d].append({
            "subject": sub_raw,
            "activity": "Practice",
            "task": task_raw,
            "duration_minutes": dur_int,
        })

    if days_map:
        return [{"date": k, "sessions": v} for k, v in days_map.items()]
    return None


def repair_plan_dict(
    raw_data: Any,
    plan_input: StudyPlanInput,
) -> Tuple[Dict[str, Any], List[str]]:
    """Intelligent Auto-Repair & Normalization Engine for Study Plans.

    Repairs common Small Language Model (e.g. 1.5B/3B) artifacts:
    1. Key schema normalization ('daily_plan', 'timetable', 'days' -> 'schedule')
    2. Ensures all planning dates are present
    3. Enforces zero sessions on 0-minute rest days
    4. Resolves daily budget overruns by clamping/adjusting session durations
    5. Resolves post-exam violations by reassigning to active upcoming subjects
    6. Maps unknown/fuzzy activity names to ALLOWED_ACTIVITIES
    7. Maps fuzzy subject names/acronyms to declared SubjectInput names
    8. Fixes non-positive durations (minimum 15 minutes)
    """
    notes: List[str] = []

    # 1. Normalize root container to list of day entries
    repaired_schedule_raw: List[Any] = []
    if isinstance(raw_data, list):
        repaired_schedule_raw = raw_data
        notes.append("Auto-aligned schema: converted top-level array into 'schedule' object.")
    elif isinstance(raw_data, dict):
        if "schedule" in raw_data and isinstance(raw_data["schedule"], list):
            repaired_schedule_raw = raw_data["schedule"]
        else:
            alt_keys = [
                "daily_schedule", "study_plan", "timetable", "days",
                "calendar", "plan", "sessions", "schedule_list", "items"
            ]
            found = False
            for k in alt_keys:
                if k in raw_data and isinstance(raw_data[k], list):
                    repaired_schedule_raw = raw_data[k]
                    notes.append(f"Auto-aligned schema: normalized root key '{k}' into 'schedule'.")
                    found = True
                    break
            if not found:
                for v in raw_data.values():
                    if isinstance(v, list) and v and isinstance(v[0], dict):
                        repaired_schedule_raw = v
                        notes.append("Auto-aligned schema: extracted schedule array from nested structure.")
                        found = True
                        break
    else:
        repaired_schedule_raw = []

    # 2. Build canonical subject mapping and exam dates
    declared_subjects = plan_input.subjects
    subject_canonical_map: Dict[str, str] = {}
    exam_dates_map: Dict[str, date] = {}
    for s in declared_subjects:
        c_name = s.name.strip()
        subject_canonical_map[c_name.lower()] = c_name
        ed = parse_date(s.exam_date)
        if ed:
            exam_dates_map[c_name.lower()] = ed

        words = [w.lower() for w in re.findall(r"\b[A-Za-z]+\b", c_name)]
        if len(words) > 1:
            acronym = "".join(w[0] for w in words)
            if acronym not in subject_canonical_map:
                subject_canonical_map[acronym] = c_name
        for w in words:
            if len(w) >= 3 and w not in subject_canonical_map:
                subject_canonical_map[w] = c_name

    known_aliases = {
        "dsa": "Data Structures & Algorithms",
        "dbms": "Database Management Systems",
        "os": "Operating Systems",
        "nlp": "Natural Language Processing",
        "algo": "Data Structures & Algorithms",
        "database": "Database Management Systems",
        "databases": "Database Management Systems",
        "data base": "Database Management Systems",
        "data structures": "Data Structures & Algorithms",
        "operating systems": "Operating Systems",
    }
    for alias, full in known_aliases.items():
        for s in declared_subjects:
            if full.lower() == s.name.lower():
                subject_canonical_map[alias] = s.name

    allowed_act_canonical: Dict[str, str] = {a.lower(): a for a in ALLOWED_ACTIVITIES}

    def normalize_activity(act: str) -> str:
        cleaned = str(act).strip().lower()
        if cleaned in allowed_act_canonical:
            return allowed_act_canonical[cleaned]
        if any(k in cleaned for k in ["pract", "code", "coding", "exercise", "solve"]):
            return "Practice"
        if any(k in cleaned for k in ["revis", "review", "summary"]):
            return "Revision"
        if any(k in cleaned for k in ["theor", "concept", "read", "lecture", "study"]):
            return "Theory"
        if any(k in cleaned for k in ["mock", "test", "quiz", "exam", "paper"]):
            return "Mock Test"
        if any(k in cleaned for k in ["problem"]):
            return "Problem Solving"
        if any(k in cleaned for k in ["note"]):
            return "Note Review"
        return "Practice"

    def match_subject(raw_sub: str, date_val: Optional[date]) -> str:
        cleaned = str(raw_sub).strip().lower()
        if cleaned in subject_canonical_map:
            return subject_canonical_map[cleaned]
        for k, v in subject_canonical_map.items():
            if k in cleaned or cleaned in k:
                return v
        if date_val:
            eligible = [
                s.name for s in declared_subjects
                if parse_date(s.exam_date) and date_val <= parse_date(s.exam_date)
            ]
            if eligible:
                return eligible[0]
        return declared_subjects[0].name if declared_subjects else "General Study"

    # 3. Organize entries by date
    expected_dates = plan_input.get_date_range()
    days_by_date: Dict[str, List[Dict[str, Any]]] = {d: [] for d in expected_dates}

    for day_item in repaired_schedule_raw:
        if not isinstance(day_item, dict):
            continue
        d_str = day_item.get("date") or day_item.get("day") or day_item.get("date_str") or ""
        d_parsed = parse_date(str(d_str))
        if not d_parsed:
            continue
        iso_d = d_parsed.isoformat()
        if iso_d in days_by_date:
            raw_sessions = (
                day_item.get("sessions") or day_item.get("tasks") or day_item.get("activities") or []
            )
            if isinstance(raw_sessions, list):
                days_by_date[iso_d].extend(raw_sessions)

    # 4. Construct normalized schedule day by day
    normalized_schedule: List[Dict[str, Any]] = []

    for d_iso in expected_dates:
        cur_date = parse_date(d_iso)
        daily_budget = plan_input.get_budget_for_date(d_iso)
        raw_sessions = days_by_date[d_iso]

        # Rule 7: Zero-minute rest days
        if daily_budget == 0:
            if raw_sessions:
                notes.append(
                    f"Auto-aligned on {d_iso}: Cleared {len(raw_sessions)} session(s) to enforce scheduled rest day (0 min budget)."
                )
            normalized_schedule.append({"date": d_iso, "sessions": []})
            continue

        # Eligible subjects for this date
        eligible_subjects = [
            s.name for s in declared_subjects
            if parse_date(s.exam_date) and cur_date <= parse_date(s.exam_date)
        ]

        repaired_sessions: List[Dict[str, Any]] = []
        for s_raw in raw_sessions:
            if not isinstance(s_raw, dict):
                continue

            sub_raw = s_raw.get("subject") or s_raw.get("name") or s_raw.get("course") or ""
            act_raw = s_raw.get("activity") or s_raw.get("type") or s_raw.get("category") or "Practice"
            task_raw = s_raw.get("task") or s_raw.get("topic") or s_raw.get("description") or "Core syllabus review"
            dur_raw = s_raw.get("duration_minutes") or s_raw.get("duration") or s_raw.get("minutes") or 60

            canonical_sub = match_subject(sub_raw, cur_date)

            # Check post-exam constraint
            exam_d = exam_dates_map.get(canonical_sub.lower()) if canonical_sub else None
            if exam_d and cur_date and cur_date > exam_d:
                if eligible_subjects:
                    weak_eligible = [sub for sub in eligible_subjects if sub in plan_input.weak_subjects]
                    replacement_sub = weak_eligible[0] if weak_eligible else eligible_subjects[0]
                    notes.append(
                        f"Auto-aligned on {d_iso}: Reallocated study session for '{canonical_sub}' "
                        f"(exam passed {exam_d.isoformat()}) to upcoming subject '{replacement_sub}'."
                    )
                    canonical_sub = replacement_sub
                else:
                    notes.append(
                        f"Auto-aligned on {d_iso}: Omitted session for '{canonical_sub}' as all exams have concluded."
                    )
                    continue

            try:
                dur_int = int(dur_raw)
            except (ValueError, TypeError):
                dur_int = 45
            if dur_int <= 0:
                dur_int = 30
                notes.append(f"Auto-aligned on {d_iso}: Corrected non-positive duration to 30m.")

            canonical_act = normalize_activity(act_raw)

            repaired_sessions.append({
                "subject": canonical_sub,
                "activity": canonical_act,
                "task": str(task_raw).strip() or "Syllabus review & problem solving",
                "duration_minutes": dur_int,
            })

        # Synthesize default sessions if model produced 0 sessions on an active study day
        if not repaired_sessions and eligible_subjects:
            half_b = daily_budget // 2
            if half_b >= 30:
                repaired_sessions.append({
                    "subject": eligible_subjects[0],
                    "activity": "Theory",
                    "task": "Core concept revision and formula recall",
                    "duration_minutes": half_b,
                })
                repaired_sessions.append({
                    "subject": eligible_subjects[1] if len(eligible_subjects) > 1 else eligible_subjects[0],
                    "activity": "Practice",
                    "task": "Practice questions and past exam problem solving",
                    "duration_minutes": daily_budget - half_b,
                })
            else:
                repaired_sessions.append({
                    "subject": eligible_subjects[0],
                    "activity": "Revision",
                    "task": "Targeted exam revision and summary review",
                    "duration_minutes": daily_budget,
                })
            notes.append(
                f"Auto-aligned on {d_iso}: Generated default study sessions to allocate {daily_budget}m available budget."
            )

        # Budget Overrun check & clamping (Rule 8)
        total_mins = sum(s["duration_minutes"] for s in repaired_sessions)
        if total_mins > daily_budget:
            overrun = total_mins - daily_budget
            # Deduct from the last session if it can absorb the overrun
            if repaired_sessions and repaired_sessions[-1]["duration_minutes"] - overrun >= 15:
                repaired_sessions[-1]["duration_minutes"] -= overrun
            else:
                # Proportional scaling
                factor = daily_budget / float(total_mins)
                acc = 0
                for s in repaired_sessions[:-1]:
                    s["duration_minutes"] = max(15, int(s["duration_minutes"] * factor))
                    acc += s["duration_minutes"]
                if repaired_sessions:
                    repaired_sessions[-1]["duration_minutes"] = max(15, daily_budget - acc)

            new_total = sum(s["duration_minutes"] for s in repaired_sessions)
            if new_total > daily_budget and repaired_sessions:
                repaired_sessions[-1]["duration_minutes"] = max(15, repaired_sessions[-1]["duration_minutes"] - (new_total - daily_budget))
                new_total = sum(s["duration_minutes"] for s in repaired_sessions)

            notes.append(
                f"Auto-aligned on {d_iso}: Adjusted total duration from {total_mins}m to {new_total}m "
                f"to strictly satisfy daily budget ({daily_budget}m)."
            )

        normalized_schedule.append({
            "date": d_iso,
            "sessions": repaired_sessions,
        })

    return {"schedule": normalized_schedule}, notes


def validate_plan_output(
    raw_response: str,
    plan_input: StudyPlanInput,
    auto_repair: bool = False,
) -> ValidationResult:
    """Validates the LLM generated response against strict study planning rules.

    Args:
        raw_response: Raw text response from model or test fixture.
        plan_input: User study plan input parameters.
        auto_repair: If True, automatically repairs schema discrepancies, budget overruns,
                     post-exam violations, and rest-day conflicts to produce a valid schedule.
                     Defaults to False (strict evaluation).

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

    clean_text = raw_response.strip()

    if auto_repair:
        parsed_data = extract_and_parse_json(clean_text)
        if parsed_data is None:
            tbl_sched = extract_markdown_table_schedule(clean_text)
            if tbl_sched:
                parsed_data = tbl_sched
            else:
                parsed_data = []

        repaired_dict, repair_notes = repair_plan_dict(parsed_data, plan_input)
        data = repaired_dict
        warnings.extend(repair_notes)
    else:
        # Strict parsing
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

    schedule_list = data.get("schedule") if isinstance(data, dict) else None
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
