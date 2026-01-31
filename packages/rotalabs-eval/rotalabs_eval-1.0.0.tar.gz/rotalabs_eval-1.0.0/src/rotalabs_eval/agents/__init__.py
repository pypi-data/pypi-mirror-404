"""Agent and multi-turn evaluation support."""
from __future__ import annotations

from rotalabs_eval.agents.trajectory import (
    Action,
    ActionSequenceF1Metric,
    ActionType,
    GoalCompletionMetric,
    Observation,
    ToolCallAccuracyMetric,
    Trajectory,
    TrajectoryEfficiencyMetric,
    TrajectoryMetric,
    TrajectoryPair,
    Turn,
    TurnRole,
    parse_trajectory_from_messages,
)
from rotalabs_eval.agents.tool_use import (
    ToolCall,
    ToolCallEfficiencyMetric,
    ToolCallPrecisionRecallMetric,
    ToolCallSequence,
    ToolErrorRecoveryMetric,
    ToolOrderAccuracyMetric,
    ToolParameterAccuracyMetric,
    ToolSelectionAccuracyMetric,
    parse_tool_calls_from_messages,
)
from rotalabs_eval.agents.debate import (
    Argument,
    ArgumentDiversityMetric,
    ArgumentQualityMetric,
    ArgumentType,
    ConsensusReachedMetric,
    ContributionBalanceMetric,
    DebateOutcomeAccuracyMetric,
    DebateProgressionMetric,
    DebateRole,
    DebateRound,
    DebateSession,
    parse_debate_from_messages,
)

__all__ = [
    "TurnRole", "ActionType", "Action", "Observation", "Turn",
    "Trajectory", "TrajectoryPair", "TrajectoryMetric",
    "GoalCompletionMetric", "TrajectoryEfficiencyMetric",
    "ToolCallAccuracyMetric", "ActionSequenceF1Metric",
    "parse_trajectory_from_messages",
    "ToolCall", "ToolCallSequence",
    "ToolSelectionAccuracyMetric", "ToolOrderAccuracyMetric",
    "ToolParameterAccuracyMetric", "ToolCallEfficiencyMetric",
    "ToolErrorRecoveryMetric", "ToolCallPrecisionRecallMetric",
    "parse_tool_calls_from_messages",
    "ArgumentType", "DebateRole", "Argument", "DebateRound", "DebateSession",
    "ConsensusReachedMetric", "ArgumentDiversityMetric",
    "ContributionBalanceMetric", "DebateProgressionMetric",
    "DebateOutcomeAccuracyMetric", "ArgumentQualityMetric",
    "parse_debate_from_messages",
]
