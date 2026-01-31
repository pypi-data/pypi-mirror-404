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
from typing import Type

from pydantic import Field, create_model

from coreason_construct.primitives.base import StructuredPrimitive


class ClassificationPrimitive(StructuredPrimitive):
    """
    Forces a choice from a given Enum.
    """

    def __init__(self, name: str, enum_type: Type[Enum], priority: int = 10):
        # Dynamically create a Pydantic model that wraps the Enum
        # This is because instructor/LLMs usually handle fields better than raw Enums as top level
        model_name = f"{name}Output"
        response_model = create_model(
            model_name,
            selection=(enum_type, Field(..., description=f"Select the most appropriate {enum_type.__name__}.")),
        )

        content = (
            f"Classify the input into one of the following categories defined in {enum_type.__name__}:\n"
            f"{[e.value for e in enum_type]}"
        )

        super().__init__(name=name, content=content, priority=priority, response_model=response_model)
