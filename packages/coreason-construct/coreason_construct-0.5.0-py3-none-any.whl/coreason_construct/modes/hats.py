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


class SixThinkingHats:
    """Factory for De Bono's Six Thinking Hats modes."""

    @staticmethod
    def _create_hat(color: str, focus: str) -> PromptComponent:
        return PromptComponent(
            name=f"SixHats_{color}",
            type=ComponentType.MODE,
            content=f"Adopt the {color} Hat thinking mode. Focus strictly on: {focus}.",
            priority=8,
        )

    White = _create_hat("White", "Facts, figures, and objective information. No opinions or emotions.")
    Red = _create_hat("Red", "Emotions, feelings, and intuition. No justification required.")
    Black = _create_hat("Black", "Caution, risks, and critical judgment. Identify potential problems.")
    Yellow = _create_hat("Yellow", "Optimism, benefits, and feasibility. Identify value and opportunities.")
    Green = _create_hat("Green", "Creativity, alternatives, and new ideas. Think outside the box.")
    Blue = _create_hat("Blue", "Process control, metacognition, and organization. Manage the thinking process.")
