"""PrepFlow — AI-Powered Personalized Study Plan Generator.

Problem ID: C20 | Bennett University Prompt Engineering Mini-Project
Architecture:
- Clean, professional Streamlit presentation layer (app.py)
- Local Ollama Client (study_plan/ollama_client.py)
- Pure Python Validation Engine (study_plan/validator.py)
- Prompt Engineering Templates v1/v2/v3 (study_plan/prompt_template.py)
- Experiment Logger (study_plan/experiment_logger.py)
- Test Fixtures & Fictional Dataset (study_plan/fixtures.py)
"""

from __future__ import annotations

import csv
import io
import time
import uuid
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Set

import streamlit as st

from study_plan.experiment_logger import get_experiments, log_completed_run
from study_plan.fixtures import (
    FIXTURE_INVALID_BUDGET_OVERRUN_JSON,
    FIXTURE_INVALID_POST_EXAM_JSON,
    FIXTURE_INVALID_REST_DAY_JSON,
    FIXTURE_INVALID_UNKNOWN_SUBJECT_JSON,
    FIXTURE_VALID_RESPONSE_JSON,
    get_sample_input,
)
from study_plan.ollama_client import (
    COMMON_OLLAMA_MODELS,
    DEFAULT_OLLAMA_MODEL,
    DEFAULT_OLLAMA_URL,
    call_ollama_study_planner,
    check_ollama_status,
)
from study_plan.prompt_template import (
    PROMPT_VERSIONS,
    build_study_plan_prompt,
)
from study_plan.validator import (
    ALLOWED_ACTIVITIES,
    DaySchedule,
    StudyPlanInput,
    SubjectInput,
    ValidationResult,
    validate_inputs,
    validate_plan_output,
)

# ---------------------------------------------------------------------------
# Page Configuration & Styling
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="PrepFlow | Personalized Exam Preparation",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    /* Global Typography & Palette */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Ambient Study-Themed Dynamic Mesh Background */
    .stApp {
        background:
            radial-gradient(circle at 12% 14%, rgba(99, 102, 241, 0.28) 0%, transparent 45%),
            radial-gradient(circle at 88% 12%, rgba(236, 72, 153, 0.24) 0%, transparent 42%),
            radial-gradient(circle at 50% 38%, rgba(6, 182, 212, 0.20) 0%, transparent 50%),
            radial-gradient(circle at 18% 85%, rgba(139, 92, 246, 0.26) 0%, transparent 48%),
            radial-gradient(circle at 82% 82%, rgba(245, 158, 11, 0.20) 0%, transparent 44%),
            #080C16 !important;
        background-attachment: fixed !important;
        background-size: cover !important;
    }

    /* Floating Study Icons Keyframe Animations */
    @keyframes float1 {
        0%, 100% { transform: translateY(0px) rotate(0deg); }
        50% { transform: translateY(-20px) rotate(6deg); }
    }
    @keyframes float2 {
        0%, 100% { transform: translateY(0px) rotate(0deg); }
        50% { transform: translateY(-25px) rotate(-8deg); }
    }
    @keyframes float3 {
        0%, 100% { transform: translateY(0px) scale(1); }
        50% { transform: translateY(-16px) scale(1.08); }
    }
    .study-floating-bg {
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        pointer-events: none;
        z-index: 0;
        overflow: hidden;
    }
    .float-item {
        position: absolute;
        font-size: 2.1rem;
        opacity: 0.12;
        filter: drop-shadow(0 0 16px rgba(129, 140, 248, 0.45));
        user-select: none;
    }
    .f1 { top: 8%; left: 5%; animation: float1 8s ease-in-out infinite; }
    .f2 { top: 14%; right: 7%; animation: float2 9.5s ease-in-out infinite; }
    .f3 { top: 44%; left: 2.5%; animation: float3 8.5s ease-in-out infinite; }
    .f4 { top: 72%; left: 7%; animation: float1 10s ease-in-out infinite; }
    .f5 { top: 52%; right: 4%; animation: float2 7.5s ease-in-out infinite; }
    .f6 { top: 84%; right: 10%; animation: float3 9.5s ease-in-out infinite; }
    .f7 { top: 26%; left: 22%; animation: float1 9s ease-in-out infinite; font-size: 1.7rem; opacity: 0.08; }
    .f8 { top: 75%; left: 45%; animation: float2 11s ease-in-out infinite; font-size: 1.7rem; opacity: 0.08; }

    /* Compact Header Bar */
    .header-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: #0F172A;
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 12px;
        padding: 16px 24px;
        margin-bottom: 20px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.35);
    }
    .header-title-box {
        display: flex;
        flex-direction: column;
    }
    .header-title {
        font-size: 1.6rem;
        font-weight: 800;
        color: #FFFFFF;
        letter-spacing: -0.02em;
        margin: 0;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .header-subtitle {
        color: #94A3B8;
        font-size: 0.88rem;
        margin: 2px 0 0 0;
        font-weight: 500;
    }
    .header-actions {
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .status-pill {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 6px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .status-online {
        background: rgba(16, 185, 129, 0.15);
        color: #34D399;
        border: 1px solid rgba(16, 185, 129, 0.35);
    }
    .status-offline {
        background: rgba(239, 68, 68, 0.15);
        color: #F87171;
        border: 1px solid rgba(239, 68, 68, 0.35);
    }
    .status-dot {
        height: 8px;
        width: 8px;
        border-radius: 50%;
        display: inline-block;
    }
    .dot-green { background: #10B981; }
    .dot-red { background: #EF4444; }

    /* Solid Panel Surfaces */
    .panel-box {
        background: #0F172A;
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 12px;
        padding: 20px 22px;
        margin-bottom: 18px;
        box-shadow: 0 4px 18px rgba(0, 0, 0, 0.3);
    }
    .panel-heading {
        font-size: 1.05rem;
        font-weight: 700;
        color: #F8FAFC;
        margin-top: 0;
        margin-bottom: 14px;
        display: flex;
        align-items: center;
        gap: 8px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        padding-bottom: 8px;
    }

    /* Live Summary Card */
    .summary-box {
        background: #0F172A;
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 12px;
        padding: 20px 22px;
        box-shadow: 0 4px 18px rgba(0, 0, 0, 0.3);
    }
    .summary-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 9px 0;
        border-bottom: 1px solid rgba(255, 255, 255, 0.06);
    }
    .summary-item:last-child {
        border-bottom: none;
    }
    .summary-label {
        color: #94A3B8;
        font-size: 0.84rem;
        font-weight: 500;
    }
    .summary-val {
        color: #F8FAFC;
        font-size: 0.92rem;
        font-weight: 700;
        text-align: right;
    }

    /* Primary Generate Button */
    div.stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 50%, #EC4899 100%) !important;
        border: none !important;
        color: #FFFFFF !important;
        font-weight: 700 !important;
        font-size: 1.02rem !important;
        padding: 12px 24px !important;
        border-radius: 10px !important;
        box-shadow: 0 4px 18px rgba(99, 102, 241, 0.4) !important;
        transition: all 0.2s ease !important;
    }
    div.stButton > button[kind="primary"]:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 6px 24px rgba(236, 72, 153, 0.55) !important;
    }

    /* Stale Plan Warning */
    .stale-plan-banner {
        background: rgba(245, 158, 11, 0.12);
        border: 1px solid rgba(245, 158, 11, 0.4);
        border-radius: 8px;
        padding: 10px 16px;
        color: #FCD34D;
        font-size: 0.88rem;
        font-weight: 600;
        margin-bottom: 16px;
        display: flex;
        align-items: center;
        gap: 10px;
    }

    /* Timetable Cards */
    .timetable-container {
        background: #0F172A;
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 12px;
        padding: 22px 24px;
        margin-top: 24px;
        box-shadow: 0 4px 22px rgba(0, 0, 0, 0.35);
    }
    .day-agenda-card {
        background: #1E293B;
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 10px;
        padding: 16px 20px;
        margin-bottom: 14px;
    }
    .day-agenda-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
        padding-bottom: 8px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.07);
    }
    .session-agenda-row {
        background: #0F172A;
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 8px;
        padding: 11px 16px;
        margin-bottom: 8px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    /* Activity Badges */
    .act-badge {
        font-size: 0.72rem;
        font-weight: 700;
        padding: 3px 8px;
        border-radius: 4px;
        text-transform: uppercase;
        letter-spacing: 0.03em;
    }
    .act-study { background: rgba(59, 130, 246, 0.18); color: #60A5FA; border: 1px solid rgba(59, 130, 246, 0.35); }
    .act-revision { background: rgba(16, 185, 129, 0.18); color: #34D399; border: 1px solid rgba(16, 185, 129, 0.35); }
    .act-practice { background: rgba(236, 72, 153, 0.18); color: #F472B6; border: 1px solid rgba(236, 72, 153, 0.35); }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Subject Color & Icon Styling
# ---------------------------------------------------------------------------
SUBJECT_PALETTE = {
    "Data Structures & Algorithms": {"border": "#6366F1", "text": "#818CF8", "bg": "rgba(99, 102, 241, 0.18)", "icon": "💻"},
    "Database Management Systems": {"border": "#10B981", "text": "#34D399", "bg": "rgba(16, 185, 129, 0.18)", "icon": "🗄️"},
    "Operating Systems": {"border": "#F59E0B", "text": "#FBBF24", "bg": "rgba(245, 158, 11, 0.18)", "icon": "⚙️"},
    "Natural Language Processing": {"border": "#06B6D4", "text": "#38BDF8", "bg": "rgba(6, 182, 212, 0.18)", "icon": "🧠"},
}
FALLBACK_PALETTES = [
    {"border": "#EC4899", "text": "#F472B6", "bg": "rgba(236, 72, 153, 0.18)", "icon": "📖"},
    {"border": "#8B5CF6", "text": "#A78BFA", "bg": "rgba(139, 92, 246, 0.18)", "icon": "📝"},
    {"border": "#14B8A6", "text": "#2DD4BF", "bg": "rgba(20, 184, 166, 0.18)", "icon": "🔬"},
]


def get_subject_style(subject_name: str) -> dict:
    if subject_name in SUBJECT_PALETTE:
        return SUBJECT_PALETTE[subject_name]
    idx = abs(hash(subject_name)) % len(FALLBACK_PALETTES)
    return FALLBACK_PALETTES[idx]


def map_activity_category(activity_name: str) -> str:
    """Maps recognized activity types into standard Study, Revision, or Practice."""
    act_lower = activity_name.lower()
    if "revision" in act_lower:
        return "Revision"
    if "practice" in act_lower or "problem" in act_lower or "mock" in act_lower:
        return "Practice"
    return "Study"


# ---------------------------------------------------------------------------
# Session State Initialization
# ---------------------------------------------------------------------------
if "start_date" not in st.session_state:
    st.session_state.start_date = date(2026, 12, 1)
if "end_date" not in st.session_state:
    st.session_state.end_date = date(2026, 12, 14)
if "default_minutes" not in st.session_state:
    st.session_state.default_minutes = 180

if "subjects_data" not in st.session_state:
    # 4 distinct university subjects with persistent unique identifiers
    st.session_state.subjects_data = [
        {
            "id": "sub_dsa",
            "name": "Data Structures & Algorithms",
            "exam_date": date(2026, 12, 5),
            "attention": True,
            "topics": "Dynamic Programming, Graph Traversals, AVL Trees",
        },
        {
            "id": "sub_dbms",
            "name": "Database Management Systems",
            "exam_date": date(2026, 12, 8),
            "attention": False,
            "topics": "Normalization, SQL, B-Trees & Indexing",
        },
        {
            "id": "sub_os",
            "name": "Operating Systems",
            "exam_date": date(2026, 12, 11),
            "attention": True,
            "topics": "Virtual Memory, Page Replacement, Deadlocks",
        },
        {
            "id": "sub_nlp",
            "name": "Natural Language Processing",
            "exam_date": date(2026, 12, 14),
            "attention": False,
            "topics": "Transformers, Word Embeddings, Attention Mechanism",
        },
    ]

if "rest_days" not in st.session_state:
    st.session_state.rest_days = ["2026-12-06"]
if "overrides" not in st.session_state:
    st.session_state.overrides = {
        "2026-12-04": 240,
        "2026-12-06": 0,
        "2026-12-07": 240,
        "2026-12-10": 210,
    }
if "preferences" not in st.session_state:
    st.session_state.preferences = "45-minute focus blocks, past paper problem-solving for weak areas"

if "ollama_model" not in st.session_state:
    st.session_state.ollama_model = "qwen2.5:1.5b"
if "ollama_url" not in st.session_state:
    st.session_state.ollama_url = DEFAULT_OLLAMA_URL
if "ollama_timeout" not in st.session_state:
    st.session_state.ollama_timeout = 300
if "prompt_version" not in st.session_state:
    st.session_state.prompt_version = "v3"

if "active_plan_result" not in st.session_state:
    st.session_state.active_plan_result = None
if "last_plan_input_snapshot" not in st.session_state:
    st.session_state.last_plan_input_snapshot = None
if "last_method_label" not in st.session_state:
    st.session_state.last_method_label = None
if "last_execution_sec" not in st.session_state:
    st.session_state.last_execution_sec = 0.0
if "last_raw_response" not in st.session_state:
    st.session_state.last_raw_response = None
if "last_prompt_rendered" not in st.session_state:
    st.session_state.last_prompt_rendered = None
if "is_generating" not in st.session_state:
    st.session_state.is_generating = False
if "app_view_mode" not in st.session_state:
    st.session_state.app_view_mode = "Planner Workspace"


def apply_sample_data():
    """Populates form with the benchmark fictional university dataset."""
    sample = get_sample_input()
    st.session_state.start_date = datetime.strptime(sample.start_date, "%Y-%m-%d").date()
    st.session_state.end_date = datetime.strptime(sample.end_date, "%Y-%m-%d").date()
    st.session_state.default_minutes = sample.default_daily_minutes
    st.session_state.subjects_data = [
        {
            "id": "sub_dsa",
            "name": "Data Structures & Algorithms",
            "exam_date": date(2026, 12, 5),
            "attention": True,
            "topics": "Dynamic Programming, Graph Traversals, AVL Trees",
        },
        {
            "id": "sub_dbms",
            "name": "Database Management Systems",
            "exam_date": date(2026, 12, 8),
            "attention": False,
            "topics": "Normalization, SQL, B-Trees & Indexing",
        },
        {
            "id": "sub_os",
            "name": "Operating Systems",
            "exam_date": date(2026, 12, 11),
            "attention": True,
            "topics": "Virtual Memory, Page Replacement, Deadlocks",
        },
        {
            "id": "sub_nlp",
            "name": "Natural Language Processing",
            "exam_date": date(2026, 12, 14),
            "attention": False,
            "topics": "Transformers, Word Embeddings, Attention Mechanism",
        },
    ]
    st.session_state.rest_days = ["2026-12-06"]
    st.session_state.overrides = dict(sample.daily_overrides)
    st.session_state.preferences = sample.preferences
    st.toast("Example data loaded: 4 university courses across 14 days.", icon="✨")


# ---------------------------------------------------------------------------
# Background Floating Study Particles
# ---------------------------------------------------------------------------
st.markdown(
    """
    <div class="study-floating-bg">
        <span class="float-item f1">📚</span>
        <span class="float-item f2">🎓</span>
        <span class="float-item f3">💡</span>
        <span class="float-item f4">⏱️</span>
        <span class="float-item f5">☕</span>
        <span class="float-item f6">🔬</span>
        <span class="float-item f7">💻</span>
        <span class="float-item f8">🎯</span>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Top Header Bar (Compact & Factual)
# ---------------------------------------------------------------------------
server_status = check_ollama_status(st.session_state.ollama_url)
is_ollama_online = server_status["available"]

head_col1, head_col2 = st.columns([3, 2])
with head_col1:
    st.markdown(
        """
        <div style="display:flex;align-items:center;gap:12px;margin-bottom:6px;">
            <span style="font-size:1.85rem;font-weight:800;color:#FFFFFF;letter-spacing:-0.02em;">📚 PrepFlow</span>
            <span style="font-size:0.92rem;color:#94A3B8;font-weight:500;padding-top:4px;">Personalized exam preparation</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
with head_col2:
    btn_col_a, btn_col_b, btn_col_c = st.columns([1.8, 1.2, 1.2])
    with btn_col_a:
        if is_ollama_online:
            st.markdown(
                f"<div style='margin-top:4px;'><span class='status-pill status-online'><span class='status-dot dot-green'></span> Connected ({st.session_state.ollama_model})</span></div>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                "<div style='margin-top:4px;'><span class='status-pill status-offline'><span class='status-dot dot-red'></span> Unavailable (Offline)</span></div>",
                unsafe_allow_html=True,
            )
    with btn_col_b:
        if st.button("✨ Load example", type="secondary", use_container_width=True, help="Load fictional benchmark dataset"):
            apply_sample_data()
            st.rerun()
    with btn_col_c:
        # Toggle primary navigation view
        curr_view = st.session_state.app_view_mode
        next_view = "Validation Lab" if curr_view == "Planner Workspace" else "Planner Workspace"
        btn_label = "🧪 Lab View" if curr_view == "Planner Workspace" else "📅 Planner"
        if st.button(btn_label, type="secondary", use_container_width=True, help="Switch between Planner and Validation/Benchmarks Lab"):
            st.session_state.app_view_mode = "Validation Lab" if curr_view == "Planner Workspace" else "Planner Workspace"
            st.rerun()

# ---------------------------------------------------------------------------
# Collapsed Model Configuration & Host Settings
# ---------------------------------------------------------------------------
with st.expander("⚙️ Model Configuration & Host Settings", expanded=False):
    cfg_c1, cfg_c2, cfg_c3 = st.columns(3)
    with cfg_c1:
        model_options = ["qwen2.5:1.5b", "qwen3:4b"]
        if server_status.get("models"):
            for m in server_status["models"]:
                if m not in model_options:
                    model_options.append(m)
        chosen_model = st.selectbox(
            "Local Ollama Model",
            options=model_options,
            index=0 if "qwen2.5:1.5b" in model_options else 0,
            help="qwen2.5:1.5b is recommended for fast CPU generation (~75s).",
        )
        st.session_state.ollama_model = chosen_model

    with cfg_c2:
        chosen_prompt = st.selectbox(
            "Prompt Guardrail Strategy",
            options=["v3", "v2", "v1"],
            format_func=lambda x: {
                "v3": "V3: Grounded Guardrails (Production)",
                "v2": "V2: Few-Shot Schema (Experimental)",
                "v1": "V1: Zero-Shot Baseline (Milestone 1)",
            }[x],
            index=0,
        )
        st.session_state.prompt_version = chosen_prompt

    with cfg_c3:
        host_url = st.text_input("Host URL", value=st.session_state.ollama_url)
        st.session_state.ollama_url = host_url
        timeout_val = st.slider("Timeout (seconds)", 60, 600, int(st.session_state.ollama_timeout), 30)
        st.session_state.ollama_timeout = timeout_val

st.markdown("<hr style='border:none;border-top:1px solid rgba(255,255,255,0.08);margin:10px 0 20px 0;'/>", unsafe_allow_html=True)


# ===========================================================================
# VIEW 1: MAIN PLANNER WORKSPACE
# ===========================================================================
if st.session_state.app_view_mode == "Planner Workspace":
    # Two desktop columns: Wider inputs (1.55), Smaller live summary (1.0)
    col_inputs, col_summary = st.columns([1.55, 1.0], gap="large")

    # -----------------------------------------------------------------------
    # WIDER COLUMN: PLANNING INPUTS
    # -----------------------------------------------------------------------
    with col_inputs:
        # PANEL 1 — Study Period
        st.markdown("<div class='panel-box'>", unsafe_allow_html=True)
        st.markdown("<div class='panel-heading'>📅 1. Study Period & Daily Time Budget</div>", unsafe_allow_html=True)
        
        sp_c1, sp_c2, sp_c3 = st.columns(3)
        with sp_c1:
            inp_start = st.date_input("Start Date", value=st.session_state.start_date, key="inp_start_date")
            st.session_state.start_date = inp_start
        with sp_c2:
            inp_end = st.date_input("End Date", value=st.session_state.end_date, key="inp_end_date")
            st.session_state.end_date = inp_end
        with sp_c3:
            equivalent_hours = round(st.session_state.default_minutes / 60.0, 1)
            inp_minutes = st.number_input(
                f"Default Daily Study Budget (Minutes) — {equivalent_hours} hrs/day",
                min_value=30,
                max_value=720,
                step=15,
                value=int(st.session_state.default_minutes),
                key="inp_default_minutes",
                help="Base available study time on standard days.",
            )
            st.session_state.default_minutes = inp_minutes

        st.markdown("</div>", unsafe_allow_html=True)

        # PANEL 2 — Subjects & Examinations (with stable IDs)
        st.markdown("<div class='panel-box'>", unsafe_allow_html=True)
        st.markdown("<div class='panel-heading'>📖 2. Enrolled Subjects & Examination Dates</div>", unsafe_allow_html=True)
        st.caption("Provide course names, exam dates, and designate priority subjects requiring focused review.")

        subject_to_delete: Optional[str] = None
        updated_subjects = []

        for idx, sub in enumerate(st.session_state.subjects_data):
            uid = sub["id"]
            sc1, sc2, sc3, sc4 = st.columns([3.6, 2.5, 2.2, 0.6])
            with sc1:
                s_name = st.text_input(
                    "Subject Name",
                    value=sub["name"],
                    key=f"name_{uid}",
                    label_visibility="collapsed" if idx > 0 else "visible",
                    placeholder="e.g. Data Structures & Algorithms",
                )
            with sc2:
                s_date = st.date_input(
                    "Exam Date",
                    value=sub["exam_date"],
                    key=f"date_{uid}",
                    label_visibility="collapsed" if idx > 0 else "visible",
                )
            with sc3:
                if idx == 0:
                    st.markdown("<div style='height:26px;'></div>", unsafe_allow_html=True)
                s_attention = st.checkbox(
                    "Needs extra attention",
                    value=sub.get("attention", False),
                    key=f"att_{uid}",
                    help="Allocates prioritized revision blocks.",
                )
            with sc4:
                if idx == 0:
                    st.markdown("<div style='height:26px;'></div>", unsafe_allow_html=True)
                if st.button("🗑️", key=f"del_{uid}", help="Remove subject"):
                    subject_to_delete = uid

            # Optional topic accordion per subject
            with st.expander(f"Optional Focus Topics for {s_name or f'Subject #{idx+1}'}", expanded=bool(sub.get("topics"))):
                s_topics = st.text_input(
                    "Key topics requiring revision",
                    value=sub.get("topics", ""),
                    key=f"top_{uid}",
                    placeholder="e.g. Dynamic Programming, Trees, Graph Algorithms",
                    label_visibility="collapsed",
                )

            updated_subjects.append({
                "id": uid,
                "name": s_name,
                "exam_date": s_date,
                "attention": s_attention,
                "topics": s_topics,
            })

        if subject_to_delete:
            st.session_state.subjects_data = [s for s in updated_subjects if s["id"] != subject_to_delete]
            st.rerun()
        else:
            st.session_state.subjects_data = updated_subjects

        if st.button("➕ Add subject", key="btn_add_subject"):
            new_uid = f"sub_{uuid.uuid4().hex[:6]}"
            st.session_state.subjects_data.append({
                "id": new_uid,
                "name": "",
                "exam_date": st.session_state.end_date,
                "attention": False,
                "topics": "",
            })
            st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

        # PANEL 3 — Availability & Rest Days
        st.markdown("<div class='panel-box'>", unsafe_allow_html=True)
        st.markdown("<div class='panel-heading'>🧘 3. Daily Availability & Rest Days</div>", unsafe_allow_html=True)

        cur_start = st.session_state.start_date
        cur_end = st.session_state.end_date

        all_calendar_dates: List[str] = []
        if cur_start <= cur_end:
            cur_iter = cur_start
            while cur_iter <= cur_end:
                all_calendar_dates.append(cur_iter.isoformat())
                cur_iter += timedelta(days=1)

        # Rest-day selection
        valid_rest_options = [d for d in st.session_state.get("rest_days", []) if d in all_calendar_dates]
        chosen_rest_days = st.multiselect(
            "Designate Scheduled Rest Days (0 min available study time):",
            options=all_calendar_dates,
            default=valid_rest_options,
            help="Dates designated as rest days strictly allocate 0 minutes of study.",
        )
        st.session_state.rest_days = chosen_rest_days

        # Enforce conflict rule: A rest day must have 0 minutes in overrides
        for rd in chosen_rest_days:
            st.session_state.overrides[rd] = 0

        # Expandable editor for date-specific study-minute overrides
        with st.expander("Configure Date-Specific Study Budgets", expanded=False):
            st.caption("Override study time on specific calendar days (e.g. 240 minutes before an examination).")
            non_rest_dates = [d for d in all_calendar_dates if d not in chosen_rest_days]
            if non_rest_dates:
                ov_c1, ov_c2 = st.columns(2)
                for i, dt_str in enumerate(non_rest_dates):
                    target_col = ov_c1 if i % 2 == 0 else ov_c2
                    with target_col:
                        cur_override_val = st.session_state.overrides.get(dt_str, int(st.session_state.default_minutes))
                        new_ov = st.number_input(
                            f"{dt_str} Budget (min)",
                            min_value=15,
                            max_value=720,
                            step=15,
                            value=int(cur_override_val) if cur_override_val > 0 else int(st.session_state.default_minutes),
                            key=f"ov_input_{dt_str}",
                        )
                        if new_ov != st.session_state.default_minutes:
                            st.session_state.overrides[dt_str] = new_ov
                        elif dt_str in st.session_state.overrides and dt_str not in chosen_rest_days:
                            del st.session_state.overrides[dt_str]

        # Flag overrides falling outside planning period
        out_of_bounds = [d for d in st.session_state.overrides if d not in all_calendar_dates]
        if out_of_bounds:
            st.caption(f"⚠️ **Notice:** {len(out_of_bounds)} date override(s) ({', '.join(out_of_bounds[:3])}) fall outside [{cur_start} to {cur_end}] and are ignored.")

        # Concise summary of active overrides
        active_adjustments = {
            d: m for d, m in st.session_state.overrides.items()
            if d in all_calendar_dates
        }
        if active_adjustments:
            st.markdown("**Active Date Overrides:**")
            chips = []
            for d, m in sorted(active_adjustments.items()):
                if m == 0:
                    chips.append(f"🏖️ `{d}: 0m (Rest Day)`")
                else:
                    chips.append(f"⏱️ `{d}: {m}m`")
            st.markdown(" • ".join(chips))
        else:
            st.caption("Standard default daily budget applied to all active dates.")

        st.markdown("</div>", unsafe_allow_html=True)

        # PANEL 4 — Preferences (Collapsed Optional)
        st.markdown("<div class='panel-box'>", unsafe_allow_html=True)
        with st.expander("⚙️ 4. Study Preferences & Style (Optional)", expanded=False):
            st.caption("Study style preferences (e.g. 45-minute focus intervals, morning formula recall) are applied where feasible within the hard academic constraints.")
            inp_pref = st.text_input(
                "Preferences",
                value=st.session_state.preferences,
                placeholder="e.g. 45-min Pomodoro blocks, problem solving for weak topics, quick morning recall",
                label_visibility="collapsed",
            )
            st.session_state.preferences = inp_pref
        st.markdown("</div>", unsafe_allow_html=True)

    # -----------------------------------------------------------------------
    # SMALLER COLUMN: LIVE CONFIGURATION SUMMARY
    # -----------------------------------------------------------------------
    with col_summary:
        st.markdown("<div class='summary-box'>", unsafe_allow_html=True)
        st.markdown("<h4 style='color:#FFFFFF;margin-top:0;margin-bottom:14px;font-size:1.05rem;'>📋 Live Configuration Summary</h4>", unsafe_allow_html=True)

        # Compute live statistics
        valid_subjects = [s for s in st.session_state.subjects_data if s["name"].strip()]
        num_subjects_cnt = len(valid_subjects)

        if cur_start <= cur_end:
            num_planning_days = (cur_end - cur_start).days + 1
        else:
            num_planning_days = 0

        total_avail_capacity_mins = 0
        if cur_start <= cur_end:
            d_iter = cur_start
            while d_iter <= cur_end:
                d_str = d_iter.isoformat()
                if d_str in st.session_state.rest_days:
                    total_avail_capacity_mins += 0
                elif d_str in st.session_state.overrides:
                    total_avail_capacity_mins += st.session_state.overrides[d_str]
                else:
                    total_avail_capacity_mins += int(st.session_state.default_minutes)
                d_iter += timedelta(days=1)
        total_avail_hours = round(total_avail_capacity_mins / 60.0, 1)

        priority_subjs = [s["name"].strip() for s in valid_subjects if s.get("attention")]
        priority_display = ", ".join(priority_subjs) if priority_subjs else "None designated"

        valid_exams = [s["exam_date"] for s in valid_subjects if s["exam_date"] >= cur_start]
        if valid_exams:
            earliest_dt = min(valid_exams)
            earliest_name = next(s["name"] for s in valid_subjects if s["exam_date"] == earliest_dt)
            earliest_exam_display = f"{earliest_dt.strftime('%b %d, %Y')} ({earliest_name})"
        else:
            earliest_exam_display = "No exams in window"

        # Summary Metrics
        st.markdown(
            f"""
            <div class="summary-item">
                <span class="summary-label">Enrolled Subjects</span>
                <span class="summary-val">{num_subjects_cnt}</span>
            </div>
            <div class="summary-item">
                <span class="summary-label">Planning Window</span>
                <span class="summary-val">{num_planning_days} days</span>
            </div>
            <div class="summary-item">
                <span class="summary-label">Total Study Capacity</span>
                <span class="summary-val">{total_avail_hours} hrs</span>
            </div>
            <div class="summary-item">
                <span class="summary-label">Priority Attention</span>
                <span class="summary-val" style="color:#C7D2FE;">{priority_display}</span>
            </div>
            <div class="summary-item">
                <span class="summary-label">Earliest Examination</span>
                <span class="summary-val" style="color:#FBBF24;">{earliest_exam_display}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Missing inputs and conflicts detection
        validation_conflicts: List[str] = []
        if cur_start > cur_end:
            validation_conflicts.append("Start date cannot be after end date.")
        if num_subjects_cnt == 0:
            validation_conflicts.append("Add at least one course.")

        seen_lower = set()
        for s in st.session_state.subjects_data:
            s_clean = s["name"].strip()
            if not s_clean:
                validation_conflicts.append("One or more subjects have blank names.")
                break
            if s_clean.lower() in seen_lower:
                validation_conflicts.append(f"Duplicate subject name: '{s_clean}'.")
            seen_lower.add(s_clean.lower())
            if s["exam_date"] < cur_start:
                validation_conflicts.append(f"Exam for '{s_clean}' is before planning start date.")

        if validation_conflicts:
            st.markdown(
                """
                <div style="background:rgba(239, 68, 68, 0.12);border:1px solid rgba(239, 68, 68, 0.35);border-radius:8px;padding:12px;margin-top:16px;">
                    <strong style="color:#F87171;font-size:0.86rem;">⚠️ Configuration Conflicts:</strong>
                """,
                unsafe_allow_html=True,
            )
            for conf in validation_conflicts:
                st.markdown(f"<small style='color:#FECACA;'>• {conf}</small><br/>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.markdown(
                """
                <div style="background:rgba(16, 185, 129, 0.12);border:1px solid rgba(16, 185, 129, 0.35);border-radius:8px;padding:12px;margin-top:16px;">
                    <span style="color:#34D399;font-size:0.85rem;font-weight:600;">✅ Configuration verified and ready for generation.</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("</div>", unsafe_allow_html=True)

    # -----------------------------------------------------------------------
    # GENERATION ACTION (Beneath the Form)
    # -----------------------------------------------------------------------
    st.markdown("<br/>", unsafe_allow_html=True)

    # Build validated domain model
    current_plan_input = StudyPlanInput(
        start_date=st.session_state.start_date.isoformat(),
        end_date=st.session_state.end_date.isoformat(),
        subjects=[
            SubjectInput(name=s["name"].strip(), exam_date=s["exam_date"].isoformat())
            for s in st.session_state.subjects_data
            if s["name"].strip()
        ],
        default_daily_minutes=int(st.session_state.default_minutes),
        daily_overrides={
            d: m for d, m in st.session_state.overrides.items()
            if d >= st.session_state.start_date.isoformat() and d <= st.session_state.end_date.isoformat()
        },
        weak_subjects=[s["name"].strip() for s in st.session_state.subjects_data if s.get("attention") and s["name"].strip()],
        weak_topics="\n".join([f"{s['name']}: {s['topics']}" for s in st.session_state.subjects_data if s.get("topics") and s["name"].strip()]),
        preferences=st.session_state.preferences,
    )

    input_validation_errors = validate_inputs(current_plan_input)

    btn_gen_col1, btn_gen_col2, btn_gen_col3 = st.columns([1, 2, 1])
    with btn_gen_col2:
        generate_clicked = st.button(
            "⚡ Generate study plan",
            type="primary",
            use_container_width=True,
            disabled=bool(input_validation_errors) or st.session_state.is_generating,
        )

    if input_validation_errors:
        st.markdown("<div style='background:rgba(239, 68, 68, 0.1);border:1px solid rgba(239,68,68,0.3);border-radius:8px;padding:12px;margin-top:12px;'>", unsafe_allow_html=True)
        st.markdown("<strong style='color:#F87171;'>Cannot generate: Please resolve input issues</strong>", unsafe_allow_html=True)
        for err in input_validation_errors:
            st.markdown(f"<small style='color:#FECACA;'>• {err}</small><br/>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    if generate_clicked:
        st.session_state.is_generating = True
        prompt_to_send = build_study_plan_prompt(current_plan_input, version=st.session_state.prompt_version)
        st.session_state.last_prompt_rendered = prompt_to_send

        clock_start = time.time()
        with st.status("Creating your study plan…", expanded=True) as status_box:
            st.write(f"Connecting to local Ollama engine (`{st.session_state.ollama_model}`)...")
            try:
                raw_resp, model_tag = call_ollama_study_planner(
                    prompt=prompt_to_send,
                    base_url=st.session_state.ollama_url,
                    model=st.session_state.ollama_model,
                    timeout=st.session_state.ollama_timeout,
                )
                elapsed_sec = time.time() - clock_start
                st.write(f"Local Ollama generation finished in {elapsed_sec:.1f}s.")
                st.write("Verifying schedule with pure-Python academic validator...")

                val_result = validate_plan_output(raw_resp, current_plan_input)
                st.session_state.active_plan_result = val_result
                st.session_state.last_execution_sec = elapsed_sec
                st.session_state.last_raw_response = raw_resp
                st.session_state.last_method_label = f"Local Ollama ({model_tag})"

                # Capture exact input snapshot for stale-plan detection
                st.session_state.last_plan_input_snapshot = {
                    "start_date": current_plan_input.start_date,
                    "end_date": current_plan_input.end_date,
                    "subjects": [(s.name, s.exam_date) for s in current_plan_input.subjects],
                    "default_minutes": current_plan_input.default_daily_minutes,
                    "overrides": dict(current_plan_input.daily_overrides),
                    "weak_subjects": list(current_plan_input.weak_subjects),
                    "preferences": current_plan_input.preferences,
                }

                # Log completed experiment run
                total_sched_mins = sum(d.used_minutes for d in val_result.schedule)
                log_completed_run(
                    engine="Local Ollama",
                    model=model_tag,
                    prompt_version=st.session_state.prompt_version,
                    dataset_name="User Planner Configuration",
                    is_valid=val_result.is_valid,
                    errors_count=len(val_result.errors),
                    warnings_count=len(val_result.warnings),
                    total_minutes=total_sched_mins,
                    execution_time_sec=round(elapsed_sec, 1),
                    notes=f"Interactive generation via {st.session_state.prompt_version}",
                )

                if val_result.is_valid:
                    status_box.update(label=f"Study plan generated and verified in {elapsed_sec:.1f}s!", state="complete", expanded=False)
                    st.toast("Your personalized study plan is ready!", icon="🎉")
                else:
                    status_box.update(label=f"Plan generated with {len(val_result.errors)} rule violations.", state="error", expanded=True)

            except Exception as exc:
                elapsed_sec = time.time() - clock_start
                status_box.update(label="Generation failed.", state="error", expanded=True)
                st.error(f"⚠️ **Ollama Execution Error:** {exc}")
                st.info("Check that Ollama is running (`ollama serve`) and the model is downloaded (`ollama pull qwen2.5:1.5b`).")
                st.session_state.active_plan_result = None
            finally:
                st.session_state.is_generating = False

    # -----------------------------------------------------------------------
    # FULL-WIDTH RESULT WORKSPACE
    # -----------------------------------------------------------------------
    if st.session_state.active_plan_result:
        plan_res: ValidationResult = st.session_state.active_plan_result

        st.markdown("<div class='timetable-container'>", unsafe_allow_html=True)

        # Check for stale plan: compare current inputs with snapshot
        current_snapshot = {
            "start_date": current_plan_input.start_date,
            "end_date": current_plan_input.end_date,
            "subjects": [(s.name, s.exam_date) for s in current_plan_input.subjects],
            "default_minutes": current_plan_input.default_daily_minutes,
            "overrides": dict(current_plan_input.daily_overrides),
            "weak_subjects": list(current_plan_input.weak_subjects),
            "preferences": current_plan_input.preferences,
        }
        if st.session_state.last_plan_input_snapshot and (st.session_state.last_plan_input_snapshot != current_snapshot):
            st.markdown(
                """
                <div class="stale-plan-banner">
                    <span>⚠️ <strong>Configuration Changed:</strong> The timetable below was generated using your previous inputs. Click <em>"Generate study plan"</em> to refresh.</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

        if not plan_res.is_valid:
            st.error("🚨 **Plan Validation Rejected!** The generated timetable violated academic scheduling constraints:")
            for err in plan_res.errors:
                st.markdown(f"- ❌ {err}")
            with st.expander("Inspect Raw JSON Response"):
                st.code(st.session_state.last_raw_response or "", language="json")
        else:
            # Calculate metrics from validated schedule
            total_active_mins = sum(d.used_minutes for d in plan_res.schedule)
            total_sched_hours = round(total_active_mins / 60.0, 1)
            num_active_study_days = sum(1 for d in plan_res.schedule if d.used_minutes > 0)
            total_unused_capacity_mins = sum(max(0, d.available_minutes - d.used_minutes) for d in plan_res.schedule)

            # Header & Factual Metrics
            res_head_col1, res_head_col2 = st.columns([2.5, 1.5])
            with res_head_col1:
                st.markdown("### 🗓️ Your Study Plan")
            with res_head_col2:
                st.markdown(
                    "<div style='text-align:right;margin-top:6px;'><span style='background:rgba(16,185,129,0.18);color:#34D399;border:1px solid rgba(16,185,129,0.4);padding:5px 12px;border-radius:20px;font-size:0.82rem;font-weight:700;'>Passed scheduling checks</span></div>",
                    unsafe_allow_html=True,
                )

            m1, m2, m3, m4 = st.columns(4)
            with m1:
                st.metric("Total Scheduled", f"{total_sched_hours} hrs")
            with m2:
                st.metric("Active Study Days", f"{num_active_study_days} days")
            with m3:
                st.metric("Unused Capacity", f"{total_unused_capacity_mins} min")
            with m4:
                st.metric("Engine Latency", f"{st.session_state.last_execution_sec:.1f}s")

            # Warnings / Trade-offs close to result
            if plan_res.warnings:
                with st.expander(f"ℹ️ Scheduling Trade-Offs & Advisory Notes ({len(plan_res.warnings)})", expanded=False):
                    for w in plan_res.warnings:
                        st.caption(f"• {w}")

            # View Mode Selector: Agenda View vs Table View
            st.markdown("<br/>", unsafe_allow_html=True)
            v_col1, v_col2 = st.columns([2, 2])
            with v_col1:
                view_mode = st.radio(
                    "Select Timetable View:",
                    options=["Agenda View", "Table View"],
                    horizontal=True,
                    label_visibility="collapsed",
                )

            # ---------------------------------------------------------------
            # 1. AGENDA VIEW
            # ---------------------------------------------------------------
            if view_mode == "Agenda View":
                # Export Full Agenda CSV
                exp_col1, exp_col2 = st.columns([3, 1])
                with exp_col2:
                    csv_buf = io.StringIO()
                    csv_w = csv.writer(csv_buf)
                    csv_w.writerow(["Date", "Day", "Subject", "Activity", "Task", "Duration (Minutes)", "Daily Budget (Minutes)"])
                    for day in plan_res.schedule:
                        d_dt = datetime.strptime(day.date, "%Y-%m-%d")
                        dw = d_dt.strftime("%A")
                        if not day.sessions:
                            csv_w.writerow([day.date, dw, "Rest Day" if day.available_minutes == 0 else "No Session", "Recovery", "Rest", 0, day.available_minutes])
                        else:
                            for s in day.sessions:
                                csv_w.writerow([day.date, dw, s.subject, map_activity_category(s.activity), s.task, s.duration_minutes, day.available_minutes])

                    st.download_button(
                        label="📥 Download Full Study Plan (CSV)",
                        data=csv_buf.getvalue(),
                        file_name=f"prepflow_study_plan_{current_plan_input.start_date}.csv",
                        mime="text/csv",
                        use_container_width=True,
                    )

                # Chronological Agenda Cards
                for day in plan_res.schedule:
                    d_dt = datetime.strptime(day.date, "%Y-%m-%d")
                    day_label = d_dt.strftime("%A, %B %d, %Y")
                    is_rest = (day.available_minutes == 0)

                    st.markdown("<div class='day-agenda-card'>", unsafe_allow_html=True)

                    # Heading with budget & utilization bar
                    st.markdown(
                        f"""
                        <div class="day-agenda-header">
                            <div>
                                <strong style="font-size:1.02rem;color:#F8FAFC;">📅 {day_label}</strong>
                            </div>
                            <div>
                                <span style="font-size:0.84rem;color:#CBD5E1;font-weight:600;">
                                    {'🏖️ Rest day' if is_rest else f'⏱️ {day.used_minutes} / {day.available_minutes} min scheduled'}
                                </span>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    # Budget-utilization bar
                    if day.available_minutes > 0:
                        pct_used = min(1.0, day.used_minutes / max(1, day.available_minutes))
                        st.progress(pct_used)

                    if is_rest:
                        st.markdown("<div style='color:#FCD34D;font-size:0.88rem;padding:6px 0;'>🏖️ <strong>Rest day</strong> — Zero study sessions scheduled. Take time to relax and recover.</div>", unsafe_allow_html=True)
                    elif not day.sessions:
                        st.markdown("<div style='color:#94A3B8;font-size:0.88rem;padding:6px 0;'>ℹ️ <em>No sessions scheduled</em> — Available study capacity was not required for revision targets.</div>", unsafe_allow_html=True)
                    else:
                        for s in day.sessions:
                            subj_style = get_subject_style(s.subject)
                            cat = map_activity_category(s.activity)
                            badge_cls = "act-revision" if cat == "Revision" else ("act-practice" if cat == "Practice" else "act-study")

                            st.markdown(
                                f"""
                                <div class="session-agenda-row" style="border-left: 4px solid {subj_style['border']};">
                                    <div style="display:flex;flex-direction:column;gap:3px;">
                                        <div style="font-size:0.92rem;font-weight:700;color:{subj_style['text']};">
                                            {subj_style['icon']} {s.subject}
                                        </div>
                                        <div style="font-size:0.86rem;color:#E2E8F0;">
                                            {s.task}
                                        </div>
                                    </div>
                                    <div style="display:flex;align-items:center;gap:12px;">
                                        <span class="act-badge {badge_cls}">{cat}</span>
                                        <span style="font-weight:700;font-size:0.88rem;color:#F8FAFC;">⏱️ {s.duration_minutes}m</span>
                                    </div>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )

                    st.markdown("</div>", unsafe_allow_html=True)

            # ---------------------------------------------------------------
            # 2. TABLE VIEW
            # ---------------------------------------------------------------
            elif view_mode == "Table View":
                # Filters
                all_plan_subjects = sorted(list(set(s.subject for d in plan_res.schedule for s in d.sessions)))
                all_plan_dates = [d.date for d in plan_res.schedule]

                tf_c1, tf_c2 = st.columns(2)
                with tf_c1:
                    filter_subject = st.selectbox("Filter by Subject", options=["All Subjects"] + all_plan_subjects)
                with tf_c2:
                    filter_date = st.selectbox("Filter by Date", options=["All Dates"] + all_plan_dates)

                # Filtered row construction
                table_rows = []
                for day in plan_res.schedule:
                    if filter_date != "All Dates" and day.date != filter_date:
                        continue
                    for s in day.sessions:
                        if filter_subject != "All Subjects" and s.subject != filter_subject:
                            continue
                        cat = map_activity_category(s.activity)
                        table_rows.append({
                            "Date": day.date,
                            "Subject": s.subject,
                            "Activity": cat,
                            "Task Description": s.task,
                            "Minutes": s.duration_minutes,
                        })

                # Table Display
                if table_rows:
                    st.dataframe(table_rows, use_container_width=True)
                else:
                    st.info("No study sessions match your filter criteria.")

                # Filter-Aware CSV Download
                csv_buf_filtered = io.StringIO()
                csv_w = csv.writer(csv_buf_filtered)
                csv_w.writerow(["Date", "Subject", "Activity", "Task Description", "Minutes"])
                for r in table_rows:
                    csv_w.writerow([r["Date"], r["Subject"], r["Activity"], r["Task Description"], r["Minutes"]])

                is_filtered = (filter_subject != "All Subjects") or (filter_date != "All Dates")
                download_label = "📥 Download Filtered Plan (CSV)" if is_filtered else "📥 Download Full Plan (CSV)"

                st.download_button(
                    label=download_label,
                    data=csv_buf_filtered.getvalue(),
                    file_name="prepflow_filtered_schedule.csv" if is_filtered else "prepflow_full_schedule.csv",
                    mime="text/csv",
                    type="secondary",
                )

            # Collapsible Developer Inspector
            with st.expander("🛠️ Developer Inspector (Rendered Prompt & Raw JSON)", expanded=False):
                tab_pr, tab_js = st.tabs(["Rendered Prompt Sent", "Raw Model Response Received"])
                with tab_pr:
                    st.code(st.session_state.last_prompt_rendered or "", language="markdown")
                with tab_js:
                    st.code(st.session_state.last_raw_response or "", language="json")

        st.markdown("</div>", unsafe_allow_html=True)


# ===========================================================================
# VIEW 2: TESTING, FIXTURES & BENCHMARK LAB
# ===========================================================================
elif st.session_state.app_view_mode == "Validation Lab":
    st.markdown("### 🧪 Testing, Fixtures & Benchmark Lab")
    st.caption("Inspect pure-Python validator behavior, pre-built test fixtures, preserved prompt iterations, and empirical experiment history.")

    lab_tab1, lab_tab2, lab_tab3, lab_tab4 = st.tabs([
        "🔬 Offline Validator & Pasted JSON",
        "📦 Benchmark Test Fixtures",
        "🎯 Prompt Iterations (v1, v2, v3)",
        "📊 Experiment Run History",
    ])

    # LAB TAB 1: Pasted-Response Validation
    with lab_tab1:
        st.markdown("#### Test Validator with Custom JSON Payload")
        st.caption("Paste any raw model output to audit it against the 9 academic scheduling guardrails without executing Ollama.")

        pasted_json = st.text_area(
            "Paste JSON Response Payload:",
            height=200,
            placeholder='{\n  "schedule": [\n    {\n      "date": "2026-12-01",\n      "sessions": []\n    }\n  ]\n}',
        )
        if st.button("🔎 Audit Pasted JSON", type="primary"):
            sample_in = get_sample_input()
            audit_res = validate_plan_output(pasted_json, sample_in)
            if audit_res.is_valid:
                st.success("🎉 **PASS: Schedule satisfied all 9 academic constraints!**")
                st.metric("Validated Calendar Days", len(audit_res.schedule))
            else:
                st.error(f"❌ **FAIL: Validator caught {len(audit_res.errors)} rule violation(s):**")
                for e in audit_res.errors:
                    st.markdown(f"- {e}")

    # LAB TAB 2: Pre-Built Test Fixtures
    with lab_tab2:
        st.markdown("#### Pre-Built Academic Test Fixtures")
        fixtures_dict = {
            "Valid 14-Day Study Plan (DSA, DBMS, OS, NLP) [Live Pass]": FIXTURE_VALID_RESPONSE_JSON,
            "Daily Budget Overrun (270 min > 180 min limit) [Rule Violation]": FIXTURE_INVALID_BUDGET_OVERRUN_JSON,
            "Post-Exam Study Session (DSA studied after exam date) [Rule Violation]": FIXTURE_INVALID_POST_EXAM_JSON,
            "Sessions on 0-Minute Rest Day [Rule Violation]": FIXTURE_INVALID_REST_DAY_JSON,
            "Unknown Subject & Negative Duration [Rule Violation]": FIXTURE_INVALID_UNKNOWN_SUBJECT_JSON,
        }
        chosen_fix_name = st.selectbox("Select Test Fixture to Inspect:", options=list(fixtures_dict.keys()))
        selected_payload = fixtures_dict[chosen_fix_name]

        fix_col1, fix_col2 = st.columns([1, 1])
        with fix_col1:
            st.markdown("**Fixture JSON Content:**")
            st.code(selected_payload, language="json")
        with fix_col2:
            st.markdown("**Automated Audit Evaluation:**")
            test_in = get_sample_input()
            f_res = validate_plan_output(selected_payload, test_in)
            if f_res.is_valid:
                st.success("✅ **PASS**: Meets all 9 constraints.")
            else:
                st.error(f"❌ **FAIL**: Caught {len(f_res.errors)} expected violation(s):")
                for err in f_res.errors:
                    st.markdown(f"- {err}")

    # LAB TAB 3: Prompt Engineering Template Comparison
    with lab_tab3:
        st.markdown("#### Prompt Engineering Evolution: v1 → v2 → v3")
        sample_in = get_sample_input()

        pv_sel = st.selectbox(
            "Select Prompt Version to Inspect:",
            options=["v3", "v2", "v1"],
            format_func=lambda x: PROMPT_VERSIONS[x],
        )
        rendered_pv = build_study_plan_prompt(sample_in, version=pv_sel)
        st.code(rendered_pv, language="markdown")

    # LAB TAB 4: Experiment History Log
    with lab_tab4:
        st.markdown("#### Completed Empirical Benchmark Runs")
        experiments = get_experiments()
        if not experiments:
            st.info("No completed experiment runs logged yet.")
        else:
            display_runs = []
            for exp in reversed(experiments):
                display_runs.append({
                    "Run #": exp["run_id"],
                    "Timestamp": exp["timestamp"],
                    "Engine": exp["engine"],
                    "Model": exp["model"],
                    "Prompt Version": exp["prompt_version"],
                    "Status": "✅ PASS" if exp["status"] == "PASS" else "❌ FAIL",
                    "Errors": exp["errors_count"],
                    "Duration": f"{exp['latency_seconds']}s",
                    "Notes": exp.get("notes", ""),
                })
            st.dataframe(display_runs, use_container_width=True)
