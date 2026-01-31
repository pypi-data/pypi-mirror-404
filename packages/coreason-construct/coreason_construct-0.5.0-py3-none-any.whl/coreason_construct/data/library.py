# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason_construct

from coreason_construct.data.components import FewShotBank, FewShotExample

AE_Examples = FewShotBank(
    name="AE_Examples",
    examples=[
        FewShotExample(
            input="Patient reported mild nausea.",
            output={"term": "Nausea", "severity": "MILD", "causality": None, "outcome": None},
        ),
        FewShotExample(
            input="Subject died due to cardiac arrest, unrelated to study treatment.",
            output={
                "term": "Cardiac Arrest",
                "severity": "FATAL",
                "causality": "NOT_RELATED",
                "outcome": "FATAL",
            },
        ),
    ],
    priority=5,
)
