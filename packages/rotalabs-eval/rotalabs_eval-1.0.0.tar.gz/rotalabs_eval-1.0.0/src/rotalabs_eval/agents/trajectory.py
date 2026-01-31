"""Multi-turn trajectory evaluation for agent conversations."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from rotalabs_eval.metrics.base import Metric, MetricResult, register_metric


class TurnRole(Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class ActionType(Enum):
    RESPONSE = "response"
    TOOL_CALL = "tool_call"
    THINK = "think"
    DELEGATE = "delegate"
    TERMINATE = "terminate"


@dataclass
class Action:
    """An action taken by the agent."""
    action_type: ActionType
    content: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Observation:
    """Result of an action."""
    content: str
    success: bool = True
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Turn:
    """Single turn in a conversation."""
    role: TurnRole
    content: str
    action: Optional[Action] = None
    observation: Optional[Observation] = None
    turn_index: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Trajectory:
    """A complete agent trajectory."""
    trajectory_id: str
    turns: List[Turn]
    initial_goal: str
    final_state: Optional[str] = None
    goal_achieved: Optional[bool] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def num_turns(self) -> int:
        return len(self.turns)

    @property
    def num_assistant_turns(self) -> int:
        return sum(1 for t in self.turns if t.role == TurnRole.ASSISTANT)

    @property
    def num_tool_calls(self) -> int:
        return sum(
            1 for t in self.turns if t.action and t.action.action_type == ActionType.TOOL_CALL
        )

    @property
    def actions(self) -> List[Action]:
        return [t.action for t in self.turns if t.action is not None]

    @property
    def tool_calls(self) -> List[Action]:
        return [a for a in self.actions if a.action_type == ActionType.TOOL_CALL]

    def get_turn(self, index: int) -> Optional[Turn]:
        if 0 <= index < len(self.turns):
            return self.turns[index]
        return None


@dataclass
class TrajectoryPair:
    """A trajectory with optional reference trajectory."""
    predicted: Trajectory
    reference: Optional[Trajectory] = None
    reference_goal_achieved: Optional[bool] = None


class TrajectoryMetric(ABC):
    """Base class for trajectory evaluation metrics."""
    name: str = "trajectory_metric"

    def __init__(self, **kwargs: Any) -> None:
        self.config = kwargs

    @abstractmethod
    def compute(self, trajectories: List[TrajectoryPair]) -> MetricResult:
        ...


@register_metric
class GoalCompletionMetric(TrajectoryMetric, Metric):
    """Measures whether the agent achieved its goal."""
    name = "goal_completion"

    def compute(
        self,
        predictions: Union[List[str], List[TrajectoryPair]],
        references: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> MetricResult:
        if not predictions:
            return MetricResult(name=self.name, value=0.0)

        if isinstance(predictions[0], TrajectoryPair):
            scores = []
            for pair in predictions:
                if pair.predicted.goal_achieved is not None:
                    scores.append(1.0 if pair.predicted.goal_achieved else 0.0)
                else:
                    scores.append(0.0)
        else:
            scores = []
            for pred in predictions:
                pred_lower = str(pred).lower().strip()
                if pred_lower in ("true", "yes", "1", "achieved", "success"):
                    scores.append(1.0)
                else:
                    scores.append(0.0)

        return MetricResult(
            name=self.name,
            value=sum(scores) / len(scores) if scores else 0.0,
            per_example_scores=scores,
        )


@register_metric
class TrajectoryEfficiencyMetric(TrajectoryMetric, Metric):
    """Measures trajectory efficiency."""
    name = "trajectory_efficiency"

    def __init__(self, max_turns: int = 20, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.max_turns = max_turns

    def compute(
        self,
        predictions: Union[List[str], List[TrajectoryPair]],
        references: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> MetricResult:
        if not predictions:
            return MetricResult(name=self.name, value=0.0)

        scores: List[float] = []
        if isinstance(predictions[0], TrajectoryPair):
            for pair in predictions:
                pred_turns = pair.predicted.num_turns
                if pair.reference:
                    ref_turns = pair.reference.num_turns
                    efficiency = ref_turns / pred_turns if pred_turns > 0 else 0.0
                else:
                    efficiency = max(0.0, min(1.0, (self.max_turns - pred_turns) / self.max_turns))
                scores.append(efficiency)
        else:
            refs = references or [str(self.max_turns)] * len(predictions)
            for pred, ref in zip(predictions, refs):
                pred_turns = int(pred) if pred else self.max_turns
                ref_turns = int(ref) if ref else self.max_turns
                scores.append(ref_turns / pred_turns if pred_turns > 0 else 0.0)

        return MetricResult(
            name=self.name,
            value=sum(scores) / len(scores) if scores else 0.0,
            per_example_scores=scores,
        )


@register_metric
class ToolCallAccuracyMetric(TrajectoryMetric, Metric):
    """Measures accuracy of tool calls in trajectories."""
    name = "tool_call_accuracy"

    def __init__(self, check_params: bool = False, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.check_params = check_params

    def compute(
        self,
        predictions: Union[List[str], List[TrajectoryPair]],
        references: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> MetricResult:
        if not predictions:
            return MetricResult(name=self.name, value=0.0)

        scores: List[float] = []
        if isinstance(predictions[0], TrajectoryPair):
            for pair in predictions:
                if not pair.reference:
                    continue
                pred_tools = pair.predicted.tool_calls
                ref_tools = pair.reference.tool_calls
                if not ref_tools:
                    scores.append(1.0 if not pred_tools else 0.0)
                    continue
                matches = 0
                for i, ref_tool in enumerate(ref_tools):
                    if i < len(pred_tools):
                        pred_tool = pred_tools[i]
                        if pred_tool.content == ref_tool.content:
                            if not self.check_params or pred_tool.parameters == ref_tool.parameters:
                                matches += 1
                scores.append(matches / len(ref_tools))
        else:
            refs = references or [""] * len(predictions)
            for pred, ref in zip(predictions, refs):
                pred_tools = [t.strip() for t in str(pred).split(",") if t.strip()]
                ref_tools = [t.strip() for t in str(ref).split(",") if t.strip()]
                if not ref_tools:
                    scores.append(1.0 if not pred_tools else 0.0)
                    continue
                matches = sum(1 for p, r in zip(pred_tools, ref_tools) if p == r)
                scores.append(matches / len(ref_tools))

        return MetricResult(
            name=self.name,
            value=sum(scores) / len(scores) if scores else 0.0,
            per_example_scores=scores,
        )


@register_metric
class ActionSequenceF1Metric(TrajectoryMetric, Metric):
    """Computes F1 score for action sequences."""
    name = "action_sequence_f1"

    def compute(
        self,
        predictions: Union[List[str], List[TrajectoryPair]],
        references: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> MetricResult:
        if not predictions:
            return MetricResult(name=self.name, value=0.0)

        scores: List[float] = []
        if isinstance(predictions[0], TrajectoryPair):
            for pair in predictions:
                if not pair.reference:
                    continue
                pred_actions = set(
                    f"{a.action_type.value}:{a.content}" for a in pair.predicted.actions
                )
                ref_actions = set(
                    f"{a.action_type.value}:{a.content}" for a in pair.reference.actions
                )
                scores.append(self._compute_f1(pred_actions, ref_actions))
        else:
            refs = references or [""] * len(predictions)
            for pred, ref in zip(predictions, refs):
                pred_actions = set(t.strip() for t in str(pred).split(",") if t.strip())
                ref_actions = set(t.strip() for t in str(ref).split(",") if t.strip())
                scores.append(self._compute_f1(pred_actions, ref_actions))

        return MetricResult(
            name=self.name,
            value=sum(scores) / len(scores) if scores else 0.0,
            per_example_scores=scores,
            metadata={"metric_type": "f1"},
        )

    def _compute_f1(self, pred: set, ref: set) -> float:
        if not pred and not ref:
            return 1.0
        if not pred or not ref:
            return 0.0
        tp = len(pred & ref)
        precision = tp / len(pred)
        recall = tp / len(ref)
        if precision + recall == 0:
            return 0.0
        return 2 * precision * recall / (precision + recall)


def parse_trajectory_from_messages(
    messages: List[Dict[str, Any]],
    trajectory_id: str = "unknown",
) -> Trajectory:
    """Parse a trajectory from chat messages."""
    turns: List[Turn] = []
    initial_goal = ""

    for i, msg in enumerate(messages):
        role_str = msg.get("role", "user").lower()
        content = msg.get("content", "")

        role_map = {
            "user": TurnRole.USER,
            "assistant": TurnRole.ASSISTANT,
            "system": TurnRole.SYSTEM,
            "tool": TurnRole.TOOL,
            "function": TurnRole.TOOL,
        }
        role = role_map.get(role_str, TurnRole.USER)

        if role == TurnRole.USER and not initial_goal:
            initial_goal = content

        action: Optional[Action] = None
        if role == TurnRole.ASSISTANT:
            tool_calls = msg.get("tool_calls", [])
            if tool_calls:
                tc = tool_calls[0]
                action = Action(
                    action_type=ActionType.TOOL_CALL,
                    content=tc.get("function", {}).get("name", ""),
                    parameters=tc.get("function", {}).get("arguments", {}),
                )
            else:
                action = Action(action_type=ActionType.RESPONSE, content=content)

        observation: Optional[Observation] = None
        if role == TurnRole.TOOL:
            observation = Observation(
                content=content,
                success="error" not in content.lower(),
            )

        turns.append(Turn(
            role=role, content=content, action=action,
            observation=observation, turn_index=i,
            metadata=msg.get("metadata", {}),
        ))

    return Trajectory(
        trajectory_id=trajectory_id, turns=turns, initial_goal=initial_goal,
    )
