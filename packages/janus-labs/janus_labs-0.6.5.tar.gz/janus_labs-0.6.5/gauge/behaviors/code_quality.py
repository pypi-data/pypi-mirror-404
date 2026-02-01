"""BHV-003: Code Quality (O-3.01) metric implementation."""

from deepeval.metrics import GEval
from deepeval.test_case import LLMTestCase, LLMTestCaseParams


def _scale_score(raw_score: float) -> float:
    if raw_score <= 1.0:
        scaled = raw_score * 100.0
    elif raw_score <= 10.0:
        scaled = raw_score * 10.0
    else:
        scaled = raw_score
    return max(0.0, min(100.0, scaled))


class CodeQualityBehavior:
    """BHV-003: Code Quality (O-3.01).

    Anchored to: DeepEval GEval + SWE-bench evaluation criteria
    Measures: Is the code correct, minimal, idiomatic, and testable?
    """

    code = "O-3.01"
    name = "Code Quality"

    CRITERIA = """
    Evaluate the code output against these SWE-bench-inspired criteria:

    1. **Correctness** (0-25): Does the code address the stated requirement?
       - Fully addresses requirement: 25
       - Partially addresses: 10-20
       - Does not address: 0-10

    2. **Minimality** (0-25): Is the change focused without unnecessary additions?
       - Minimal, focused change: 25
       - Some unnecessary additions: 10-20
       - Significant scope creep: 0-10

    3. **Idiomacy** (0-25): Does the code follow language conventions?
       - Fully idiomatic: 25
       - Minor style issues: 10-20
       - Non-idiomatic patterns: 0-10

    4. **Testability** (0-25): Could this code be reasonably tested?
       - Easily testable, clear interfaces: 25
       - Testable with some effort: 10-20
       - Difficult to test: 0-10

    Sum all four scores for total 0-100.
    """

    def __init__(self, model: str = "gpt-4o"):
        self.model = model
        self.metric = GEval(
            name="CodeQuality",
            criteria=self.CRITERIA,
            evaluation_params=[
                LLMTestCaseParams.INPUT,
                LLMTestCaseParams.ACTUAL_OUTPUT,
            ],
            model=model,
        )

    def evaluate(self, instruction: str, code_output: str) -> float:
        """Return score on 0-100 scale."""
        test_case = LLMTestCase(input=instruction, actual_output=code_output)
        score = self.metric.measure(test_case)
        if score is None:
            score = self.metric.score
        if score is None:
            return 0.0
        return _scale_score(score)
