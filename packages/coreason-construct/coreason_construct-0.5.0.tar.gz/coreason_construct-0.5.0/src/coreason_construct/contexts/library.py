# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason_construct

from typing import Any

from coreason_identity.models import UserContext
from loguru import logger

from coreason_construct.schemas.base import ComponentType, PromptComponent


class PatientHistory(PromptComponent):
    """
    Dynamic Context: Injects patient history based on ID.
    """

    type: ComponentType = ComponentType.CONTEXT

    def __init__(self, patient_id: str, priority: int = 7, **data: Any) -> None:
        if "content" not in data:
            data["content"] = (
                f"Patient History for ID: {patient_id}.\n"
                "[Dynamic patient history data would be injected here from the database]"
            )
        super().__init__(name=f"PatientHistory_{patient_id}", priority=priority, type=ComponentType.CONTEXT, **data)


class StudyProtocol(PromptComponent):
    """
    Dynamic Context: Injects study protocol based on NCT ID.
    """

    type: ComponentType = ComponentType.CONTEXT

    def __init__(self, nct_id: str, priority: int = 7, **data: Any) -> None:
        if "content" not in data:
            data["content"] = (
                f"Study Protocol for NCT ID: {nct_id}.\n"
                "[Dynamic protocol data would be injected here from the database]"
            )
        super().__init__(name=f"StudyProtocol_{nct_id}", priority=priority, type=ComponentType.CONTEXT, **data)


def create_static_context(name: str, content: str, priority: int = 5) -> PromptComponent:
    """Helper to create static context components."""
    return PromptComponent(name=name, type=ComponentType.CONTEXT, content=content, priority=priority)


HIPAA_Context = create_static_context(
    name="HIPAA",
    content=(
        "You must strictly adhere to HIPAA regulations. "
        "Do not disclose Protected Health Information (PHI) unless explicitly authorized. "
        "De-identify all patient data where possible."
    ),
    priority=10,
)

GxP_Context = create_static_context(
    name="GxP",
    content=(
        "Follow GxP guidelines (Good Clinical Practice, Good Laboratory Practice, etc.). "
        "Ensure data integrity, traceability, and accountability in all responses."
    ),
    priority=9,
)


class ContextLibrary:
    @staticmethod
    def register_context(name: str, component: Any, context: UserContext) -> None:
        from coreason_construct.contexts.registry import CONTEXT_REGISTRY

        if not context:
            raise ValueError("UserContext is required")
        logger.debug("Registering artifact", user_id=context.user_id, type="context", name=name)
        CONTEXT_REGISTRY[name] = component

    @staticmethod
    def get_context(name: str, context: UserContext) -> Any:
        from coreason_construct.contexts.registry import CONTEXT_REGISTRY

        if not context:
            raise ValueError("UserContext is required")
        # In a real system we might check access here
        return CONTEXT_REGISTRY.get(name)
