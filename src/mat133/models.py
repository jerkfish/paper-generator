"""Document models for generated MAT133 papers and marking schemes."""
from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class DiagramSpec(BaseModel):
    path: str = Field(min_length=1)
    caption: str = Field(default="", max_length=300)
    width_cm: float = Field(default=10.0, gt=0, le=18)


class FormulaSpec(BaseModel):
    path: str = Field(min_length=1)
    caption: str = Field(default="", max_length=300)
    width_cm: float = Field(default=6.0, gt=0, le=18)


class Mat133Part(BaseModel):
    label: str = Field(default="", max_length=20)
    text: str = Field(min_length=1, max_length=3000)
    marks: float = Field(gt=0, le=20)
    topic: str = ""
    subtopic: str = ""
    diagram: DiagramSpec | None = None
    formula: FormulaSpec | None = None
    answer: str = Field(default="", max_length=3000)
    answer_latex: str = Field(default="", max_length=3000)
    solution_steps: list[str] = Field(default_factory=list, max_length=20)
    solution_latex: list[str] = Field(default_factory=list, max_length=20)
    solution_marks: list[str] = Field(default_factory=list, max_length=20)
    marking_notes: list[str] = Field(default_factory=list, max_length=12)

    @field_validator("solution_steps", "solution_latex", "solution_marks",
                     "marking_notes",
                     mode="before")
    @classmethod
    def _coerce_list(cls, value):
        if value is None:
            return []
        if isinstance(value, str):
            return [value]
        return value


class Mat133Question(BaseModel):
    number: int = Field(ge=1, le=30)
    stem: str = Field(default="", max_length=3000)
    parts: list[Mat133Part] = Field(min_length=1, max_length=20)


class Mat133Paper(BaseModel):
    subject: str = "MAT133"
    month: str = Field(min_length=3, max_length=20)
    year: int = Field(ge=2000, le=2100)
    duration: str = Field(default="2 HOURS", max_length=40)
    questions: list[Mat133Question] = Field(min_length=1, max_length=30)
    appendix: list[str] = Field(default_factory=list, max_length=40)
    title: str = "PRE CALCULUS"
    with_appendix: bool = True
    seed: int | None = None
    generator_notes: list[str] = Field(default_factory=list)

    @field_validator("appendix", "generator_notes", mode="before")
    @classmethod
    def _coerce_list(cls, value):
        if value is None:
            return []
        if isinstance(value, str):
            return [value]
        return value

    @property
    def total_marks(self) -> float:
        return sum(part.marks for q in self.questions for part in q.parts)

    def question_marks(self, number: int) -> float:
        return sum(part.marks for q in self.questions
                   if q.number == number for part in q.parts)


DEFAULT_APPENDIX = [
    "sin² A + cos² A = 1",
    "sin(A + B) = sin A cos B + cos A sin B",
    "cos(A + B) = cos A cos B − sin A sin B",
    "tan(A − B) = (tan A − tan B) / (1 + tan A tan B)",
    "cos 2A = cos² A − sin² A",
    "cos 2A = 1 − 2sin² A = 2cos² A − 1",
    "sin 2A = 2 sin A cos A",
    "tan² A + 1 = sec² A",
    "tan 2A = 2 tan A / (1 − tan² A)",
    "Arc length, s = rθ",
    "Area of sector = ½r²θ",
    "a / sin A = b / sin B = c / sin C",
    "a² = b² + c² − 2bc cos A",
    "Area of triangle = ½ab sin C",
]
