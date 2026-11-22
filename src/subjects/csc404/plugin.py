"""Subject plugin scaffold for CSC404 (asset-first recycle of real past-paper questions (default)).

This file is the only place subject-specific pipeline code belongs.
Replace the stubs after the stage-0 intake checkpoint.  The shared app
loads this module through subjects/CSC404/subject.json.
"""
from __future__ import annotations


# Recycle subjects keep their questions in the shared bank.  Subject-specific
# extraction/normalisation rules may be added here later; generators are off.

def generator_labels() -> dict:
    return {}


def topic_labels() -> dict:
    return {}
