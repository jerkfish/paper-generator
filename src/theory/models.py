"""Pydantic schemas for theory drafting and verification."""
from __future__ import annotations

from pydantic import BaseModel, Field


class MarkingPoint(BaseModel):
    point: str = Field(min_length=3, max_length=500)
    quote: str = Field(min_length=3, max_length=1200)
    chunk_id: str = Field(min_length=3, max_length=200)


class DraftQuestion(BaseModel):
    slot: str
    question: str = Field(min_length=8, max_length=1200)
    marking_points: list[MarkingPoint] = Field(min_length=1, max_length=12)


class TheoryDraft(BaseModel):
    questions: list[DraftQuestion] = Field(min_length=1, max_length=2)


class VerifiedPoint(BaseModel):
    point: str
    marks: int = 1
    quote: str
    source_file: str
    source_slide: int
    source_deck: str
    chunk_id: str


class VerifiedQuestion(BaseModel):
    slot: str
    question: str
    marks: int
    topic: str
    task: str
    marking_points: list[VerifiedPoint]
    confidence: str = "sourced"
    citations: list[str]
    style_examples: list[dict] = Field(default_factory=list)
    style_mode: str = ""
    low_style_confidence: bool = False


class Placeholder(BaseModel):
    slot: str
    marks: int
    topic: str
    task: str
    reason: str
    attempts: int
    low_style_confidence: bool = False
