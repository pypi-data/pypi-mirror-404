# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason_construct

from coreason_construct.primitives.base import StructuredPrimitive
from coreason_construct.schemas.primitives import CohortQuery


class CohortLogicPrimitive(StructuredPrimitive):
    """
    Task: Generates structured query logic for patient selection.
    """

    def __init__(self, name: str = "CohortBuilder", priority: int = 10):
        super().__init__(
            name=name,
            content=(
                "Translate the natural language request into a structured cohort query including inclusion criteria "
                "and SQL logic."
            ),
            priority=priority,
            response_model=CohortQuery,
        )
