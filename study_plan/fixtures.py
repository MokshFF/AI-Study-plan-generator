"""Test Fixtures and Fictional University Student Data.

Problem ID: C20 - Bennett University Prompt Engineering Mini-Project
Includes:
- Fictional DSA, DBMS, OS, and NLP dataset for quick form population.
- Pre-built test fixtures (clearly labeled) to test validation without API keys.
"""

import json
from study_plan.validator import StudyPlanInput, SubjectInput

# Fictional Student Dataset
SAMPLE_START_DATE = "2026-12-01"
SAMPLE_END_DATE = "2026-12-14"

SAMPLE_SUBJECTS = [
    SubjectInput(name="Data Structures & Algorithms", exam_date="2026-12-05"),
    SubjectInput(name="Database Management Systems", exam_date="2026-12-08"),
    SubjectInput(name="Operating Systems", exam_date="2026-12-11"),
    SubjectInput(name="Natural Language Processing", exam_date="2026-12-14"),
]

SAMPLE_DEFAULT_DAILY_MINUTES = 180

SAMPLE_OVERRIDES = {
    "2026-12-04": 240,  # Day before DSA exam: intensive revision
    "2026-12-06": 0,    # Day after DSA exam: scheduled rest day
    "2026-12-07": 240,  # Day before DBMS exam
    "2026-12-10": 210,  # Day before OS exam
}

SAMPLE_WEAK_SUBJECTS = [
    "Data Structures & Algorithms",
    "Operating Systems",
]

SAMPLE_WEAK_TOPICS = (
    "DSA: Dynamic Programming, Graph Traversals (Dijkstra, Bellman-Ford), AVL Trees.\n"
    "OS: Virtual Memory, Page Replacement Algorithms, Banker's Algorithm (Deadlocks)."
)

SAMPLE_PREFERENCES = (
    "45-minute focus blocks with 15-minute breaks. "
    "Emphasize past paper problem-solving for weak areas and quick formula revision on exam mornings."
)


def get_sample_input() -> StudyPlanInput:
    """Returns a fresh instance of the fictional student study plan input."""
    return StudyPlanInput(
        start_date=SAMPLE_START_DATE,
        end_date=SAMPLE_END_DATE,
        subjects=[SubjectInput(s.name, s.exam_date) for s in SAMPLE_SUBJECTS],
        default_daily_minutes=SAMPLE_DEFAULT_DAILY_MINUTES,
        daily_overrides=dict(SAMPLE_OVERRIDES),
        weak_subjects=list(SAMPLE_WEAK_SUBJECTS),
        weak_topics=SAMPLE_WEAK_TOPICS,
        preferences=SAMPLE_PREFERENCES,
    )


# ---------------------------------------------------------------------------
# Clearly Labeled Test Fixtures for Independent Validation Verification
# ---------------------------------------------------------------------------

# 1. Fully Valid 14-Day Plan Fixture
FIXTURE_VALID_PLAN_DICT = {
    "schedule": [
        {
            "date": "2026-12-01",
            "sessions": [
                {
                    "subject": "Data Structures & Algorithms",
                    "activity": "Theory",
                    "task": "Review Dynamic Programming concepts: memoization vs tabulation",
                    "duration_minutes": 60,
                },
                {
                    "subject": "Data Structures & Algorithms",
                    "activity": "Practice",
                    "task": "Solve 0/1 Knapsack and Longest Common Subsequence problems",
                    "duration_minutes": 60,
                },
                {
                    "subject": "Database Management Systems",
                    "activity": "Theory",
                    "task": "Review Relational Algebra and Normal Forms (1NF, 2NF, 3NF, BCNF)",
                    "duration_minutes": 60,
                },
            ],
        },
        {
            "date": "2026-12-02",
            "sessions": [
                {
                    "subject": "Data Structures & Algorithms",
                    "activity": "Problem Solving",
                    "task": "Graph Algorithms: Dijkstra's shortest path and Bellman-Ford implementation",
                    "duration_minutes": 90,
                },
                {
                    "subject": "Operating Systems",
                    "activity": "Theory",
                    "task": "Process scheduling algorithms (FCFS, SJF, Round Robin)",
                    "duration_minutes": 45,
                },
                {
                    "subject": "Database Management Systems",
                    "activity": "Practice",
                    "task": "SQL complex queries with nested subqueries and joins",
                    "duration_minutes": 45,
                },
            ],
        },
        {
            "date": "2026-12-03",
            "sessions": [
                {
                    "subject": "Data Structures & Algorithms",
                    "activity": "Practice",
                    "task": "Solve AVL tree insertion, deletion, and rotation problems",
                    "duration_minutes": 90,
                },
                {
                    "subject": "Natural Language Processing",
                    "activity": "Theory",
                    "task": "Text preprocessing: tokenization, lemmatization, and TF-IDF representation",
                    "duration_minutes": 45,
                },
                {
                    "subject": "Operating Systems",
                    "activity": "Problem Solving",
                    "task": "Deadlock detection and Banker's algorithm safe state calculations",
                    "duration_minutes": 45,
                },
            ],
        },
        {
            "date": "2026-12-04",
            "sessions": [
                {
                    "subject": "Data Structures & Algorithms",
                    "activity": "Mock Test",
                    "task": "Comprehensive timed DSA mock test covering arrays, trees, graphs, and DP",
                    "duration_minutes": 120,
                },
                {
                    "subject": "Data Structures & Algorithms",
                    "activity": "Revision",
                    "task": "Analyze mock test mistakes and review standard algorithm complexity tables",
                    "duration_minutes": 60,
                },
                {
                    "subject": "Data Structures & Algorithms",
                    "activity": "Note Review",
                    "task": "Final formula sheet and edge-case review for tomorrow's DSA exam",
                    "duration_minutes": 60,
                },
            ],
        },
        {
            "date": "2026-12-05",  # DSA Exam Day! Study on exam day is allowed by date-level rule
            "sessions": [
                {
                    "subject": "Data Structures & Algorithms",
                    "activity": "Revision",
                    "task": "Exam Morning: Rapid formula recall and asymptotic notation summary",
                    "duration_minutes": 60,
                },
                {
                    "subject": "Database Management Systems",
                    "activity": "Theory",
                    "task": "Post-DSA exam evening: Kick off DBMS indexing (B-Trees, B+ Trees)",
                    "duration_minutes": 60,
                },
                {
                    "subject": "Database Management Systems",
                    "activity": "Practice",
                    "task": "Transaction management and ACID property concurrency questions",
                    "duration_minutes": 60,
                },
            ],
        },
        {
            "date": "2026-12-06",  # Rest Day (0 minutes)
            "sessions": [],
        },
        {
            "date": "2026-12-07",
            "sessions": [
                {
                    "subject": "Database Management Systems",
                    "activity": "Mock Test",
                    "task": "Full-length DBMS mock exam with ER diagrams and normalization",
                    "duration_minutes": 120,
                },
                {
                    "subject": "Database Management Systems",
                    "activity": "Revision",
                    "task": "Review SQL triggers, views, and serializability graphs",
                    "duration_minutes": 60,
                },
                {
                    "subject": "Database Management Systems",
                    "activity": "Note Review",
                    "task": "Pre-exam high-yield DBMS notes review",
                    "duration_minutes": 60,
                },
            ],
        },
        {
            "date": "2026-12-08",  # DBMS Exam Day
            "sessions": [
                {
                    "subject": "Database Management Systems",
                    "activity": "Revision",
                    "task": "Exam Morning: Final glance at SQL syntax and BCNF decomposition rules",
                    "duration_minutes": 45,
                },
                {
                    "subject": "Operating Systems",
                    "activity": "Theory",
                    "task": "Virtual Memory architecture, demand paging, and page fault handling",
                    "duration_minutes": 75,
                },
                {
                    "subject": "Operating Systems",
                    "activity": "Problem Solving",
                    "task": "Page replacement algorithms (FIFO, LRU, Optimal) numericals",
                    "duration_minutes": 60,
                },
            ],
        },
        {
            "date": "2026-12-09",
            "sessions": [
                {
                    "subject": "Operating Systems",
                    "activity": "Practice",
                    "task": "Synchronization primitives: Semaphores, Mutex locks, Dining Philosophers",
                    "duration_minutes": 90,
                },
                {
                    "subject": "Natural Language Processing",
                    "activity": "Theory",
                    "task": "N-gram language models, smoothing techniques (Laplace, Good-Turing)",
                    "duration_minutes": 45,
                },
                {
                    "subject": "Operating Systems",
                    "activity": "Problem Solving",
                    "task": "Disk scheduling algorithms (FCFS, SSTF, SCAN, C-SCAN) calculations",
                    "duration_minutes": 45,
                },
            ],
        },
        {
            "date": "2026-12-10",
            "sessions": [
                {
                    "subject": "Operating Systems",
                    "activity": "Mock Test",
                    "task": "Timed full-syllabus OS mock test",
                    "duration_minutes": 120,
                },
                {
                    "subject": "Operating Systems",
                    "activity": "Revision",
                    "task": "Review weak areas from mock test and memory management diagrams",
                    "duration_minutes": 45,
                },
                {
                    "subject": "Operating Systems",
                    "activity": "Note Review",
                    "task": "OS key definitions and architecture comparison charts",
                    "duration_minutes": 45,
                },
            ],
        },
        {
            "date": "2026-12-11",  # OS Exam Day
            "sessions": [
                {
                    "subject": "Operating Systems",
                    "activity": "Revision",
                    "task": "Exam Morning: Quick formula revision for paging and disk seek calculations",
                    "duration_minutes": 45,
                },
                {
                    "subject": "Natural Language Processing",
                    "activity": "Theory",
                    "task": "Word embeddings: Word2Vec (Skip-gram, CBOW) and GloVe",
                    "duration_minutes": 75,
                },
                {
                    "subject": "Natural Language Processing",
                    "activity": "Practice",
                    "task": "Recurrent Neural Networks (RNN, LSTM, GRU) for sequence tagging",
                    "duration_minutes": 60,
                },
            ],
        },
        {
            "date": "2026-12-12",
            "sessions": [
                {
                    "subject": "Natural Language Processing",
                    "activity": "Theory",
                    "task": "Transformer architecture: self-attention mechanism, multi-head attention",
                    "duration_minutes": 90,
                },
                {
                    "subject": "Natural Language Processing",
                    "activity": "Practice",
                    "task": "BERT vs GPT pre-training objectives and fine-tuning mechanics",
                    "duration_minutes": 90,
                },
            ],
        },
        {
            "date": "2026-12-13",
            "sessions": [
                {
                    "subject": "Natural Language Processing",
                    "activity": "Mock Test",
                    "task": "Full-length NLP mock test covering classic and modern NLP",
                    "duration_minutes": 90,
                },
                {
                    "subject": "Natural Language Processing",
                    "activity": "Revision",
                    "task": "Review attention matrices, evaluation metrics (BLEU, ROUGE, F1)",
                    "duration_minutes": 60,
                },
                {
                    "subject": "Natural Language Processing",
                    "activity": "Note Review",
                    "task": "High-yield summary sheets review for tomorrow's NLP final exam",
                    "duration_minutes": 30,
                },
            ],
        },
        {
            "date": "2026-12-14",  # NLP Exam Day
            "sessions": [
                {
                    "subject": "Natural Language Processing",
                    "activity": "Revision",
                    "task": "Exam Morning: Final glance at evaluation formulas and transformer layers",
                    "duration_minutes": 45,
                },
            ],
        },
    ]
}

FIXTURE_VALID_RESPONSE_JSON = json.dumps(FIXTURE_VALID_PLAN_DICT, indent=2)

# 2. Invalid Fixture: Budget Overrun
FIXTURE_INVALID_BUDGET_OVERRUN_DICT = {
    "schedule": [
        {
            "date": "2026-12-01",
            "sessions": [
                {
                    "subject": "Data Structures & Algorithms",
                    "activity": "Theory",
                    "task": "Reading DP theory",
                    "duration_minutes": 150,
                },
                {
                    "subject": "Data Structures & Algorithms",
                    "activity": "Practice",
                    "task": "Practicing DP problems",
                    "duration_minutes": 120,  # Total = 270 min, exceeds 180 min budget!
                },
            ],
        }
    ]
}
FIXTURE_INVALID_BUDGET_OVERRUN_JSON = json.dumps(FIXTURE_INVALID_BUDGET_OVERRUN_DICT, indent=2)

# 3. Invalid Fixture: Post-Exam Scheduling
FIXTURE_INVALID_POST_EXAM_DICT = {
    "schedule": [
        {
            "date": "2026-12-07",  # DSA Exam was on 2026-12-05!
            "sessions": [
                {
                    "subject": "Data Structures & Algorithms",
                    "activity": "Practice",
                    "task": "Studying Graph algorithms after exam has ended",
                    "duration_minutes": 60,
                }
            ],
        }
    ]
}
FIXTURE_INVALID_POST_EXAM_JSON = json.dumps(FIXTURE_INVALID_POST_EXAM_DICT, indent=2)

# 4. Invalid Fixture: Session on 0-Minute Rest Day
FIXTURE_INVALID_REST_DAY_DICT = {
    "schedule": [
        {
            "date": "2026-12-06",  # 2026-12-06 is configured as 0 minutes (rest day)
            "sessions": [
                {
                    "subject": "Database Management Systems",
                    "activity": "Revision",
                    "task": "Studying on a rest day",
                    "duration_minutes": 60,
                }
            ],
        }
    ]
}
FIXTURE_INVALID_REST_DAY_JSON = json.dumps(FIXTURE_INVALID_REST_DAY_DICT, indent=2)

# 5. Invalid Fixture: Unknown Subject & Non-positive Duration
FIXTURE_INVALID_UNKNOWN_SUBJECT_DICT = {
    "schedule": [
        {
            "date": "2026-12-01",
            "sessions": [
                {
                    "subject": "Quantum Computing",  # Not in declared subjects!
                    "activity": "Theory",
                    "task": "Qubits and superposition",
                    "duration_minutes": -30,  # Negative duration!
                }
            ],
        }
    ]
}
FIXTURE_INVALID_UNKNOWN_SUBJECT_JSON = json.dumps(FIXTURE_INVALID_UNKNOWN_SUBJECT_DICT, indent=2)
