# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason_construct

from typing import Any, Type

from pydantic import BaseModel

from coreason_construct.schemas.base import ComponentType, PromptComponent


class StructuredPrimitive(PromptComponent):
    """
    Base class for atomic units of work that return structured data.
    """

    type: ComponentType = ComponentType.PRIMITIVE
    response_model: Type[BaseModel]

    def __init__(self, **data: Any):
        if "type" not in data:
            data["type"] = ComponentType.PRIMITIVE
        super().__init__(**data)
