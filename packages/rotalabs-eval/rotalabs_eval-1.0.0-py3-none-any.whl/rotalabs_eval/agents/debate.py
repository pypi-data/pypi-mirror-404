"""Multi-agent debate evaluation metrics."""
from __future__ import annotations

import json
import logging
import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from rotalabs_eval.metrics.base import Metric, MetricResult, register_metric

logger = logging.getLogger(__name__)


class ArgumentType(Enum):
    CLAIM = "claim"
    SUPPORT = "support"
    COUNTER = "counter"
    CONCESSION = "concession"
    SYNTHESIS = "synthesis"
    CLARIFICATION = "clarification"


class DebateRole(Enum):
    PROPONENT = "proponent"
    OPPONENT = "opponent"
    MEDIATOR = "mediator"
    JUDGE = "judge"


@dataclass
class Argument:
    """A single argument in a debate."""
    agent_id: str
    role: DebateRole
    argument_type: ArgumentType
    content: str
    references: List[int] = field(default_factory=list)
    strength: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DebateRound:
    round_number: int
    arguments: List[Argument]
    topic: str = ""


@dataclass
class DebateSession:
    """Complete debate session between agents."""
    session_id: str
    topic: str
    agents: List[str]
    rounds: List[DebateRound]
    final_verdict: Optional[str] = None
    winner_agent_id: Optional[str] = None
    consensus_reached: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def num_rounds(self) -> int:
        return len(self.rounds)

    @property
    def all_arguments(self) -> List[Argument]:
        return [arg for round_ in self.rounds for arg in round_.arguments]

    @property
    def num_arguments(self) -> int:
        return sum(len(r.arguments) for r in self.rounds)

    def arguments_by_agent(self, agent_id: str) -> List[Argument]:
        return [a for a in self.all_arguments if a.agent_id == agent_id]

    def argument_type_counts(self) -> Dict[ArgumentType, int]:
        counts: Dict[ArgumentType, int] = {}
        for arg in self.all_arguments:
            counts[arg.argument_type] = counts.get(arg.argument_type, 0) + 1
        return counts


@register_metric
class ConsensusReachedMetric(Metric):
    name = "consensus_reached"

    def compute(self, predictions: List[str], references: List[str], **kwargs: Any) -> MetricResult:
        self.validate_inputs(predictions, references)
        scores: List[float] = []
        for pred, ref in zip(predictions, references):
            pred_c = pred.lower().strip() in ("consensus", "yes", "true", "1")
            ref_c = ref.lower().strip() in ("consensus", "yes", "true", "1")
            scores.append(1.0 if pred_c == ref_c else 0.0)
        return MetricResult(name=self.name, value=sum(scores) / len(scores) if scores else 0.0, per_example_scores=scores)


@register_metric
class ArgumentDiversityMetric(Metric):
    name = "argument_diversity"

    def compute(self, predictions: List[str], references: List[str], **kwargs: Any) -> MetricResult:
        self.validate_inputs(predictions, references)
        scores: List[float] = []
        for pred, ref in zip(predictions, references):
            pred_types = {t.strip().lower() for t in pred.split(",") if t.strip()}
            ref_types = {t.strip().lower() for t in ref.split(",") if t.strip()}
            if not ref_types:
                ref_types = {t.value for t in ArgumentType}
            scores.append(min(1.0, len(pred_types) / len(ref_types) if ref_types else 0.0))
        return MetricResult(name=self.name, value=sum(scores) / len(scores) if scores else 0.0, per_example_scores=scores)


@register_metric
class ContributionBalanceMetric(Metric):
    name = "contribution_balance"

    def compute(self, predictions: List[str], references: List[str], **kwargs: Any) -> MetricResult:
        self.validate_inputs(predictions, references)
        scores: List[float] = []
        for pred, ref in zip(predictions, references):
            try:
                counts = [int(c.strip()) for c in pred.split(",") if c.strip()]
                num_agents = int(ref) if ref else len(counts)
            except ValueError:
                scores.append(0.0)
                continue
            if not counts or sum(counts) == 0:
                scores.append(0.0)
                continue
            total = sum(counts)
            probs = [c / total for c in counts]
            entropy = -sum(p * math.log2(p) for p in probs if p > 0)
            max_entropy = math.log2(num_agents) if num_agents > 1 else 1
            scores.append(entropy / max_entropy if max_entropy > 0 else 1.0)
        return MetricResult(name=self.name, value=sum(scores) / len(scores) if scores else 0.0, per_example_scores=scores)


@register_metric
class DebateProgressionMetric(Metric):
    name = "debate_progression"

    def compute(self, predictions: List[str], references: List[str], **kwargs: Any) -> MetricResult:
        self.validate_inputs(predictions, references)
        scores: List[float] = []
        for pred, ref in zip(predictions, references):
            pred_seq = [t.strip().lower() for t in pred.split(",") if t.strip()]
            if not pred_seq:
                scores.append(0.0)
                continue
            scores.append(self._score_progression(pred_seq))
        return MetricResult(name=self.name, value=sum(scores) / len(scores) if scores else 0.0, per_example_scores=scores)

    def _score_progression(self, sequence: List[str]) -> float:
        valid_transitions = {
            "claim": {"support", "counter", "clarification"},
            "support": {"counter", "concession", "synthesis", "claim"},
            "counter": {"support", "concession", "synthesis", "counter"},
            "concession": {"synthesis", "claim", "support"},
            "synthesis": {"claim", "concession"},
            "clarification": {"support", "counter", "claim"},
        }
        if len(sequence) < 2:
            return 1.0 if sequence else 0.0
        valid_count = 0
        for i in range(len(sequence) - 1):
            if sequence[i + 1] in valid_transitions.get(sequence[i], set()):
                valid_count += 1
        return valid_count / (len(sequence) - 1)


@register_metric
class DebateOutcomeAccuracyMetric(Metric):
    name = "debate_outcome_accuracy"

    def compute(self, predictions: List[str], references: List[str], **kwargs: Any) -> MetricResult:
        self.validate_inputs(predictions, references)
        scores: List[float] = []
        for pred, ref in zip(predictions, references):
            p = pred.lower().strip() if pred else ""
            r = ref.lower().strip() if ref else ""
            if p == r:
                scores.append(1.0)
            elif self._is_partial_match(p, r):
                scores.append(0.5)
            else:
                scores.append(0.0)
        return MetricResult(name=self.name, value=sum(scores) / len(scores) if scores else 0.0, per_example_scores=scores)

    def _is_partial_match(self, pred: str, ref: str) -> bool:
        pos = {"win", "correct", "true", "yes", "agree"}
        neg = {"lose", "incorrect", "false", "no", "disagree"}
        pp = any(i in pred for i in pos)
        pn = any(i in pred for i in neg)
        rp = any(i in ref for i in pos)
        rn = any(i in ref for i in neg)
        return (pp and rp) or (pn and rn)


@register_metric
class ArgumentQualityMetric(Metric):
    name = "argument_quality"

    def __init__(
        self,
        relevance_weight: float = 0.3,
        coherence_weight: float = 0.3,
        evidence_weight: float = 0.2,
        response_weight: float = 0.2,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.weights = {
            "relevance": relevance_weight,
            "coherence": coherence_weight,
            "evidence": evidence_weight,
            "response": response_weight,
        }

    def compute(self, predictions: List[str], references: List[str], **kwargs: Any) -> MetricResult:
        self.validate_inputs(predictions, references)
        scores: List[float] = []
        component_scores: Dict[str, List[float]] = {k: [] for k in self.weights}
        for pred, ref in zip(predictions, references):
            try:
                if pred.startswith("{"):
                    pred_scores = json.loads(pred)
                else:
                    parts = [float(p.strip()) for p in pred.split(",")]
                    pred_scores = dict(zip(self.weights.keys(), parts))
                total = 0.0
                for comp, weight in self.weights.items():
                    cs = pred_scores.get(comp, 0.0)
                    total += weight * cs
                    component_scores[comp].append(cs)
                scores.append(min(1.0, max(0.0, total)))
            except (json.JSONDecodeError, ValueError):
                scores.append(0.0)
                for comp in component_scores:
                    component_scores[comp].append(0.0)
        avg_comp = {k: sum(v) / len(v) if v else 0.0 for k, v in component_scores.items()}
        return MetricResult(
            name=self.name,
            value=sum(scores) / len(scores) if scores else 0.0,
            per_example_scores=scores,
            metadata={"component_scores": avg_comp},
        )


def parse_debate_from_messages(
    messages: List[Dict[str, Any]],
    session_id: str = "unknown",
    topic: str = "",
) -> DebateSession:
    """Parse a debate session from messages."""
    agents: Set[str] = set()
    rounds: List[DebateRound] = []
    current_round_args: List[Argument] = []
    round_num = 0

    for msg in messages:
        agent_id = msg.get("agent_id", msg.get("name", "unknown"))
        agents.add(agent_id)
        role_str = msg.get("debate_role", "proponent").lower()
        role_map = {"proponent": DebateRole.PROPONENT, "opponent": DebateRole.OPPONENT,
                     "mediator": DebateRole.MEDIATOR, "judge": DebateRole.JUDGE}
        role = role_map.get(role_str, DebateRole.PROPONENT)
        arg_type_str = msg.get("argument_type", "claim").lower()
        arg_type_map = {"claim": ArgumentType.CLAIM, "support": ArgumentType.SUPPORT,
                         "counter": ArgumentType.COUNTER, "concession": ArgumentType.CONCESSION,
                         "synthesis": ArgumentType.SYNTHESIS, "clarification": ArgumentType.CLARIFICATION}
        arg_type = arg_type_map.get(arg_type_str, ArgumentType.CLAIM)
        content = msg.get("content", "")
        refs = msg.get("references", [])
        arg = Argument(agent_id=agent_id, role=role, argument_type=arg_type,
                       content=content, references=refs, metadata=msg.get("metadata", {}))
        current_round_args.append(arg)
        if msg.get("end_round", False) or (arg_type == ArgumentType.SYNTHESIS and len(current_round_args) >= 2):
            rounds.append(DebateRound(round_number=round_num, arguments=current_round_args, topic=topic))
            current_round_args = []
            round_num += 1
    if current_round_args:
        rounds.append(DebateRound(round_number=round_num, arguments=current_round_args, topic=topic))

    return DebateSession(session_id=session_id, topic=topic, agents=list(agents), rounds=rounds)
