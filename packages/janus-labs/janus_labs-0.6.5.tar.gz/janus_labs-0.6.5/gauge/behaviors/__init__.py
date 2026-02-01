"""Sample behavior specifications for Janus Labs."""

from .code_quality import CodeQualityBehavior
from .instruction_adherence import InstructionAdherenceBehavior
from .test_cheating import TEST_CHEATING_BEHAVIOR

__all__ = [
    "CodeQualityBehavior",
    "InstructionAdherenceBehavior",
    "TEST_CHEATING_BEHAVIOR",
]
