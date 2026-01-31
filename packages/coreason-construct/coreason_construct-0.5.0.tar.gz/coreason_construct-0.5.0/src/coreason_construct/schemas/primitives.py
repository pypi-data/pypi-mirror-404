# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason_construct

from typing import List

from pydantic import BaseModel, Field


class Summary(BaseModel):
    """
    Structured summary object.
    """

    title: str
    bullets: List[str]
    sentiment: float = Field(description="Sentiment score between -1.0 (negative) and 1.0 (positive)")


class Criterion(BaseModel):
    """
    A single inclusion/exclusion criterion.
    """

    field: str
    operator: str
    value: str
    type: str = Field(description="INCLUSION or EXCLUSION")


class CohortQuery(BaseModel):
    """
    Structured query logic for patient selection.
    """

    inclusion_criteria: List[Criterion]
    sql_logic: str = Field(description="Valid SQL query string")
