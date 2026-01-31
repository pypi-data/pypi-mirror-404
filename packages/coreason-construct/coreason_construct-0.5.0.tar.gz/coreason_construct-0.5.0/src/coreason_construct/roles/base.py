# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason_construct

from typing import Any, List

from pydantic import Field

from coreason_construct.schemas.base import ComponentType, PromptComponent


class RoleDefinition(PromptComponent):
    """
    Standardized "Persona" component.

    Attributes:
        title: The professional title of the role.
        tone: The required tone of voice.
        competencies: List of key skills or knowledge areas.
        biases: specific biases or perspectives this role should adopt.
        dependencies: List of context names that this role requires.
    """

    type: ComponentType = ComponentType.ROLE
    title: str
    tone: str
    competencies: List[str]
    biases: List[str] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)

    def __init__(self, **data: Any) -> None:
        # Auto-generate content if not explicitly provided, based on attributes
        if "content" not in data:
            title = data.get("title", "Expert")
            tone = data.get("tone", "Professional")
            competencies = ", ".join(data.get("competencies", []))
            biases = ", ".join(data.get("biases", []))

            content = f"You are a {title}.\nTone: {tone}.\nCompetencies: {competencies}.\n"
            if biases:
                content += f"Biases/Perspective: {biases}.\n"

            data["content"] = content

        super().__init__(**data)
