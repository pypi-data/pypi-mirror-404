"""Exploration runner for Probe layer."""

from dataclasses import dataclass, field
from typing import Optional

from harness.artifacts import ArtifactCollector
from harness.executor import init_fixture
from harness.types import RunArtifactBundle
from probe.mutations import MutationStrategy, TaskMutation, apply_mutation
from probe.tracer import PhoenixTracer, TraceContext


@dataclass
class ExplorationConfig:
    """Configuration for exploration runs."""
    max_runs: int = 10
    strategies: list[MutationStrategy] = field(
        default_factory=lambda: [
            MutationStrategy.NONE,
            MutationStrategy.TASK_VARIATION,
            MutationStrategy.TOOL_REMOVAL,
        ]
    )
    available_tools: list[str] = field(
        default_factory=lambda: ["read_file", "write_file", "bash"]
    )
    seed: Optional[int] = 42
    timeout_ms: int = 60000
    fixture_path: Optional[str] = None


@dataclass
class ExplorationRun:
    """Result of a single exploration run."""
    run_id: str
    mutation: TaskMutation
    bundle: RunArtifactBundle
    trace_context: TraceContext
    success: bool
    error: Optional[str] = None


@dataclass
class ExplorationResult:
    """Complete exploration result."""
    config: ExplorationConfig
    runs: list[ExplorationRun]
    total_runs: int
    successful_runs: int
    failed_runs: int
    mutations_applied: dict[str, int]


class Explorer:
    """
    Executes exploration runs with mutations and tracing.

    The Explorer:
    1. Generates task mutations
    2. Initializes fixtures
    3. Simulates agent execution (or calls real agent)
    4. Collects traces via PhoenixTracer
    5. Aggregates results
    """

    def __init__(
        self,
        config: ExplorationConfig,
        tracer: Optional[PhoenixTracer] = None,
    ):
        """
        Initialize explorer.

        Args:
            config: Exploration configuration
            tracer: Optional PhoenixTracer (created if not provided)
        """
        self.config = config
        self.tracer = tracer or PhoenixTracer()
        self.runs: list[ExplorationRun] = []

    def _simulate_agent_execution(
        self,
        mutation: TaskMutation,
        collector: ArtifactCollector,
    ) -> None:
        """
        Simulate agent execution for a mutated task.

        In production, this would invoke the actual agent.
        For MVP, we simulate with mock tool calls.
        """
        collector.record_message("user", mutation.mutated_task)
        self.tracer.record_message("user", mutation.mutated_task)

        collector.record_message(
            "assistant",
            f"I'll work on: {mutation.mutated_task[:100]}..."
        )
        self.tracer.record_message(
            "assistant",
            f"Processing task with mutation: {mutation.strategy.value}"
        )

        if mutation.strategy == MutationStrategy.TOOL_REMOVAL:
            removed = mutation.mutation_details.get("removed_tool", "unknown")
            collector.record_tool_call(
                removed,
                {"action": "attempt"},
                {"error": "Tool unavailable"},
                0,
            )
            self.tracer.record_tool_call(
                removed,
                {"action": "attempt"},
                {"error": "Tool unavailable"},
                0,
            )
        else:
            collector.record_tool_call(
                "read_file",
                {"path": "main.py"},
                "def hello(): pass",
                50,
            )
            self.tracer.record_tool_call(
                "read_file",
                {"path": "main.py"},
                "def hello(): pass",
                50,
            )

    def run_single(
        self,
        task: str,
        strategy: MutationStrategy,
        run_index: int = 0,
    ) -> ExplorationRun:
        """
        Execute a single exploration run.

        Args:
            task: Original task description
            strategy: Mutation strategy to apply
            run_index: Index for seed calculation

        Returns:
            ExplorationRun with results
        """
        base_seed = self.config.seed
        seed = base_seed + run_index if base_seed is not None else None

        mutation = apply_mutation(
            task,
            strategy,
            available_tools=self.config.available_tools,
            seed=seed,
        )

        trace_ctx = self.tracer.start_trace(
            task_description=mutation.mutated_task,
            mutation=strategy.value,
        )

        if self.config.fixture_path:
            init_fixture(self.config.fixture_path)

        collector = ArtifactCollector()
        error = None
        success = True

        try:
            self._simulate_agent_execution(mutation, collector)
            exit_code = "success"
        except Exception as exc:
            error = str(exc)
            success = False
            exit_code = "crash"

        self.tracer.end_trace(exit_code)
        bundle = collector.finalize(exit_code)

        run = ExplorationRun(
            run_id=trace_ctx.run_id,
            mutation=mutation,
            bundle=bundle,
            trace_context=trace_ctx,
            success=success,
            error=error,
        )
        self.runs.append(run)
        return run

    def explore(self, task: str) -> ExplorationResult:
        """
        Run full exploration with all configured strategies.

        Args:
            task: Original task to explore

        Returns:
            ExplorationResult with all runs
        """
        self.runs = []
        mutations_count: dict[str, int] = {}

        run_index = 0
        for strategy in self.config.strategies:
            runs_per_strategy = max(
                1, self.config.max_runs // len(self.config.strategies)
            )

            for _ in range(runs_per_strategy):
                if run_index >= self.config.max_runs:
                    break

                self.run_single(task, strategy, run_index)
                run_index += 1

                strategy_name = strategy.value
                mutations_count[strategy_name] = mutations_count.get(strategy_name, 0) + 1

        successful = sum(1 for run in self.runs if run.success)

        return ExplorationResult(
            config=self.config,
            runs=self.runs,
            total_runs=len(self.runs),
            successful_runs=successful,
            failed_runs=len(self.runs) - successful,
            mutations_applied=mutations_count,
        )

    def get_traces(self) -> list[dict]:
        """Export collected traces."""
        return self.tracer.export_traces()
