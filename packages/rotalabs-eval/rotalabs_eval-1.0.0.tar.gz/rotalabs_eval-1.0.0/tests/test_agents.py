"""Tests for agent evaluation metrics."""
from __future__ import annotations

import pytest

from rotalabs_eval.agents.trajectory import (
    Action,
    ActionType,
    GoalCompletionMetric,
    Observation,
    Trajectory,
    TrajectoryEfficiencyMetric,
    TrajectoryPair,
    Turn,
    TurnRole,
    parse_trajectory_from_messages,
)
from rotalabs_eval.agents.tool_use import (
    ToolCall,
    ToolCallSequence,
    ToolSelectionAccuracyMetric,
    parse_tool_calls_from_messages,
)
from rotalabs_eval.agents.debate import (
    ArgumentType,
    DebateRole,
    parse_debate_from_messages,
)


class TestGoalCompletion:
    def test_string_input(self):
        m = GoalCompletionMetric()
        r = m.compute(["true", "false", "yes"], ["", "", ""])
        assert r.value == pytest.approx(2 / 3)

    def test_trajectory_input(self):
        m = GoalCompletionMetric()
        pairs = [
            TrajectoryPair(predicted=Trajectory("1", [], "goal", goal_achieved=True)),
            TrajectoryPair(predicted=Trajectory("2", [], "goal", goal_achieved=False)),
        ]
        r = m.compute(pairs)
        assert r.value == 0.5


class TestTrajectoryEfficiency:
    def test_string_input(self):
        m = TrajectoryEfficiencyMetric(max_turns=10)
        r = m.compute(["5", "10"], ["10", "10"])
        assert r.per_example_scores[0] == 2.0  # ref/pred = 10/5
        assert r.per_example_scores[1] == 1.0


class TestToolSelection:
    def test_perfect(self):
        m = ToolSelectionAccuracyMetric()
        r = m.compute(["search,calculate"], ["search,calculate"])
        assert r.value == 1.0

    def test_partial(self):
        m = ToolSelectionAccuracyMetric()
        r = m.compute(["search"], ["search,calculate"])
        assert 0.0 < r.value < 1.0


class TestParseTrajectory:
    def test_basic(self):
        messages = [
            {"role": "user", "content": "Help me find a restaurant"},
            {"role": "assistant", "content": "I'll search for restaurants"},
            {"role": "user", "content": "In San Francisco"},
        ]
        traj = parse_trajectory_from_messages(messages, "test-1")
        assert traj.trajectory_id == "test-1"
        assert traj.initial_goal == "Help me find a restaurant"
        assert traj.num_turns == 3


class TestParseToolCalls:
    def test_basic(self):
        messages = [
            {"role": "user", "content": "What's the weather?"},
            {"role": "assistant", "content": "", "tool_calls": [
                {"function": {"name": "get_weather", "arguments": '{"city": "SF"}'}}
            ]},
            {"role": "tool", "content": "72°F, sunny"},
            {"role": "assistant", "content": "It's 72°F and sunny."},
        ]
        seq = parse_tool_calls_from_messages(messages)
        assert len(seq.calls) == 1
        assert seq.calls[0].name == "get_weather"
        assert seq.final_answer == "It's 72°F and sunny."


class TestParseDebate:
    def test_basic(self):
        messages = [
            {"agent_id": "agent1", "debate_role": "proponent", "argument_type": "claim", "content": "AI is beneficial"},
            {"agent_id": "agent2", "debate_role": "opponent", "argument_type": "counter", "content": "But risks exist"},
        ]
        session = parse_debate_from_messages(messages, "debate-1", "AI")
        assert session.num_arguments == 2
        assert len(session.agents) == 2
