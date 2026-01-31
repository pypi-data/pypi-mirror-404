# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason_construct

"""
coreason-construct: The Standard Library for Cognitive Architecture.
"""

__version__ = "0.4.0"
__author__ = "Gowtham A Rao"
__email__ = "gowtham.rao@coreason.ai"

from .contexts.registry import CONTEXT_REGISTRY
from .primitives.base import StructuredPrimitive
from .roles.base import RoleDefinition
from .schemas.base import ComponentType, PromptComponent, PromptConfiguration
from .weaver import Weaver

__all__ = [
    "CONTEXT_REGISTRY",
    "ComponentType",
    "PromptComponent",
    "PromptConfiguration",
    "RoleDefinition",
    "StructuredPrimitive",
    "Weaver",
]
