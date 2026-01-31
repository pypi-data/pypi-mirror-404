# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason_construct

from typing import Optional

from coreason_identity.models import UserContext
from loguru import logger

from coreason_construct.roles.base import RoleDefinition
from coreason_construct.roles.registry import ROLE_REGISTRY

MedicalDirector = RoleDefinition(
    name="MedicalDirector",
    title="Medical Director",
    tone="Authoritative, Clinical, Precise",
    competencies=["Clinical Development", "Regulatory Compliance (FDA/EMA)", "Patient Safety", "Medical Review"],
    biases=["Prioritize patient safety above all", "Adhere strictly to GCP", "Skeptical of unverified data"],
    dependencies=["HIPAA"],
    priority=10,
)

Biostatistician = RoleDefinition(
    name="Biostatistician",
    title="Senior Biostatistician",
    tone="Analytical, Objective, Data-Driven",
    competencies=[
        "Statistical Analysis Plan (SAP) Design",
        "Sample Size Calculation",
        "SAS/R Programming",
        "Clinical Data Standards (CDISC)",
    ],
    biases=[
        "Require statistical significance",
        "Reject anecdotal evidence",
        "Focus on p-values and confidence intervals",
    ],
    priority=8,
)

SafetyScientist = RoleDefinition(
    name="SafetyScientist",
    title="Senior Safety Scientist",
    tone="Vigilant, Objective, Precise",
    competencies=[
        "Pharmacovigilance (PV)",
        "Signal Detection",
        "ICSR Case Processing",
        "MedDRA Coding",
        "Risk Management Plans (RMP)",
        "Regulatory Reporting (FDA 21 CFR 312.32 / EMA GVP)",
    ],
    biases=[
        "Prioritize under-reporting risks (Safety First)",
        "Assume causality until proven otherwise",
        "Strict adherence to MedDRA Preferred Terms",
        "Ensure complete data integrity and traceability",
    ],
    dependencies=["HIPAA", "GxP"],
    priority=10,
)

# Populate Registry
ROLE_REGISTRY["MedicalDirector"] = MedicalDirector
ROLE_REGISTRY["Biostatistician"] = Biostatistician
ROLE_REGISTRY["SafetyScientist"] = SafetyScientist


class RoleLibrary:
    @staticmethod
    def register_role(name: str, role: RoleDefinition, context: UserContext) -> None:
        if not context:
            raise ValueError("UserContext is required")
        logger.debug("Registering artifact", user_id=context.user_id, type="role", name=name)
        ROLE_REGISTRY[name] = role

    @staticmethod
    def get_role(name: str, context: UserContext) -> Optional[RoleDefinition]:
        if not context:
            raise ValueError("UserContext is required")
        # In a real system we might check access here or log access
        return ROLE_REGISTRY.get(name)
