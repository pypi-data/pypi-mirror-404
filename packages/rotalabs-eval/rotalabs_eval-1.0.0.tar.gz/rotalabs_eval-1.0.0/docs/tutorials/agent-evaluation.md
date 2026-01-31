# Agent Evaluation

This tutorial demonstrates how to evaluate agentic AI systems using the trajectory, tool use, and debate modules in `rotalabs-eval`.

---

## 1. Trajectory Evaluation

### Create a Trajectory

Build a multi-turn conversation using `Turn`, `Action`, `Observation`, and `Trajectory`:

```python
from rotalabs_eval.agents.trajectory import (
    Trajectory,
    TrajectoryPair,
    Turn,
    TurnRole,
    Action,
    ActionType,
    Observation,
)

# Build turns for an agent that searches and answers a question
turns = [
    Turn(
        role=TurnRole.USER,
        content="What is the population of Tokyo?",
        turn_index=0,
    ),
    Turn(
        role=TurnRole.ASSISTANT,
        content="search_web",
        action=Action(
            action_type=ActionType.TOOL_CALL,
            content="search_web",
            parameters={"query": "population of Tokyo"},
        ),
        turn_index=1,
    ),
    Turn(
        role=TurnRole.TOOL,
        content="Tokyo has a population of approximately 14 million.",
        observation=Observation(
            content="Tokyo has a population of approximately 14 million.",
            success=True,
        ),
        turn_index=2,
    ),
    Turn(
        role=TurnRole.ASSISTANT,
        content="The population of Tokyo is approximately 14 million.",
        action=Action(
            action_type=ActionType.RESPONSE,
            content="The population of Tokyo is approximately 14 million.",
        ),
        turn_index=3,
    ),
]

trajectory = Trajectory(
    trajectory_id="traj_001",
    turns=turns,
    initial_goal="What is the population of Tokyo?",
    goal_achieved=True,
)

print(f"Total turns: {trajectory.num_turns}")           # 4
print(f"Assistant turns: {trajectory.num_assistant_turns}")  # 2
print(f"Tool calls: {trajectory.num_tool_calls}")        # 1
```

### Run GoalCompletionMetric

`GoalCompletionMetric` can operate in two modes. In string mode, it checks whether predictions contain success indicators like "success", "yes", "true", or "achieved":

```python
from rotalabs_eval.agents.trajectory import GoalCompletionMetric

goal_metric = GoalCompletionMetric()

# String mode: predictions are goal completion labels
result = goal_metric.compute(
    predictions=["success", "failure", "yes", "no", "achieved"],
    references=["", "", "", "", ""],  # References not used in string mode
)
print(f"{result.name}: {result.value:.2f}")
# goal_completion: 0.60
print(result.per_example_scores)
# [1.0, 0.0, 1.0, 0.0, 1.0]
```

It can also accept `TrajectoryPair` objects directly, reading the `goal_achieved` flag from the trajectory.

---

## 2. Tool Use Evaluation

### Create ToolCall and ToolCallSequence

```python
from rotalabs_eval.agents.tool_use import ToolCall, ToolCallSequence

# Define the tool calls an agent made
predicted_calls = ToolCallSequence(
    calls=[
        ToolCall(name="search_web", parameters={"query": "Tokyo population"}),
        ToolCall(name="calculator", parameters={"expression": "14000000 / 1000"}),
    ],
    task_description="Find and convert Tokyo's population to thousands",
)

print(f"Tool names: {predicted_calls.tool_names}")
# Tool names: ['search_web', 'calculator']
print(f"Unique tools: {predicted_calls.unique_tools}")
# Unique tools: {'search_web', 'calculator'}
print(f"Total calls: {predicted_calls.num_calls}")
# Total calls: 2
print(f"Failures: {predicted_calls.num_failures}")
# Failures: 0
```

### Run ToolSelectionAccuracyMetric

This metric takes comma-separated tool names as strings and computes Jaccard similarity:

```python
from rotalabs_eval.agents.tool_use import ToolSelectionAccuracyMetric

tool_metric = ToolSelectionAccuracyMetric()

result = tool_metric.compute(
    predictions=[
        "search_web, calculator",
        "search_web, translator",
        "search_web",
    ],
    references=[
        "search_web, calculator",
        "search_web, summarizer",
        "search_web, calculator",
    ],
)
print(f"{result.name}: {result.value:.4f}")
# tool_selection_accuracy: 0.5556
print(result.per_example_scores)
# [1.0, 0.3333333333333333, 0.3333333333333333]
```

Scoring per example:

- Example 0: `{search_web, calculator}` matches exactly --> Jaccard = 1.0
- Example 1: intersection `{search_web}`, union `{search_web, translator, summarizer}` --> 1/3
- Example 2: intersection `{search_web}`, union `{search_web, calculator}` --> 1/2 (but both are lowercased and compared as sets)

### Other Tool Metrics

Additional tool use metrics work the same way with string inputs:

```python
from rotalabs_eval.agents.tool_use import (
    ToolOrderAccuracyMetric,
    ToolCallEfficiencyMetric,
    ToolCallPrecisionRecallMetric,
)

# Tool order accuracy (LCS-based)
order_metric = ToolOrderAccuracyMetric()
result = order_metric.compute(
    predictions=["search_web, calculator, summarizer"],
    references=["search_web, summarizer, calculator"],
)
print(f"{result.name}: {result.value:.4f}")
# tool_order_accuracy: 0.6667

# Tool efficiency (optimal / actual call count)
eff_metric = ToolCallEfficiencyMetric()
result = eff_metric.compute(
    predictions=["5"],   # Agent used 5 calls
    references=["3"],    # Optimal was 3 calls
)
print(f"{result.name}: {result.value:.4f}")
# tool_efficiency: 0.6000

# Tool call F1 (precision, recall, F1)
f1_metric = ToolCallPrecisionRecallMetric()
result = f1_metric.compute(
    predictions=["search_web, calculator, translator"],
    references=["search_web, calculator, summarizer"],
)
print(f"{result.name}: {result.value:.4f}")
# tool_call_f1: 0.6667
print(f"Avg precision: {result.metadata['avg_precision']:.4f}")
print(f"Avg recall: {result.metadata['avg_recall']:.4f}")
```

---

## 3. Debate Evaluation

### Create a DebateSession

Build a multi-agent debate with `Argument`, `DebateRound`, and `DebateSession`:

```python
from rotalabs_eval.agents.debate import (
    Argument,
    ArgumentType,
    DebateRole,
    DebateRound,
    DebateSession,
)

# Round 1: Initial claims
round_1 = DebateRound(
    round_number=0,
    arguments=[
        Argument(
            agent_id="agent_a",
            role=DebateRole.PROPONENT,
            argument_type=ArgumentType.CLAIM,
            content="Renewable energy is more cost-effective than fossil fuels.",
        ),
        Argument(
            agent_id="agent_b",
            role=DebateRole.OPPONENT,
            argument_type=ArgumentType.COUNTER,
            content="Fossil fuels have lower upfront infrastructure costs.",
        ),
    ],
    topic="Energy policy",
)

# Round 2: Supporting evidence and synthesis
round_2 = DebateRound(
    round_number=1,
    arguments=[
        Argument(
            agent_id="agent_a",
            role=DebateRole.PROPONENT,
            argument_type=ArgumentType.SUPPORT,
            content="Solar panel costs have dropped 90% in the last decade.",
        ),
        Argument(
            agent_id="agent_b",
            role=DebateRole.OPPONENT,
            argument_type=ArgumentType.CONCESSION,
            content="Long-term costs do favor renewables in many regions.",
        ),
        Argument(
            agent_id="agent_c",
            role=DebateRole.MEDIATOR,
            argument_type=ArgumentType.SYNTHESIS,
            content="A transitional approach balancing both is most practical.",
        ),
    ],
    topic="Energy policy",
)

session = DebateSession(
    session_id="debate_001",
    topic="Energy policy",
    agents=["agent_a", "agent_b", "agent_c"],
    rounds=[round_1, round_2],
    consensus_reached=True,
)

print(f"Rounds: {session.num_rounds}")          # 2
print(f"Total arguments: {session.num_arguments}")  # 5
print(f"Agent A arguments: {len(session.arguments_by_agent('agent_a'))}")  # 2
print(f"Argument types: {session.argument_type_counts()}")
# {ArgumentType.CLAIM: 1, ArgumentType.COUNTER: 1, ArgumentType.SUPPORT: 1,
#  ArgumentType.CONCESSION: 1, ArgumentType.SYNTHESIS: 1}
```

### Run ConsensusReachedMetric

This metric compares predicted and reference consensus labels. Values like "consensus", "yes", "true", and "1" are treated as positive:

```python
from rotalabs_eval.agents.debate import ConsensusReachedMetric

consensus_metric = ConsensusReachedMetric()

result = consensus_metric.compute(
    predictions=["consensus", "no", "yes"],
    references=["consensus", "no", "no"],
)
print(f"{result.name}: {result.value:.4f}")
# consensus_reached: 0.6667
print(result.per_example_scores)
# [1.0, 1.0, 0.0]
```

Scoring: example 0 both "consensus" (match), example 1 both "no" (match), example 2 "yes" vs "no" (mismatch).

### Other Debate Metrics

```python
from rotalabs_eval.agents.debate import (
    ArgumentDiversityMetric,
    ContributionBalanceMetric,
    DebateProgressionMetric,
)

# Argument diversity: fraction of argument types used vs. reference types
diversity_metric = ArgumentDiversityMetric()
result = diversity_metric.compute(
    predictions=["claim, support, counter, concession, synthesis"],
    references=["claim, support, counter, concession, synthesis, clarification"],
)
print(f"{result.name}: {result.value:.4f}")
# argument_diversity: 0.8333

# Contribution balance: entropy-normalized balance across agents
balance_metric = ContributionBalanceMetric()
result = balance_metric.compute(
    predictions=["3, 3, 2"],   # Argument counts per agent
    references=["3"],           # Number of agents
)
print(f"{result.name}: {result.value:.4f}")
# contribution_balance: 0.9810

# Debate progression: valid argument type transitions
progression_metric = DebateProgressionMetric()
result = progression_metric.compute(
    predictions=["claim, counter, support, synthesis"],
    references=[""],  # Not used
)
print(f"{result.name}: {result.value:.4f}")
# debate_progression: 1.0000
```

---

## Putting It All Together

Here is a complete example evaluating an agent across trajectory, tool use, and debate dimensions:

```python
from rotalabs_eval.metrics.registry import MetricRegistry

registry = MetricRegistry()

# Trajectory metrics
goal_result = registry.get("goal_completion").compute(
    predictions=["success", "success", "failure"],
    references=["", "", ""],
)

# Tool metrics
tool_result = registry.get("tool_selection_accuracy").compute(
    predictions=["search, calculate", "search, translate", "search"],
    references=["search, calculate", "search, summarize", "search, calculate"],
)

# Debate metrics
consensus_result = registry.get("consensus_reached").compute(
    predictions=["yes", "no", "yes"],
    references=["yes", "no", "no"],
)

print("Agent Evaluation Summary")
print("-" * 40)
print(f"  Goal completion:         {goal_result.value:.4f}")
print(f"  Tool selection accuracy: {tool_result.value:.4f}")
print(f"  Consensus reached:       {consensus_result.value:.4f}")
```
