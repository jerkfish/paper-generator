"""Pydantic models for LLM-proposed question labels (Step 3)."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class QuestionRow(BaseModel):
    """One question or sub-part, as proposed by the LLM and verified by code."""

    q_no: str
    sub_part: str = ""
    original_text: str = Field(min_length=1)
    marks: float | None = None  # None = not stated (unsure)
    topic: str = ""
    question_type: str = ""
    has_diagram: bool = False
    diagram_type: str = ""
    machine_verifiable: Literal["Y", "Partial", "N"] = "N"
    wording_note: str = ""


class PaperQuestions(BaseModel):
    paper_id: str
    questions: list[QuestionRow]
