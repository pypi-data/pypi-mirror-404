# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason_construct

from typing import Type

from pydantic import BaseModel

from coreason_construct.primitives.base import StructuredPrimitive


class ExtractionPrimitive(StructuredPrimitive):
    """
    Pulls entities into a generic Pydantic model.
    """

    def __init__(self, name: str, schema: Type[BaseModel], priority: int = 10):
        content = f"Extract the following information from the input data according to the schema {schema.__name__}."

        super().__init__(name=name, content=content, priority=priority, response_model=schema)
