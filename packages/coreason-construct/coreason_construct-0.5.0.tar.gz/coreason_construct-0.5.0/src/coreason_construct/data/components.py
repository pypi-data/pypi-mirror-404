# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason_construct

from typing import Any, Dict, List, Union

from pydantic import BaseModel

from coreason_construct.schemas.base import ComponentType, PromptComponent


class FewShotExample(BaseModel):
    """
    Structure for a single few-shot example.
    """

    input: str
    output: Union[str, Dict[str, Any]]


class FewShotBank(PromptComponent):
    """
    Manages the "Few-Shot" context window.
    Maps input -> ideal output.
    """

    type: ComponentType = ComponentType.DATA
    examples: List[FewShotExample]

    def __init__(self, name: str, examples: List[FewShotExample], priority: int = 5):
        formatted_examples = "\n\n".join(f"Input: {ex.input}\nIdeal Output: {ex.output}" for ex in examples)
        content = f"Here are some examples of how to perform the task:\n\n{formatted_examples}"
        super().__init__(name=name, type=ComponentType.DATA, content=content, priority=priority, examples=examples)


class NegativeExample(PromptComponent):
    """
    Explicit examples of failures to avoid.
    """

    type: ComponentType = ComponentType.DATA

    def __init__(self, name: str, examples: List[str], priority: int = 6):
        formatted_negatives = "\n".join(f"- {ex}" for ex in examples)
        content = f"NEGATIVE CONSTRAINTS (DO NOT DO THIS):\n{formatted_negatives}"
        super().__init__(name=name, type=ComponentType.DATA, content=content, priority=priority)


class DataDictionary(PromptComponent):
    """
    Injects domain definitions.
    """

    type: ComponentType = ComponentType.DATA

    def __init__(self, name: str, terms: Dict[str, str], priority: int = 4):
        formatted_terms = "\n".join(f"{term}: {definition}" for term, definition in terms.items())
        content = f"DATA DICTIONARY / DEFINITIONS:\n{formatted_terms}"
        super().__init__(name=name, type=ComponentType.DATA, content=content, priority=priority)
