# coreason-construct

**The Standard Library for Cognitive Architecture.**

[![CI/CD](https://github.com/CoReason-AI/coreason-construct/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/CoReason-AI/coreason-construct/actions/workflows/ci-cd.yml)
[![Docker](https://github.com/CoReason-AI/coreason-construct/actions/workflows/docker.yml/badge.svg)](https://github.com/CoReason-AI/coreason-construct/actions/workflows/docker.yml)
[![PyPI version](https://badge.fury.io/py/coreason_construct.svg)](https://badge.fury.io/py/coreason_construct)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/coreason_construct.svg)](https://pypi.org/project/coreason_construct/)
[![License](https://img.shields.io/badge/license-Prosperity%20Public%20License%203.0-blue.svg)](LICENSE)
[![codecov](https://codecov.io/gh/CoReason-AI/coreason-construct/branch/main/graph/badge.svg)](https://codecov.io/gh/CoReason-AI/coreason-construct)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)

## Executive Summary

coreason-construct is the **Standard Library for Cognitive Architecture**.

It replaces ad-hoc prompt engineering with **Type-Driven Generation**. It integrates **instructor** to patch LLM clients, linking Pydantic schemas directly to the model's logits.

However, structure alone is not enough. The package provides a strictly typed library of **Cognitive Components**—Roles, Contexts, Logic Primitives, and Data Banks—that are assembled by the **Weaver**. The Weaver not only enforces output schema but also manages **Dependency Resolution** (context injection) and **Token Optimization** before the request is sent.

## Service Mode (New in v0.5.0)

`coreason-construct` can now act as a **Prompt Compilation Microservice** (Service C). This service exposes endpoints to:

*   **Compile (`/v1/compile`)**: Weave components into a final configuration, handling context injection and token optimization on the server side.
*   **Optimize (`/v1/optimize`)**: Compress raw text using token-aware strategies (e.g., middle-out pruning).

Refer to the [Usage Guide](docs/usage.md#microservice-usage) for API details.

## Functional Philosophy: The Assembler Pattern

"Prompts are not written; they are assembled. Outputs are not strings; they are Objects."

A Prompt is an object composed of:

1.  **Identity (Who):** The Role and its biases.
2.  **Environment (Where):** The regulatory and data context.
3.  **Mode (How):** The active reasoning style (e.g., "Six Hats", "Socratic").
4.  **Data (Evidence):** Few-shot examples and negative constraints.
5.  **Task (What):** The **Structured Primitive** (e.g., CohortLogic, Extract).
6.  **Output (Type):** The specific Pydantic model the LLM *must* populate.

## Getting Started

### Prerequisites

- Python 3.12+
- Poetry (for development)

### Installation

```sh
pip install coreason-construct
```

Or with Poetry:

```sh
poetry add coreason-construct
```

### Quick Start

Assemble a prompt for Adverse Event extraction using a standardized Role and Few-Shot Data.

```python
from coreason_construct import Weaver
from coreason_construct.roles.library import SafetyScientist
from coreason_construct.data.library import AE_Examples
from coreason_construct.primitives.extract import ExtractionPrimitive
from coreason_construct.schemas.clinical import AdverseEvent

# 1. Initialize the Weaver
weaver = Weaver()

# 2. Add Components
# Automatically injects dependencies (e.g., HIPAA & GxP Contexts for SafetyScientist)
weaver.add(SafetyScientist)
# Injects Few-Shot examples for robust extraction
weaver.add(AE_Examples)

# 3. Add the Task (Primitive)
extractor = ExtractionPrimitive(
    name="AE_Extractor",
    schema=AdverseEvent
)
weaver.add(extractor)

# 4. Build the Prompt Configuration
user_input = "Patient reported mild nausea after taking the study drug."
config = weaver.build(user_input)

# The 'config' object is now ready to be sent to an LLM via instructor
print(config.system_message)
# Output includes:
# - Safety Scientist Persona
# - HIPAA/GxP Constraints
# - Few-Shot Examples (formatted JSON)
# - Extraction Instructions
```

## Documentation

For more detailed information, please refer to the documentation:

*   [Usage Guide](docs/usage.md): Detailed explanation of components, the Weaver, and Microservice API.
*   [Requirements](docs/requirements.md): Full list of dependencies for Library and Service modes.
*   [Vignette](docs/vignette.md): A narrative example of using coreason-construct.
*   [Product Requirements Document](docs/PRD.md): The full PRD for this library.

## License

Proprietary and Dual-Licensed. See [LICENSE](LICENSE) for details.
