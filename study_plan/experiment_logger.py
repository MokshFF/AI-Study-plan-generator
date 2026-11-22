"""Experiment Logging Module for Prompt Engineering Evaluation.

Problem ID: C20 - Bennett University Prompt Engineering Mini-Project
Rule: Update the experiment logs only with completed runs.
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

EXPERIMENTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "experiments")
LOG_JSON_PATH = os.path.join(EXPERIMENTS_DIR, "experiment_log.json")
LOG_MD_PATH = os.path.join(EXPERIMENTS_DIR, "experiment_log.md")


def get_experiments() -> List[Dict[str, Any]]:
    """Loads all completed experiment runs from the log file."""
    if not os.path.exists(LOG_JSON_PATH):
        return []
    try:
        with open(LOG_JSON_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def log_completed_run(
    engine: str,
    model: str,
    prompt_version: str,
    dataset_name: str,
    is_valid: bool,
    errors_count: int,
    warnings_count: int,
    total_minutes: int,
    execution_time_sec: float,
    notes: str = "",
) -> Dict[str, Any]:
    """Records a completed experiment run to both JSON and Markdown experiment logs.

    Only invoked when a model generation or test fixture evaluation actually completes.
    """
    os.makedirs(EXPERIMENTS_DIR, exist_ok=True)

    experiments = get_experiments()

    run_entry = {
        "run_id": len(experiments) + 1,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "engine": engine,
        "model": model,
        "prompt_version": prompt_version,
        "dataset": dataset_name,
        "status": "PASS" if is_valid else "FAIL",
        "errors_count": errors_count,
        "warnings_count": warnings_count,
        "total_minutes_scheduled": total_minutes,
        "latency_seconds": round(execution_time_sec, 2),
        "notes": notes,
    }

    experiments.append(run_entry)

    # Save JSON log
    with open(LOG_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(experiments, f, indent=2)

    # Save Markdown summary log
    _write_markdown_log(experiments)

    return run_entry


def _write_markdown_log(experiments: List[Dict[str, Any]]) -> None:
    """Regenerates the human-readable Markdown log."""
    md_lines = [
        "# 🧪 Study Plan Generator - Prompt Engineering Experiment Log",
        "",
        "**Problem ID**: C20 | **Bennett University Mini-Project**",
        "",
        "This log records completed evaluation runs comparing local Ollama models (`qwen3:4b`, `qwen2.5:3b`) and prompt iterations (v1, v2, v3).",
        "",
        "| Run # | Timestamp | Engine / Model | Prompt Version | Status | Errors | Warnings | Duration (s) | Notes |",
        "| :---: | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |",
    ]

    for exp in experiments:
        status_badge = "✅ PASS" if exp["status"] == "PASS" else "❌ FAIL"
        md_lines.append(
            f"| {exp['run_id']} | {exp['timestamp']} | `{exp['engine']} ({exp['model']})` | "
            f"**{exp['prompt_version']}** | {status_badge} | {exp['errors_count']} | "
            f"{exp['warnings_count']} | {exp['latency_seconds']}s | {exp['notes']} |"
        )

    with open(LOG_MD_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines) + "\n")
