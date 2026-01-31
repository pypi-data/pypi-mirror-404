# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason_construct

from typing import Dict, Type, Union

from coreason_construct.contexts.library import GxP_Context, HIPAA_Context, PatientHistory, StudyProtocol
from coreason_construct.schemas.base import PromptComponent

CONTEXT_REGISTRY: Dict[str, Union[PromptComponent, Type[PromptComponent]]] = {
    "HIPAA": HIPAA_Context,
    "GxP": GxP_Context,
    "PatientHistory": PatientHistory,
    "StudyProtocol": StudyProtocol,
}
