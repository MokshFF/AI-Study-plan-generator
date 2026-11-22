# Milestone 2 Submission Content Draft

**Problem ID**: C20  
**Project Title**: AI-Powered Personalized Study Plan Generator Using Prompt Engineering  
**Course**: Prompt Engineering Mini-Project (B.Tech CSE - 5th Semester)  
**Team ID**: `[Team ID: Team-XX]`  
**Team Members**: `[Student 1 Name (E22CSEUXXXX), Student 2 Name (E22CSEUXXXX), Student 3 Name (E22CSEUXXXX)]`

---

## 1. Project Summary & Milestone 2 Objective
This project addresses **Problem C20** by developing a fully working, offline, AI-powered study planner tailored for university students balancing multiple overlapping exams. The application takes student exam dates, daily study budgets, rest day overrides, and weak subjects, and uses **Prompt Engineering with local Ollama LLMs** to generate a feasible, personalized study timetable.

All generations are audited by an **independent Python validator** before display, guaranteeing that no hallucinated subjects, post-exam sessions, or rest-day overruns ever reach the student.

---

## 2. Key Milestone 2 Deliverables & Achievements

### 2.1 Complete Local Ollama Migration (Zero Cloud APIs)
- Completely migrated from external APIs to **100% local, privacy-preserving Ollama inference**.
- Installed and benchmarked two local models:
  - **`qwen2.5:1.5b`** (Primary, 986 MB): Generates pure JSON on local CPU at ~18–21 tokens/sec, completing full 14-day timetables in **~75–77 seconds**.
  - **`qwen3:4b`** (Alternative, 2.5 GB): Reasoning model available via configurable sidebar dropdown.
- Configurable Ollama URL (`http://localhost:11434`) and model selection in the Streamlit sidebar.

### 2.2 Prompt Engineering Iteration (3 Distinct Versions Preserved)
We preserved and benchmarked three distinct prompt versions on identical student data:
1. **Version 1 (V1 Baseline Zero-Shot)**: Milestone 1 naive prompt. Fails schema validation (outputs `"dates"` and textual times instead of machine-parseable durations).
2. **Version 2 (V2 Few-Shot with Schema)**: Added schema definition. Solved root keys but produced **6 academic errors** (hallucinated sessions after exams, violated rest days, copied placeholder activity strings).
3. **Version 3 (V3 Final Grounded Guardrails)**: Introduced role prompting, strict negative guardrails, and **per-date candidate grounding** (pre-computing eligible subjects for each calendar day). Achieved **0 validation errors (100% Valid)**.
- **Prompt Versions Preserved**: 3
- **Final Runtime Prompt Count**: 1 (V3 template)

### 2.3 Rigorous Test Matrix (10 Distinct Cases)
Executed 10 distinct test cases across normal, edge, and invalid conditions (`experiments/run_test_matrix.py`):
- **TC-01 (Normal)**: 4 subjects, 14 days, distinct exam dates $\rightarrow$ **PASS** (100% valid, 0 errors).
- **TC-02 (Edge)**: Weak subject prioritization (DSA, OS) $\rightarrow$ **PASS** (priority topics scheduled).
- **TC-03 (Edge)**: Two exams on the same date (DBMS & OS on Dec 3) $\rightarrow$ **PASS** (valid scheduling).
- **TC-04 (Edge)**: Zero-study rest day (Dec 6 budget = 0) $\rightarrow$ **PASS** (`sessions: []` honored).
- **TC-05 (Edge)**: Very small daily time budget (30 min/day) $\rightarrow$ **PASS** (0 overruns).
- **TC-06 (Invalid Input)**: Exam date before planning period $\rightarrow$ **PASS** (rejected pre-LLM).
- **TC-07 (Invalid Input)**: Reversed dates (`start > end`) $\rightarrow$ **PASS** (rejected pre-LLM).
- **TC-08 (Invalid Output)**: Daily budget overrun in model response $\rightarrow$ **PASS** (caught by validator).
- **TC-09 (Invalid Output)**: Missing calendar date in schedule $\rightarrow$ **PASS** (caught by validator).
- **TC-10 (Invalid Output)**: Hallucinated unknown subject $\rightarrow$ **PASS** (caught by validator).
- **Test Pass Rate**: **10 / 10 PASSED (100%)**.

### 2.4 Experiment Logging
- Automated logging engine (`study_plan/experiment_logger.py`) writes completed evaluation runs to `experiments/experiment_log.json` and `experiments/experiment_log.md`.
- Records run ID, timestamp, model, prompt version, status, error count, total minutes, latency, and notes.

### 2.5 Streamlit Application Features
- **One-Click "Load sample"**: Fills the form with fictional DSA, DBMS, OS, and NLP data.
- **Local Ollama Trigger**: "Generate timetable" button with real-time spinner, latency timer, and exact model display.
- **Offline Fixture Mode**: "Check pasted response" tab allows instant validation testing without running local inference.
- **Grouped Timetable**: Shows date, available vs. used minutes, subject, activity badge, task, and duration.
- **CSV Download**: One-click download of validated timetable as `study_plan.csv`.
- **Live Experiment Log Viewer**: Dedicated expandable tab displaying all completed historical runs.

---

## 3. Evidence & File Artifacts

| Deliverable | File Path |
| :--- | :--- |
| **Streamlit Entry Point** | [`app.py`](file:///c:/Users/avars/Downloads/STUDY%20PLAN%20GENERATOR/app.py) |
| **Pure Python Validator** | [`study_plan/validator.py`](file:///c:/Users/avars/Downloads/STUDY%20PLAN%20GENERATOR/study_plan/validator.py) |
| **Prompt Engineering Templates** | [`study_plan/prompt_template.py`](file:///c:/Users/avars/Downloads/STUDY%20PLAN%20GENERATOR/study_plan/prompt_template.py) |
| **Local Ollama Client** | [`study_plan/ollama_client.py`](file:///c:/Users/avars/Downloads/STUDY%20PLAN%20GENERATOR/study_plan/ollama_client.py) |
| **Unit Test Suite (28 Tests)** | [`tests/test_study_plan.py`](file:///c:/Users/avars/Downloads/STUDY%20PLAN%20GENERATOR/tests/test_study_plan.py) |
| **10-Case Test Matrix Harness** | [`experiments/run_test_matrix.py`](file:///c:/Users/avars/Downloads/STUDY%20PLAN%20GENERATOR/experiments/run_test_matrix.py) |
| **Test Results Data** | [`experiments/test_matrix_results.json`](file:///c:/Users/avars/Downloads/STUDY%20PLAN%20GENERATOR/experiments/test_matrix_results.json) |
| **Experiment Logs** | [`experiments/experiment_log.md`](file:///c:/Users/avars/Downloads/STUDY%20PLAN%20GENERATOR/experiments/experiment_log.md) & [`.json`](file:///c:/Users/avars/Downloads/STUDY%20PLAN%20GENERATOR/experiments/experiment_log.json) |
| **Raw Prompt Outputs** | [`experiments/raw_outputs/`](file:///c:/Users/avars/Downloads/STUDY%20PLAN%20GENERATOR/experiments/raw_outputs) (`v1_response.json`, `v2_response.json`, `v3_response.json`) |
| **Comprehensive Technical Report** | [`docs/Milestone2_Technical_Report.md`](file:///c:/Users/avars/Downloads/STUDY%20PLAN%20GENERATOR/docs/Milestone2_Technical_Report.md) |
