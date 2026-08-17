"""Deterministic task-aware Project Intelligence orchestration."""

from .contracts import (
    ContextScope,
    IntelligenceLevel,
    IntelligencePlan,
    IntentUncertainty,
    PlanOutcome,
    TaskIntent,
    TaskIntentName,
    TaskSignals,
)
from .service import (
    MAX_OBJECTIVE_CHARS,
    MAX_SIGNAL_PATHS,
    build_intelligence_plan,
    classify_task,
    create_shadow_plan,
    project_task_signals,
)

__all__ = [
    "MAX_OBJECTIVE_CHARS",
    "MAX_SIGNAL_PATHS",
    "ContextScope",
    "IntelligenceLevel",
    "IntelligencePlan",
    "IntentUncertainty",
    "PlanOutcome",
    "TaskIntent",
    "TaskIntentName",
    "TaskSignals",
    "build_intelligence_plan",
    "classify_task",
    "create_shadow_plan",
    "project_task_signals",
]
