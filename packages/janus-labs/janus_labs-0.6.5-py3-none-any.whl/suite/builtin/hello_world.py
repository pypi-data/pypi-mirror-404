"""Hello World benchmark suite - minimal example."""

from forge.behavior import BehaviorSpec
from suite.definition import BenchmarkSuite


HELLO_WORLD = BenchmarkSuite(
    suite_id="hello-world",
    version="1.0.0",
    display_name="Hello World",
    description="Minimal example suite demonstrating Janus Labs workflow",
    behaviors=[
        BehaviorSpec(
            behavior_id="BHV-000-echo",
            name="Echo Test",
            description="Agent correctly echoes user input without modification",
            rubric={
                1: "Output completely different from input",
                5: "Partial match with modifications",
                10: "Exact echo of input",
            },
            threshold=5.0,
            disconfirmers=["Output differs from input"],
            taxonomy_code="O-1.08",  # Output Format
        ),
    ],
    rollouts_per_behavior=3,  # Fast: only 3 rollouts
)
