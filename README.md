# 🎓 AI-Powered Personalized Study Plan Generator Using Prompt Engineering

**Problem ID**: C20  
**Academic Context**: Bennett University - Prompt Engineering Mini-Project (5th Sem B.Tech CSE)  
**Target Users**: University students preparing for multiple concurrent semester examinations.  
**Engine**: 100% Local Ollama (`qwen2.5:1.5b` default recommended / `qwen3:4b` configurable)  
**Cloud API Status**: Zero external API dependencies (fully offline, private, zero cost)

---

## 📌 1. Project Overview

Preparing for university examinations across multiple technical subjects (e.g., Data Structures & Algorithms, Database Management Systems, Operating Systems, Natural Language Processing) is a high-stakes scheduling problem. Students must balance time budgets, rest days, and subject-specific exam dates without overrunning daily limits or scheduling revision after exams have already taken place.

This project delivers:
1. **100% Local Inference via Ollama**: Runs completely offline and locally using open-source models (`qwen2.5:1.5b` for fast ~75s generation or `qwen3:4b`).
2. **Three Preserved Prompt Engineering Iterations**: Preserves and evaluates Prompt v1 (baseline zero-shot from Milestone 1), Prompt v2 (few-shot with schema), and Prompt v3 (grounded production guardrail template).
3. **Independent Pure-Python Validation Engine**: A zero-LLM dependency safety layer enforcing 9 academic rules: chronological completeness, daily budget bounds, zero-minute rest days, subject whitelisting, activity whitelisting, and post-exam prohibition.
4. **10 Distinct Test Cases Matrix**: Evaluated against normal, edge, and invalid cases with 10/10 PASS rate.
5. **Experiment Logging**: Automatically tracks only completed runs into `experiments/experiment_log.json` and `experiments/experiment_log.md`.
6. **Manual Fallback & Offline Fixtures**: Full prompt-copying and response-pasting fallback to test validation without active servers.

---

## 🏗️ 2. Architecture & File Structure

```
STUDY PLAN GENERATOR/
│
├── app.py                     # Streamlit frontend & interactive UI
├── requirements.txt           # Python dependencies (streamlit, pytest, etc.)
├── .env.example               # Environment variables template
├── .gitignore                 # Excludes local caches and credentials
├── README.md                  # Comprehensive documentation and viva guide
│
├── study_plan/                # Core Python package (Pure standard-library logic)
│   ├── __init__.py            # Package initializer
│   ├── validator.py           # Pure-Python input & output validation engine (9 rules)
│   ├── prompt_template.py     # Three prompt versions (v1, v2, v3 grounded)
│   ├── ollama_client.py       # Local Ollama client with error handling & JSON formatting
│   ├── experiment_logger.py   # Records completed runs to JSON & Markdown
│   └── fixtures.py            # Fictional student dataset (DSA, DBMS, OS, NLP) & labeled test fixtures
│
├── experiments/               # Experiment logs & raw model outputs
│   ├── experiment_log.json    # Machine-readable experiment history
│   ├── experiment_log.md      # Formatted Markdown benchmark table
│   ├── run_test_matrix.py     # 10-case test matrix execution harness
│   ├── test_matrix_results.json # 10/10 test results dataset
│   └── raw_outputs/           # Preserved raw outputs for V1, V2, and V3
│       ├── v1_response.json   # Milestone 1 baseline raw response
│       ├── v2_response.json   # Few-shot raw response
│       ├── v3_prompt.txt      # Grounded V3 prompt text
│       └── v3_response.json   # Grounded V3 100% valid response
│
├── tests/
│   └── test_study_plan.py     # 28 comprehensive unit tests (pytest)
│
├── docs/                      # Milestone 2 submission documentation
│   ├── Milestone2_Technical_Report.md  # 9-chapter academic technical report
│   ├── Milestone2_Content_Draft.md     # Milestone 2 submission summary
│   └── Video_Reel_Script.md            # 90-150 second timed video presentation script
│
└── .streamlit/
    └── secrets.toml.example   # Streamlit secrets configuration template
```

---

## 🖥️ 3. Quickstart & Installation (Windows)

### Step 1: Install Python Dependencies
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Step 2: Install and Start Ollama on Windows
1. Download the Windows installer from [https://ollama.com/download/windows](https://ollama.com/download/windows).
2. Start the Ollama server:
   ```powershell
   ollama serve
   ```
3. Pull the recommended fast CPU model (under 1 GB):
   ```powershell
   ollama pull qwen2.5:1.5b
   ```
   *(Optional)* For machines with dedicated GPUs, you can also pull `qwen3:4b`:
   ```powershell
   ollama pull qwen3:4b
   ```

### Step 3: Run the Streamlit Application
```powershell
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

---

## 🧪 4. Testing & Verification Commands

### Run Unit Test Suite (28 Tests)
```powershell
python -m pytest tests/test_study_plan.py -v
```
*Expected: 28 passed in ~2.3 seconds.*

### Run the 10 Distinct Test Cases Matrix
```powershell
python experiments/run_test_matrix.py
```
*Expected: 10 / 10 cases PASSED across normal, edge, and invalid conditions.*

---

## 🔬 5. Prompt Engineering Comparison (v1 vs v2 vs v3)

All three versions evaluated on identical hardware using `qwen2.5:1.5b`:

| Metric | Version 1 (V1 Baseline) | Version 2 (V2 Few-Shot) | Version 3 (V3 Grounded Production) |
| :--- | :---: | :---: | :---: |
| **Strategy** | Naive Zero-Shot (Milestone 1) | Few-Shot Schema | Context Grounding + Negative Guardrails |
| **Requested Format** | Markdown Table | JSON Schema | Guardrailed JSON Schema |
| **Format Compliance** | ✅ Complied with Markdown table format | ✅ Complied with JSON syntax | ✅ Complied with JSON syntax |
| **Automated JSON Pipeline Compatibility** | ❌ **FAIL** (Compatibility Finding: Unstructured table cannot be parsed) | ❌ **FAIL** (Parsed, but failed 6 academic planning rules) | ✅ **PASS (0 Errors, 100% Valid)** in 77.6s |
| **Manual Transcription & Scheduling Constraints** | - Overgeneralized rest day to all 14 days (0 min scheduled).<br>- Scheduled DSA after exam on Dec 6 & 7; DBMS on Dec 9–13.<br>- Omitted Operating Systems. | - Violated Dec 6 rest day (allocated 120 min).<br>- Scheduled OS on Dec 12 & 13 (exam Dec 11).<br>- Copied placeholder text `"Theory/Revision"`. | - Dec 6 rest day strictly honored (`sessions: []`).<br>- 0 post-exam violations across all subjects.<br>- 100% allowed activity enum matched. |
| **Inference Time** | 21.4s | 76.9s | 77.6s |
| **Feasibility & Usefulness** | Unusable | Poor | **High (Directly actionable timetable)** |

- **Prompt Versions Preserved**: 3 (`v1_baseline`, `v2_fewshot_schema`, `v3_optimized_guardrails`)
- **Final Runtime Prompt Count**: 1 (Only V3 is constructed and sent during live generation)

---

## 🌐 6. Evaluator Access & Public Hosting Strategy

### Does the current application depend on your local laptop?
**Yes.** In this local prototype configuration, Ollama runs on your local CPU (`http://localhost:11434`), and Streamlit binds to port 8501 on your machine.

> **Continuous Execution Requirement**:
> For an evaluator on another device (phone, remote PC) to access the app via a public tunnel URL:
> 1. The **student laptop** must remain powered on, awake (no sleep mode), and connected to the internet.
> 2. The **Ollama daemon** must remain running on port 11434 (`ollama serve`).
> 3. The **Streamlit app** must remain running on port 8501 (`streamlit run app.py`).
> 4. The **Tunnel process** (e.g., ngrok / localtunnel) must remain active in a terminal window.
> If the laptop lid is closed or any of these four components stop, external requests immediately fail with 502 Bad Gateway.

### Access Interstitial Warning
When opening a tunnel link (`ngrok-free.app` or `loca.lt`) on an external device, evaluators will see a **provider security interstitial** (e.g. clicking "Visit Site" on ngrok, or submitting the tunnel IP on localtunnel). Once bypassed, the full Streamlit UI loads seamlessly.

### Alternative Zero-Laptop Hosting Option:
Deploying to **Streamlit Community Cloud** with the built-in **"Check pasted response"** tab allows evaluators to test complete, independent validation of test fixtures and study plans without requiring the student's laptop to stay online.

---

## 📋 7. Milestone 2 Audit Checklist

- [x] **Full Workflow Verified**: Form input $\rightarrow$ Prompt construction $\rightarrow$ Ollama `qwen2.5:1.5b` generation $\rightarrow$ Pure-Python validation $\rightarrow$ Grouped timetable display $\rightarrow$ CSV download.
- [x] **Exact Model Documented**: `qwen2.5:1.5b` (986 MB GGUF, default) and `qwen3:4b` (2.5 GB, alternative).
- [x] **10 Distinct Test Cases**: Recorded and executed in `experiments/test_matrix_results.json` (10/10 PASS). TC-01, TC-02, and TC-04 explicitly documented as distinct constraint evaluations from a shared 14-day live run.
- [x] **3 Prompt Versions Preserved**: V1 (Milestone 1 baseline table), V2 (few-shot), and V3 (grounded guardrails) in `study_plan/prompt_template.py`.
- [x] **Prompt Counts Separated**: Prompt version count = 3; Final runtime prompt count = 1.
- [x] **Date-Level Rule Scoped**: Explicitly noted that sessions on exam dates are allowed, but start times are not collected so validation does not verify time-of-day before exam sitting.
- [x] **Unit Test Suite**: 28 automated tests passing in `tests/test_study_plan.py`.
- [x] **Experiment Logging**: Active in `experiments/experiment_log.json` and `.md` (3 verified runs logged).
- [x] **PDF & Documentation Deliverables Delivered**:
  - Main Milestone 2 Report PDF (7 Official Sections): [`docs/Milestone2_Main_Report.pdf`](file:///c:/Users/avars/Downloads/STUDY%20PLAN%20GENERATOR/docs/Milestone2_Main_Report.pdf) & [`.md`](file:///c:/Users/avars/Downloads/STUDY%20PLAN%20GENERATOR/docs/Milestone2_Main_Report.md)
  - Supporting Technical Report PDF (9 Chapters): [`docs/Milestone2_Technical_Report.pdf`](file:///c:/Users/avars/Downloads/STUDY%20PLAN%20GENERATOR/docs/Milestone2_Technical_Report.pdf) & [`.md`](file:///c:/Users/avars/Downloads/STUDY%20PLAN%20GENERATOR/docs/Milestone2_Technical_Report.md)
  - Content Draft: [`docs/Milestone2_Content_Draft.md`](file:///c:/Users/avars/Downloads/STUDY%20PLAN%20GENERATOR/docs/Milestone2_Content_Draft.md)
  - Video Reel Script (90–150s): [`docs/Video_Reel_Script.md`](file:///c:/Users/avars/Downloads/STUDY%20PLAN%20GENERATOR/docs/Video_Reel_Script.md)
- [x] **Zero Gemini / Cloud Dependencies**: 100% verified zero references to cloud Gemini SDKs.
