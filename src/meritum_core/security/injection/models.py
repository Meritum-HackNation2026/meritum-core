"""What the injection detector reports and what the classifier answers.

Features:
    US-BEZ-01, F-19, ADR-12, ADR-23
"""

from enum import StrEnum
from typing import NamedTuple

from pydantic import BaseModel, ConfigDict, Field

from meritum_core.checks import InjectionEvent


class DetectionLayer(StrEnum):
    """The detector layer that found an instruction.

    Features:
        US-BEZ-01, F-19, ADR-12, ADR-35
    """

    PATTERNS = "patterns"
    GATE = "gate"
    CLASSIFIER = "classifier"


class TextRange(NamedTuple):
    """A half-open ``[start, end)`` range of characters in the scanned text.

    Attributes:
        start: Index of the first character.
        end: Index after the last character.

    Features:
        US-BEZ-01, F-19
    """

    start: int
    end: int


class InjectionSpan(BaseModel):
    """One detected instruction: its sentence in the scanned text and who found it.

    Attributes:
        start: Index of the first character of the instruction's sentence.
        end: Index after its last character.
        layer: The layer that found it.

    Features:
        US-BEZ-01, F-19, ADR-23
    """

    model_config = ConfigDict(frozen=True)

    start: int = Field(ge=0)
    end: int = Field(gt=0)
    layer: DetectionLayer


class InjectionScan(BaseModel):
    """The scanned text with every instruction found in it.

    Spans of different layers may overlap; each keeps the layer that found it.

    Attributes:
        text: The scanned text, unchanged.
        spans: Detected instructions, ordered by position.

    Features:
        US-BEZ-01, F-19, ADR-12, ADR-23
    """

    model_config = ConfigDict(frozen=True)

    text: str
    spans: tuple[InjectionSpan, ...] = ()

    @property
    def detected(self) -> bool:
        """Whether any layer found an instruction."""
        return bool(self.spans)


class InjectionClassification(BaseModel):
    """The isolated classifier's answer (the ``LlmPort`` output model).

    Attributes:
        injected: Whether the text holds instructions for an AI system.
        instructions: Each instruction copied verbatim from the text.

    Features:
        US-BEZ-01, F-19, ADR-12
    """

    model_config = ConfigDict(frozen=True)

    injected: bool
    instructions: tuple[str, ...] = ()


class CleanedInput(BaseModel):
    """User text with instructions cut out, and one event per cut.

    Attributes:
        text: What is left to analyse as data.
        events: ``instruction_removed`` events for the check result.

    Features:
        US-BEZ-01, F-19, ADR-23
    """

    model_config = ConfigDict(frozen=True)

    text: str
    events: tuple[InjectionEvent, ...] = ()
