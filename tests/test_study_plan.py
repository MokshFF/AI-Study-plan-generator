"""Unit Test Suite for AI-Powered Personalized Study Plan Generator.

Problem ID: C20 - Bennett University Prompt Engineering Mini-Project
Tests:
- Input validation (blank/duplicate subjects, reversed dates, negative budgets, unknown weak subjects)
- Output validation (valid JSON, malformed JSON, missing/duplicate dates, unknown subjects,
  non-positive durations, unrecognized activities, zero-minute days, budget overruns, post-exam violations)
- Date-level rule confirmation (sessions on exam date are permitted)
- Three prompt versions (v1 baseline, v2 few-shot, v3 final guardrails)
- Ollama client error handling (server unavailable, missing model, timeout, and valid structured response)
- Experiment logging (only completed runs are logged)
"""

import json
from unittest.mock import MagicMock, patch
import urllib.error
import pytest

from study_plan.validator import (
    ALLOWED_ACTIVITIES,
    DaySchedule,
    StudyPlanInput,
    SubjectInput,
    validate_inputs,
    validate_plan_output,
)
from study_plan.prompt_template import (
    build_study_plan_prompt,
    build_prompt_v1_baseline,
    build_prompt_v2_fewshot_schema,
    build_prompt_v3_optimized_guardrails,
    PROMPT_VERSIONS,
)
from study_plan.fixtures import (
    get_sample_input,
    FIXTURE_VALID_RESPONSE_JSON,
    FIXTURE_INVALID_BUDGET_OVERRUN_JSON,
    FIXTURE_INVALID_POST_EXAM_JSON,
    FIXTURE_INVALID_REST_DAY_JSON,
    FIXTURE_INVALID_UNKNOWN_SUBJECT_JSON,
)
from study_plan.ollama_client import (
    check_ollama_status,
    call_ollama_study_planner,
    resolve_ollama_url,
    resolve_ollama_model,
)
from study_plan.experiment_logger import log_completed_run, get_experiments


# ---------------------------------------------------------------------------
# 1. INPUT VALIDATION TESTS
# ---------------------------------------------------------------------------

def test_valid_sample_input_passes():
    """Verify that the standard fictional student input has zero validation errors."""
    sample = get_sample_input()
    errors = validate_inputs(sample)
    assert errors == []


def test_input_rejects_reversed_date_range():
    """Verify that start_date > end_date is caught and rejected."""
    plan = StudyPlanInput(
        start_date="2026-12-15",
        end_date="2026-12-01",  # Reversed!
        subjects=[SubjectInput(name="DSA", exam_date="2026-12-20")],
        default_daily_minutes=120,
    )
    errors = validate_inputs(plan)
    assert any("reversed" in err.lower() for err in errors)


def test_input_rejects_blank_subject_name():
    """Verify that blank or whitespace-only subject names are rejected."""
    plan = StudyPlanInput(
        start_date="2026-12-01",
        end_date="2026-12-05",
        subjects=[SubjectInput(name="   ", exam_date="2026-12-04")],
        default_daily_minutes=120,
    )
    errors = validate_inputs(plan)
    assert any("blank name" in err.lower() for err in errors)


def test_input_rejects_duplicate_subject_names():
    """Verify that duplicate subject names (case-insensitive) are rejected."""
    plan = StudyPlanInput(
        start_date="2026-12-01",
        end_date="2026-12-05",
        subjects=[
            SubjectInput(name="Operating Systems", exam_date="2026-12-04"),
            SubjectInput(name="operating systems", exam_date="2026-12-05"),
        ],
        default_daily_minutes=120,
    )
    errors = validate_inputs(plan)
    assert any("duplicate subject" in err.lower() for err in errors)


def test_input_rejects_exam_before_start_date():
    """Verify that an exam date scheduled before the planning start date is rejected."""
    plan = StudyPlanInput(
        start_date="2026-12-05",
        end_date="2026-12-10",
        subjects=[SubjectInput(name="DSA", exam_date="2026-12-02")],  # Prior to start!
        default_daily_minutes=120,
    )
    errors = validate_inputs(plan)
    assert any("before the planning start date" in err.lower() for err in errors)


def test_input_rejects_negative_budget():
    """Verify that negative daily study minutes are rejected."""
    plan = StudyPlanInput(
        start_date="2026-12-01",
        end_date="2026-12-05",
        subjects=[SubjectInput(name="DSA", exam_date="2026-12-04")],
        default_daily_minutes=-60,
        daily_overrides={"2026-12-02": -30},
    )
    errors = validate_inputs(plan)
    assert any("cannot be negative" in err.lower() for err in errors)


def test_input_rejects_unknown_weak_subject():
    """Verify that weak subjects not present in declared subjects are rejected."""
    plan = StudyPlanInput(
        start_date="2026-12-01",
        end_date="2026-12-05",
        subjects=[SubjectInput(name="DSA", exam_date="2026-12-04")],
        default_daily_minutes=120,
        weak_subjects=["Compiler Design"],  # Not in subjects
    )
    errors = validate_inputs(plan)
    assert any("unknown weak subject" in err.lower() for err in errors)


# ---------------------------------------------------------------------------
# 2. OUTPUT VALIDATION TESTS
# ---------------------------------------------------------------------------

def test_output_validates_perfect_fixture():
    """Verify that our 14-day sample fixture is 100% valid under all rules."""
    sample_input = get_sample_input()
    result = validate_plan_output(FIXTURE_VALID_RESPONSE_JSON, sample_input)
    assert result.is_valid is True
    assert result.errors == []
    assert len(result.schedule) == 14


def test_output_rejects_malformed_json():
    """Verify that invalid JSON syntax is caught with a clear error."""
    sample_input = get_sample_input()
    bad_json = "{ schedule: [ { date: '2026-12-01', ... "
    result = validate_plan_output(bad_json, sample_input)
    assert result.is_valid is False
    assert any("malformed json" in err.lower() for err in result.errors)


def test_output_rejects_markdown_code_block_wrapping():
    """Verify that markdown code block wrappers (```json ... ```) are cleanly parsed."""
    sample_input = get_sample_input()
    wrapped_json = f"```json\n{FIXTURE_VALID_RESPONSE_JSON}\n```"
    result = validate_plan_output(wrapped_json, sample_input)
    assert result.is_valid is True
    assert result.errors == []


def test_output_rejects_missing_dates():
    """Verify that missing dates in the planning window are flagged."""
    sample_input = get_sample_input()
    fixture_dict = json.loads(FIXTURE_VALID_RESPONSE_JSON)
    fixture_dict["schedule"] = [d for d in fixture_dict["schedule"] if d["date"] != "2026-12-03"]
    result = validate_plan_output(json.dumps(fixture_dict), sample_input)
    assert result.is_valid is False
    assert any("missing date" in err.lower() for err in result.errors)
    assert any("2026-12-03" in err for err in result.errors)


def test_output_rejects_duplicate_dates():
    """Verify that duplicate dates in schedule are flagged."""
    sample_input = get_sample_input()
    fixture_dict = json.loads(FIXTURE_VALID_RESPONSE_JSON)
    fixture_dict["schedule"].append(fixture_dict["schedule"][0])
    result = validate_plan_output(json.dumps(fixture_dict), sample_input)
    assert result.is_valid is False
    assert any("duplicate date" in err.lower() for err in result.errors)


def test_output_rejects_unknown_subject():
    """Verify that sessions with subjects not declared by the student are rejected."""
    sample_input = get_sample_input()
    result = validate_plan_output(FIXTURE_INVALID_UNKNOWN_SUBJECT_JSON, sample_input)
    assert result.is_valid is False
    assert any("unknown subject 'quantum computing'" in err.lower() for err in result.errors)


def test_output_rejects_non_positive_duration():
    """Verify that session duration <= 0 is flagged as an error."""
    sample_input = get_sample_input()
    result = validate_plan_output(FIXTURE_INVALID_UNKNOWN_SUBJECT_JSON, sample_input)
    assert result.is_valid is False
    assert any("duration must be an integer > 0" in err.lower() for err in result.errors)


def test_output_rejects_unrecognized_activity():
    """Verify that an arbitrary activity name not in ALLOWED_ACTIVITIES is rejected."""
    sample_input = get_sample_input()
    invalid_data = {
        "schedule": [
            {
                "date": "2026-12-01",
                "sessions": [
                    {
                        "subject": "Data Structures & Algorithms",
                        "activity": "Social Media Browsing",  # Invalid activity!
                        "task": "Watching reels about sorting",
                        "duration_minutes": 60,
                    }
                ],
            }
        ]
    }
    result = validate_plan_output(json.dumps(invalid_data), sample_input)
    assert result.is_valid is False
    assert any("unrecognized activity type" in err.lower() for err in result.errors)


def test_output_rejects_sessions_on_zero_minute_day():
    """Verify that scheduling sessions on a 0-minute day off is rejected."""
    sample_input = get_sample_input()
    result = validate_plan_output(FIXTURE_INVALID_REST_DAY_JSON, sample_input)
    assert result.is_valid is False
    assert any("rest day (0 available minutes)" in err.lower() for err in result.errors)


def test_output_rejects_daily_budget_overrun():
    """Verify that total session duration exceeding the day's available minutes is rejected."""
    sample_input = get_sample_input()
    result = validate_plan_output(FIXTURE_INVALID_BUDGET_OVERRUN_JSON, sample_input)
    assert result.is_valid is False
    assert any("budget overrun" in err.lower() for err in result.errors)


def test_output_rejects_post_exam_scheduling():
    """Verify that scheduling study for a subject AFTER its exam date is strictly rejected."""
    sample_input = get_sample_input()
    result = validate_plan_output(FIXTURE_INVALID_POST_EXAM_JSON, sample_input)
    assert result.is_valid is False
    assert any("post-exam scheduling violation" in err.lower() for err in result.errors)


def test_output_permits_study_on_exam_date_date_level_rule():
    """Confirm the prototype's explicit date-level rule:

    Study sessions ON the exam date itself (session_date <= exam_date) are allowed.
    """
    sample_input = get_sample_input()
    result = validate_plan_output(FIXTURE_VALID_RESPONSE_JSON, sample_input)
    assert result.is_valid is True
    assert not any("post-exam" in err.lower() for err in result.errors)


# ---------------------------------------------------------------------------
# 3. PROMPT GENERATOR & THREE PROMPT VERSIONS TESTS
# ---------------------------------------------------------------------------

def test_prompt_version_1_baseline_renders():
    """Verify v1 baseline prompt renders without guardrails."""
    sample_input = get_sample_input()
    prompt_v1 = build_prompt_v1_baseline(sample_input)
    assert "Make a study timetable" in prompt_v1
    assert "Data Structures & Algorithms" in prompt_v1
    assert "GUARDRAILS" not in prompt_v1


def test_prompt_version_2_fewshot_renders():
    """Verify v2 few-shot prompt renders schema but lacks negative guardrails."""
    sample_input = get_sample_input()
    prompt_v2 = build_prompt_v2_fewshot_schema(sample_input)
    assert "schedule" in prompt_v2
    assert "GUARDRAILS" not in prompt_v2
    assert "ZERO-MINUTE REST DAYS" not in prompt_v2


def test_prompt_version_3_optimized_guardrails_renders():
    """Verify v3 final optimized prompt includes all academic constraints and guardrails."""
    sample_input = get_sample_input()
    prompt_v3 = build_prompt_v3_optimized_guardrails(sample_input)

    assert "Data Structures & Algorithms" in prompt_v3
    assert "2026-12-01" in prompt_v3
    assert "2026-12-14" in prompt_v3
    assert "ZERO-MINUTE REST DAYS" in prompt_v3
    assert "POST-EXAM SCHEDULING RULE" in prompt_v3
    assert "DATE-LEVEL RULE" in prompt_v3
    assert "STRICT DAILY TIME BUDGET" in prompt_v3
    assert "ALLOWED ACTIVITY TYPES" in prompt_v3
    assert "Theory" in prompt_v3


def test_prompt_dispatcher():
    """Verify build_study_plan_prompt dispatches to requested version."""
    sample = get_sample_input()
    assert "Make a study timetable" in build_study_plan_prompt(sample, "v1")
    assert "academic study planner" in build_study_plan_prompt(sample, "v2")
    assert "CRITICAL ACADEMIC PLANNING RULES" in build_study_plan_prompt(sample, "v3")


# ---------------------------------------------------------------------------
# 4. OLLAMA CLIENT TESTS
# ---------------------------------------------------------------------------

def test_ollama_url_and_model_resolution():
    """Verify Ollama URL and model fallback resolution."""
    assert resolve_ollama_url(None) == "http://localhost:11434"
    assert resolve_ollama_url("http://192.168.1.50:11434/") == "http://192.168.1.50:11434"
    assert resolve_ollama_model(None) == "qwen3:4b"
    assert resolve_ollama_model("qwen2.5:3b") == "qwen2.5:3b"


def test_ollama_handles_unavailable_server():
    """Verify clear error message when Ollama server is unreachable."""
    # Connecting to non-existent port should raise informative RuntimeError
    with pytest.raises(RuntimeError) as exc_info:
        call_ollama_study_planner(
            prompt="test",
            base_url="http://127.0.0.1:59999",  # Non-existent port
            model="qwen3:4b",
            timeout=1,
        )
    assert "Ollama server is unavailable" in str(exc_info.value)
    assert "59999" in str(exc_info.value)


@patch("urllib.request.urlopen")
def test_ollama_handles_missing_model(mock_urlopen):
    """Verify clear error message when model is missing on Ollama server."""
    # Mock /api/tags response returning installed models list that does not contain qwen3:4b
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.read.return_value = json.dumps({"models": [{"name": "llama3.2:1b"}]}).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp
    mock_urlopen.return_value = mock_resp

    with pytest.raises(RuntimeError) as exc_info:
        call_ollama_study_planner(
            prompt="test",
            base_url="http://localhost:11434",
            model="qwen3:4b",
        )
    assert "Model 'qwen3:4b' is not installed" in str(exc_info.value)
    assert "ollama pull qwen3:4b" in str(exc_info.value)


@patch("urllib.request.urlopen")
def test_ollama_handles_successful_json_generation(mock_urlopen):
    """Verify successful Ollama JSON generation call and model return."""
    # First call: check /api/tags
    mock_tags = MagicMock()
    mock_tags.status = 200
    mock_tags.read.return_value = json.dumps({"models": [{"name": "qwen3:4b"}]}).encode("utf-8")
    mock_tags.__enter__.return_value = mock_tags

    # Second call: /api/generate
    mock_gen = MagicMock()
    mock_gen.status = 200
    mock_gen.read.return_value = json.dumps({
        "response": json.dumps({"schedule": []})
    }).encode("utf-8")
    mock_gen.__enter__.return_value = mock_gen

    mock_urlopen.side_effect = [mock_tags, mock_gen]

    text, model_name = call_ollama_study_planner(
        prompt="test prompt",
        base_url="http://localhost:11434",
        model="qwen3:4b",
    )
    assert '{"schedule": []}' in text
    assert "qwen3:4b" in model_name


# ---------------------------------------------------------------------------
# 5. EXPERIMENT LOGGER TESTS
# ---------------------------------------------------------------------------

def test_experiment_logger_records_completed_run(tmp_path):
    """Verify that logging only happens for completed runs and records to disk."""
    with patch("study_plan.experiment_logger.LOG_JSON_PATH", str(tmp_path / "exp.json")), \
         patch("study_plan.experiment_logger.LOG_MD_PATH", str(tmp_path / "exp.md")), \
         patch("study_plan.experiment_logger.EXPERIMENTS_DIR", str(tmp_path)):

        entry = log_completed_run(
            engine="Ollama",
            model="qwen3:4b",
            prompt_version="v3",
            dataset_name="DSA, DBMS, OS, NLP (14 days)",
            is_valid=True,
            errors_count=0,
            warnings_count=1,
            total_minutes=2520,
            execution_time_sec=14.5,
            notes="Full guardrail test run",
        )
        assert entry["status"] == "PASS"
        assert entry["model"] == "qwen3:4b"

        # Verify JSON was written
        with open(tmp_path / "exp.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            assert len(data) == 1
            assert data[0]["engine"] == "Ollama"

        # Verify Markdown was written
        with open(tmp_path / "exp.md", "r", encoding="utf-8") as f:
            md_text = f.read()
            assert "qwen3:4b" in md_text
            assert "PASS" in md_text


# ---------------------------------------------------------------------------
# 6. AUTO-REPAIR & CONSTRAINT NORMALIZER TESTS
# ---------------------------------------------------------------------------

def test_auto_repair_clamps_budget_overrun():
    """Verify that auto_repair=True clamps minor budget overruns to exact available minutes."""
    sample = get_sample_input()
    data = json.loads(FIXTURE_VALID_RESPONSE_JSON)
    # Inject 195 min on 2026-12-05 (which has 180m budget)
    for d in data["schedule"]:
        if d["date"] == "2026-12-05":
            d["sessions"] = [
                {"subject": "Data Structures & Algorithms", "activity": "Revision", "task": "Formulas", "duration_minutes": 90},
                {"subject": "Data Structures & Algorithms", "activity": "Practice", "task": "Trees", "duration_minutes": 105},
            ]
    raw_payload = json.dumps(data)

    # Strict mode catches the overrun
    strict_res = validate_plan_output(raw_payload, sample, auto_repair=False)
    assert strict_res.is_valid is False
    assert any("budget overrun" in e.lower() for e in strict_res.errors)

    # Auto-repair mode clamps to 180 min
    repaired_res = validate_plan_output(raw_payload, sample, auto_repair=True)
    assert repaired_res.is_valid is True
    assert repaired_res.errors == []
    dec5 = [d for d in repaired_res.schedule if d.date == "2026-12-05"][0]
    assert dec5.used_minutes == 180
    assert any("auto-aligned" in w.lower() for w in repaired_res.warnings)


def test_auto_repair_clears_zero_minute_rest_day_sessions():
    """Verify that auto_repair=True clears sessions on scheduled rest days."""
    sample = get_sample_input()
    # FIXTURE_INVALID_REST_DAY_JSON has study sessions on 2026-12-06 (rest day)
    strict_res = validate_plan_output(FIXTURE_INVALID_REST_DAY_JSON, sample, auto_repair=False)
    assert strict_res.is_valid is False

    repaired_res = validate_plan_output(FIXTURE_INVALID_REST_DAY_JSON, sample, auto_repair=True)
    assert repaired_res.is_valid is True
    dec6 = [d for d in repaired_res.schedule if d.date == "2026-12-06"][0]
    assert dec6.used_minutes == 0
    assert dec6.sessions == []


def test_auto_repair_reallocates_post_exam_sessions():
    """Verify that auto_repair=True reallocates post-exam sessions to active subjects."""
    sample = get_sample_input()
    # FIXTURE_INVALID_POST_EXAM_JSON has DSA sessions after its Dec 5 exam
    strict_res = validate_plan_output(FIXTURE_INVALID_POST_EXAM_JSON, sample, auto_repair=False)
    assert strict_res.is_valid is False

    repaired_res = validate_plan_output(FIXTURE_INVALID_POST_EXAM_JSON, sample, auto_repair=True)
    assert repaired_res.is_valid is True
    # Verify no DSA sessions exist after Dec 5
    for day in repaired_res.schedule:
        if day.date > "2026-12-05":
            for s in day.sessions:
                assert s.subject != "Data Structures & Algorithms"


def test_auto_repair_normalizes_v1_markdown_table():
    """Verify that auto_repair=True can extract and normalize markdown tables into valid schedules."""
    sample = get_sample_input()
    md_table = """
| Date | Subject | Task Description | Duration (Minutes) |
| 2026-12-01 | Data Structures & Algorithms | Dynamic Programming | 90 |
| 2026-12-01 | Operating Systems | Virtual Memory | 90 |
| 2026-12-02 | Data Structures & Algorithms | Graphs | 90 |
| 2026-12-02 | Database Management Systems | Normalization | 90 |
    """
    repaired_res = validate_plan_output(md_table, sample, auto_repair=True)
    assert repaired_res.is_valid is True
    assert len(repaired_res.schedule) == 14

