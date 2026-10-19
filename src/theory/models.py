"""Pydantic schemas for theory drafting and verification."""
from __future__ import annotations

from pydantic import BaseModel, Field

LECTURE_LABEL = "supported by lecture slides (not lecturer-marked)"


class MarkingPoint(BaseModel):
    point: str = Field(min_length=3, max_length=500)
    quote: str = Field(min_length=3, max_length=1200)
    chunk_id: str = Field(min_length=3, max_length=200)


class DraftQuestion(BaseModel):
    slot: str
    question: str = Field(min_length=8, max_length=1200)
    marking_points: list[MarkingPoint] = Field(min_length=1, max_length=12)


class TheoryDraft(BaseModel):
    scenario: str = Field(default="", max_length=1200)
    questions: list[DraftQuestion] = Field(min_length=1, max_length=2)


class VerifiedPoint(BaseModel):
    point: str
    marks: int = 1
    quote: str
    source_file: str
    source_slide: int
    source_deck: str
    source_key: str
    chunk_id: str
    term_overlap: float = 1.0
    low_term_overlap: bool = False
    short_quote: bool = False
    quote_repaired: bool = False


class VerifiedQuestion(BaseModel):
    slot: str
    question: str
    marks: int
    topic: str
    task: str
    marking_points: list[VerifiedPoint]
    confidence: str = LECTURE_LABEL
    citations: list[str]
    source_keys: list[str] = Field(default_factory=list)
    scenario: str = ""
    scenario_grounding: float = 1.0
    style_examples: list[dict] = Field(default_factory=list)
    style_mode: str = ""
    low_style_confidence: bool = False
    overlap_allowed: bool = False


class Placeholder(BaseModel):
    slot: str
    marks: int
    topic: str
    task: str
    reason: str
    attempts: int
    low_style_confidence: bool = False
