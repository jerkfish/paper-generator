"""Pydantic schema for the MAT133 paper-derived question log.

The LLM is asked for :class:`LLMPaper`; deterministic post-processing adds
paper metadata and validation flags to produce :class:`QuestionLog`.
"""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

Confidence = Literal["high", "medium", "low"]


class Given(BaseModel):
    """One concrete quantity or expression supplied in a question."""

    name: str = Field(min_length=1, max_length=120)
    value_type: str = Field(min_length=1, max_length=120)
    example: str = Field(default="", max_length=300)


class LLMPart(BaseModel):
    """A single graded question part as returned by the extraction model."""

    question: str = Field(min_length=1, max_length=40)
    part: str = Field(default="", max_length=40)
    marks: float | None = Field(default=None, ge=0, le=100)
    topic: str = Field(min_length=1, max_length=80)
    secondary_topics: list[str] = Field(default_factory=list)
    subtopic: str = Field(min_length=1, max_length=80)
    command: str = Field(default="solve", max_length=80)
    question_pattern: str = Field(default="", max_length=600)
    givens: list[Given] = Field(default_factory=list)
    parameter_types: list[str] = Field(default_factory=list)
    formula_forms: list[str] = Field(default_factory=list)
    solution_blueprint: list[str] = Field(default_factory=list)
    diagram: str = Field(default="none", max_length=80)
    evidence: str = Field(default="", max_length=1000)
    confidence: Confidence = "medium"
    review_flags: list[str] = Field(default_factory=list)

    @field_validator("givens", mode="before")
    @classmethod
    def _coerce_givens(cls, value: Any) -> Any:
        if value is None:
            return []
        if not isinstance(value, list):
            return value
        out = []
        for item in value:
            if isinstance(item, str):
                out.append({"name": item, "value_type": "unspecified",
                            "example": ""})
            else:
                out.append(item)
        return out

    @field_validator("secondary_topics", "parameter_types", "formula_forms",
                     "solution_blueprint", "review_flags", mode="before")
    @classmethod
    def _coerce_string_list(cls, value: Any) -> Any:
        if value is None:
            return []
        if isinstance(value, str):
            return [value]
        return value


class LLMPaper(BaseModel):
    """Raw extraction for one paper."""

    question_count: int | None = Field(default=None, ge=0, le=50)
    total_marks: int | None = Field(default=None, ge=0, le=500)
    parts: list[LLMPart] = Field(default_factory=list)
    notes: str = Field(default="", max_length=2000)


class QuestionEntry(LLMPart):
    """One question part with paper metadata and deterministic validation."""

    entry_id: str
    paper: str
    paper_stem: str
    month: str
    year: int
    priority: int = 9
    topic_label: str = ""
    duplicate_of: str | None = None
    taxonomy_version: int = 1


class PaperRecord(BaseModel):
    paper: str
    paper_stem: str
    month: str
    year: int
    pages: int = 0
    text_source: str = ""
    duplicate_of: str | None = None
    question_count: int | None = None
    total_marks: float | None = None
    entry_count: int = 0
    marks_sum: float = 0
    notes: str = ""
    review_flags: list[str] = Field(default_factory=list)


class PatternRecord(BaseModel):
    pattern_id: str
    topic: str
    topic_label: str
    subtopic: str
    priority: int
    frequency: int
    paper_count: int
    example_entry_ids: list[str] = Field(default_factory=list)
    commands: list[str] = Field(default_factory=list)
    parameter_types: list[str] = Field(default_factory=list)
    formula_forms: list[str] = Field(default_factory=list)
    solution_blueprint: list[str] = Field(default_factory=list)
    diagram_types: list[str] = Field(default_factory=list)
    marks_min: float | None = None
    marks_max: float | None = None
    marks_mean: float | None = None
    representative_question: str = ""


class ValidationSummary(BaseModel):
    entries: int = 0
    papers: int = 0
    unique_papers: int = 0
    unknown_topic: int = 0
    unknown_subtopic: int = 0
    missing_marks: int = 0
    unverified_evidence: int = 0
    low_confidence: int = 0
    duplicate_entries: int = 0
    total_marks_min: float = 0
    total_marks_max: float = 0
    warnings: list[str] = Field(default_factory=list)


class QuestionLog(BaseModel):
    schema_version: int = 1
    subject: str = "MAT133"
    source_dir: str = "data/papers/MAT133"
    generated_by: str = ""
    model: str = ""
    papers: list[PaperRecord] = Field(default_factory=list)
    entries: list[QuestionEntry] = Field(default_factory=list)
    patterns: list[PatternRecord] = Field(default_factory=list)
    validation: ValidationSummary = Field(default_factory=ValidationSummary)
