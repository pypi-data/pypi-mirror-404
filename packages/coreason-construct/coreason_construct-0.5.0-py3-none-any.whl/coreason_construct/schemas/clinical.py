# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason_construct

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class Severity(str, Enum):
    """Clinical severity scale."""

    MILD = "MILD"
    MODERATE = "MODERATE"
    SEVERE = "SEVERE"
    LIFE_THREATENING = "LIFE_THREATENING"
    FATAL = "FATAL"


class Causality(str, Enum):
    """Relationship to the study drug/procedure."""

    RELATED = "RELATED"
    POSSIBLY_RELATED = "POSSIBLY_RELATED"
    UNLIKELY_RELATED = "UNLIKELY_RELATED"
    NOT_RELATED = "NOT_RELATED"


class Outcome(str, Enum):
    """Outcome of the adverse event."""

    RECOVERED = "RECOVERED"
    RECOVERING = "RECOVERING"
    NOT_RECOVERED = "NOT_RECOVERED"
    FATAL = "FATAL"
    UNKNOWN = "UNKNOWN"


class AdverseEvent(BaseModel):
    """
    Schema for a clinical Adverse Event (AE).
    """

    term: str = Field(description="The medical term for the adverse event (e.g., 'Nausea', 'Headache').", min_length=1)
    severity: Severity = Field(description="The intensity of the event.")
    causality: Optional[Causality] = Field(default=None, description="The causal relationship to the intervention.")
    outcome: Optional[Outcome] = Field(default=None, description="The final outcome of the event.")
