"""BHV-002: Instruction Adherence (O-2.01) metric implementation."""

try:
    from deepeval.metrics import InstructionFollowingMetric
except ImportError as exc:  # pragma: no cover - handled at runtime
    InstructionFollowingMetric = None
    _IMPORT_ERROR = exc
from deepeval.test_case import LLMTestCase


def _scale_score(raw_score: float) -> float:
    if raw_score <= 1.0:
        scaled = raw_score * 100.0
    elif raw_score <= 10.0:
        scaled = raw_score * 10.0
    else:
        scaled = raw_score
    return max(0.0, min(100.0, scaled))


class InstructionAdherenceBehavior:
    """BHV-002: Instruction Adherence (O-2.01).

    Anchored to: DeepEval InstructionFollowingMetric
    Measures: Did the agent do what was asked?
    """

    code = "O-2.01"
    name = "Instruction Adherence"

    def __init__(self, threshold: float = 0.7, model: str = "gpt-4o"):
        self.threshold = threshold
        self.model = model
        if InstructionFollowingMetric is None:
            raise ImportError(
                "InstructionFollowingMetric is unavailable in the installed deepeval "
                "package. Upgrade deepeval to use BHV-002."
            ) from _IMPORT_ERROR
        self.metric = InstructionFollowingMetric(
            threshold=threshold,
            model=model,
        )

    def evaluate(self, instruction: str, output: str) -> float:
        """Return score on 0-100 scale."""
        test_case = LLMTestCase(input=instruction, actual_output=output)
        score = self.metric.measure(test_case)
        if score is None:
            score = self.metric.score
        if score is None:
            return 0.0
        return _scale_score(score)
