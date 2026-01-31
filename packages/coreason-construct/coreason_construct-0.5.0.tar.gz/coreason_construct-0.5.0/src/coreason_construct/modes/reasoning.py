# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason_construct

from coreason_construct.schemas.base import ComponentType, PromptComponent


class ReasoningPatterns:
    """Library of advanced reasoning modes."""

    FirstPrinciples = PromptComponent(
        name="Reasoning_FirstPrinciples",
        type=ComponentType.MODE,
        content=(
            "Reason from First Principles. Break the problem down to its most basic truths "
            "and build up from there. Do not rely on analogy or convention."
        ),
        priority=8,
    )

    PreMortem = PromptComponent(
        name="Reasoning_PreMortem",
        type=ComponentType.MODE,
        content=(
            "Perform a Pre-Mortem analysis. Assume the proposed solution has failed strictly. "
            "Work backward to determine the specific causes of this failure."
        ),
        priority=8,
    )

    ChainOfVerification = PromptComponent(
        name="Reasoning_ChainOfVerification",
        type=ComponentType.MODE,
        content=(
            "Use Chain of Verification. Draft an initial response, then generate verification questions "
            "to check your facts. Finally, answer the questions and revise the response."
        ),
        priority=8,
    )
