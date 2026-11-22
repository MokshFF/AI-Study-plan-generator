"""Prompt Engineering Module Preserving Three Iterative Prompt Versions.

Problem ID: C20 - Bennett University Prompt Engineering Mini-Project
Prompt Progression:
- Version 1 (v1): Baseline Zero-Shot (Unconstrained baseline)
- Version 2 (v2): Few-Shot with JSON Schema (Missing negative guardrails)
- Version 3 (v3): Final Production Guardrail Template (Full constraints & date-level rule)
"""

from typing import List
from study_plan.validator import ALLOWED_ACTIVITIES, StudyPlanInput

PROMPT_VERSIONS = {
    "v3": "Version 3 (Final Optimized Guardrail Template - Recommended)",
    "v2": "Version 2 (Few-Shot with JSON Schema, No Guardrails)",
    "v1": "Version 1 (Zero-Shot Baseline, Unconstrained)",
}


def build_prompt_v1_baseline(plan_input: StudyPlanInput) -> str:
    """Prompt Version 1 (v1): Baseline Zero-Shot Prompt.

    Naive prompt without strict schema enforcement or negative guardrails.
    Used in Prompt Engineering mini-projects to establish baseline evaluation metrics.
    """
    subjects_str = ", ".join(s.name for s in plan_input.subjects)
    return f"""Make a study timetable for a university student.
Dates: from {plan_input.start_date} to {plan_input.end_date}.
Subjects: {subjects_str}.
Study minutes per day: {plan_input.default_daily_minutes}.
Weak areas: {", ".join(plan_input.weak_subjects)}.
Please provide a daily schedule in JSON with dates and sessions."""


def build_prompt_v2_fewshot_schema(plan_input: StudyPlanInput) -> str:
    """Prompt Version 2 (v2): Few-Shot Prompt with JSON Schema.

    Improves upon v1 by specifying JSON structure and exam dates, but lacks
    explicit negative guardrails (frequently violates post-exam rules or zero-minute rest days).
    """
    subjects_text = "\n".join(f"- {s.name} (Exam on {s.exam_date})" for s in plan_input.subjects)
    date_range = plan_input.get_date_range()

    return f"""You are an academic study planner.
Generate a daily study schedule in JSON from {plan_input.start_date} to {plan_input.end_date}.

Subjects and Exam Dates:
{subjects_text}

Default Study Minutes per Day: {plan_input.default_daily_minutes} minutes.
Weak Subjects: {", ".join(plan_input.weak_subjects) if plan_input.weak_subjects else "None"}

Please output JSON with the following structure:
{{
  "schedule": [
    {{
      "date": "YYYY-MM-DD",
      "sessions": [
        {{
          "subject": "Subject Name",
          "activity": "Theory/Practice/Revision",
          "task": "Specific task",
          "duration_minutes": 60
        }}
      ]
    }}
  ]
}}
Cover all {len(date_range)} days."""


def build_prompt_v3_optimized_guardrails(plan_input: StudyPlanInput) -> str:
    """Prompt Version 3 (v3): Final Production Guardrailed Template.

    Complete state-of-the-art prompt utilizing:
    1. Role & Persona Prompting
    2. Dynamic Context & Constraint Injection (Per-date eligible subjects grounding)
    3. Strict Negative Guardrails (Post-exam prohibition, zero-minute rest days, budget bounds)
    4. Date-Level Rule Justification (Pre-exam study allowed on exam day)
    5. Machine-parseable JSON grammar specification
    """
    date_range: List[str] = plan_input.get_date_range()

    # Build subjects summary
    subjects_text_lines = []
    for s in plan_input.subjects:
        subjects_text_lines.append(f"- Subject: '{s.name}' | Exam Date: {s.exam_date}")
    subjects_text = "\n".join(subjects_text_lines)

    # Build daily budgets and active subjects summary (Per-date Context Grounding)
    budgets_text_lines = []
    for d in date_range:
        budget = plan_input.get_budget_for_date(d)
        if budget == 0:
            budgets_text_lines.append(
                f"- Date {d}: 0 minutes available (ZERO-MINUTE REST DAYS / Day Off). "
                f'Allowed subjects: NONE. "sessions" MUST BE strictly empty []. '
                f'Exact required output for this date: {{"date": "{d}", "sessions": []}}'
            )
        else:
            allowed_subs = [s.name for s in plan_input.subjects if d <= s.exam_date]
            if budget % 60 == 0 and budget >= 120:
                arithmetic_hint = f"Exact session breakdown: 2 sessions of {budget // 2}m each, or {budget // 60} sessions of 60m"
            elif budget % 45 == 0 and budget >= 90:
                arithmetic_hint = f"Exact session breakdown: {budget // 45} sessions of 45m"
            else:
                arithmetic_hint = f"Total sum of durations must be <= {budget}m"

            budgets_text_lines.append(
                f"- Date {d}: Available budget is EXACTLY {budget} minutes. Allowed subjects: {allowed_subs}. "
                f"Schedule 1, 2 or 3 sessions ({arithmetic_hint}). Total duration across sessions MUST NOT exceed {budget} min."
            )
    budgets_text = "\n".join(budgets_text_lines)

    # Weak subjects and topics
    weak_subs_str = ", ".join(plan_input.weak_subjects) if plan_input.weak_subjects else "None specified"
    weak_topics_str = plan_input.weak_topics.strip() if plan_input.weak_topics.strip() else "None specified"
    preferences_str = plan_input.preferences.strip() if plan_input.preferences.strip() else "Standard university exam revision"

    allowed_activities_str = ", ".join(f'"{act}"' for act in sorted(list(ALLOWED_ACTIVITIES)))

    prompt = f"""You are an expert University Academic Advisor and Personalized Study Planner.
Your task is to generate a day-by-day personalized exam study plan for a university student.

=== STUDENT PROFILE & EXAM CONSTRAINTS ===
1. Planning Window: From {plan_input.start_date} to {plan_input.end_date} (Total: {len(date_range)} days).
2. Enrolled Subjects & Exam Schedule:
{subjects_text}

3. Daily Available Study Time Budgets & Allowed Subjects:
{budgets_text}

4. Identified Weak Subjects:
{weak_subs_str}

5. Specific Weak Topics / High Priority Focus Areas:
{weak_topics_str}

6. Student Preferences:
{preferences_str}

=== CRITICAL ACADEMIC PLANNING RULES (GUARDRAILS) ===
1. CHRONOLOGICAL COVERAGE:
   - You MUST output a daily schedule covering EVERY single date from {plan_input.start_date} to {plan_input.end_date} inclusive.
   - Do NOT omit any date, and do NOT duplicate dates.

2. ZERO-MINUTE REST DAYS:
   - Any date with an available budget of 0 minutes represents a scheduled DAY OFF.
   - For zero-minute days, the "sessions" list MUST be completely empty ([]), formatted as:
     {{"date": "YYYY-MM-DD", "sessions": []}}
   - Do NOT omit zero-minute dates from the "schedule" list!

3. STRICT DAILY TIME BUDGET (ZERO TOLERANCE FOR OVERRUNS):
   - On any given date, sum(duration_minutes) across all sessions MUST BE LESS THAN OR EQUAL TO that date's available budget.
   - Explicit daily arithmetic limits:
     * If budget is 180 min: use two 90m sessions (90+90=180), OR three 60m sessions (60+60+60=180), OR four 45m sessions (45*4=180).
     * If budget is 240 min: use two 120m sessions or four 60m sessions.
     * If budget is 210 min: use one 90m + two 60m sessions.
   - NEVER emit sessions summing to 195 min or exceeding the daily budget. Overruns will trigger validation rejection. Keep sum <= daily budget.

4. POST-EXAM SCHEDULING RULE:
   - NEVER schedule any study session for a subject AFTER its exam date.
   - For each date, ONLY schedule subjects from the 'Allowed subjects' list specified for that date in Section 3 above.
   - DATE-LEVEL RULE: Since exam times are not collected, study sessions on the exam date itself (e.g. morning quick revision or formula recall before the exam) ARE allowed.

5. EXACT SUBJECT MATCHING:
   - The "subject" field in every session MUST strictly match one of the student's declared subjects:
     {[s.name for s in plan_input.subjects]}

6. ALLOWED ACTIVITY TYPES:
   - The "activity" field MUST be one of these exact strings:
     [{allowed_activities_str}]

7. POSITIVE DURATIONS & ACTIONABLE TASKS:
   - Each session "duration_minutes" must be an integer > 0 (e.g., 45, 60, 90). Never use 0 minutes for a session.
   - For dates with available budget > 0, schedule 1 or 2 focused sessions to cover the daily budget cleanly.
   - For dates with budget == 0 (rest days), do NOT schedule any sessions at all; output an empty list: "sessions": [].
   - "task" must describe a concrete, actionable learning topic or sub-topic (e.g., "Solve Dynamic Programming knapsack problems", "Review Memory Paging and Virtual Memory diagrams").
   - Give prioritized focus and more time to designated weak subjects/topics prior to their exams.

=== OUTPUT FORMAT INSTRUCTIONS ===
You must respond with ONLY a valid JSON object. No intro, no conversational text, and no commentary.
Format:
{{
  "schedule": [
    {{
      "date": "YYYY-MM-DD",
      "sessions": [
        {{
          "subject": "<Exact subject name>",
          "activity": "<One of allowed activities>",
          "task": "<Specific actionable topic or task>",
          "duration_minutes": <positive integer>
        }}
      ]
    }},
    {{
      "date": "YYYY-MM-DD",
      "sessions": []
    }}
  ]
}}
"""
    return prompt.strip()


def build_study_plan_prompt(plan_input: StudyPlanInput, version: str = "v3") -> str:
    """Unified prompt generator dispatching to requested prompt version (default: v3)."""
    if version == "v1":
        return build_prompt_v1_baseline(plan_input)
    elif version == "v2":
        return build_prompt_v2_fewshot_schema(plan_input)
    else:
        return build_prompt_v3_optimized_guardrails(plan_input)
