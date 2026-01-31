# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason_construct

import inspect
from typing import Any, Dict, List, Optional, Type, Union

import tiktoken
from coreason_identity.models import UserContext
from loguru import logger
from pydantic import BaseModel

from coreason_construct.contexts.library import ContextLibrary
from coreason_construct.primitives.base import StructuredPrimitive
from coreason_construct.schemas.base import ComponentType, PromptComponent, PromptConfiguration


class Weaver:
    """
    The Builder Engine that stitches components into the final request configuration.
    """

    def __init__(self, context_data: Optional[Dict[str, Any]] = None) -> None:
        self.components: List[PromptComponent] = []
        self._response_model: Optional[Type[BaseModel]] = None
        self.context_data: Dict[str, Any] = context_data or {}

    def _has_component(self, name: str) -> bool:
        return any(c.name == name for c in self.components)

    def _sort_components(self, components: List[PromptComponent]) -> List[PromptComponent]:
        # Sort by priority (descending), then stable
        return sorted(components, key=lambda c: c.priority, reverse=True)

    def _resolve_dependency(self, dep_name: str, context: Optional[UserContext]) -> Optional[PromptComponent]:
        """
        Resolves a dependency name to a PromptComponent instance.
        Supports both static instances and dynamic class instantiation.
        """
        if not context:
            # Enforce context as per "Fail Safe" constraint
            raise ValueError(f"UserContext is required to resolve dependency '{dep_name}'")

        # Use ContextLibrary to retrieve artifact (ensures audit logging)
        registry_item: Optional[Union[PromptComponent, Type[PromptComponent]]] = ContextLibrary.get_context(
            dep_name, context
        )

        if not registry_item:
            return None

        # Case 1: Registry item is already an instance
        if isinstance(registry_item, PromptComponent):
            return registry_item

        # Case 2: Registry item is a class (Dynamic Context)
        if isinstance(registry_item, type) and issubclass(registry_item, PromptComponent):
            # Inspect __init__ to see what arguments it needs
            init_signature = inspect.signature(registry_item.__init__)
            init_params = init_signature.parameters

            # Prepare arguments from context_data
            kwargs = {}
            missing_params = []

            for param_name, param in init_params.items():
                if param_name == "self":
                    continue
                # If param is in context_data, use it
                if param_name in self.context_data:
                    kwargs[param_name] = self.context_data[param_name]
                # If param has no default value and is missing, flag it
                elif param.default == inspect.Parameter.empty and param.kind not in (
                    inspect.Parameter.VAR_POSITIONAL,
                    inspect.Parameter.VAR_KEYWORD,
                ):
                    missing_params.append(param_name)

            if missing_params:
                logger.warning(
                    f"Cannot instantiate dependency '{dep_name}': Missing required context data: {missing_params}"
                )
                return None

            try:
                return registry_item(**kwargs)
            except Exception as e:
                logger.error(f"Failed to instantiate dependency '{dep_name}': {e}")

        return None

    def add(self, component: PromptComponent, context: Optional[UserContext] = None) -> "Weaver":
        """
        Add a component to the weaver.
        Handles dependency resolution.
        """
        # Avoid duplicate addition
        if self._has_component(component.name):
            return self

        # Add the component first to handle circular dependencies (breaking the recursion)
        self.components.append(component)

        if isinstance(component, StructuredPrimitive):
            self._response_model = component.response_model

        # 1. Dependency Resolution
        if hasattr(component, "dependencies"):
            deps: List[str] = getattr(component, "dependencies", [])
            for dep_name in deps:
                # Resolve the dependency (instance or new instance from class)
                if not self._has_component(dep_name) and not any(
                    c.name.startswith(f"{dep_name}_") for c in self.components
                ):
                    # Note: The check startswith is a heuristic for dynamic components like PatientHistory_123
                    # But exact name match check is safer if the dynamic component sets a predictable name.
                    # Ideally we resolve it, check its name, then decide.

                    resolved_context = self._resolve_dependency(dep_name, context=context)

                    if resolved_context:
                        # Recursive call to handle transitive dependencies
                        self.add(resolved_context, context=context)
                    else:
                        logger.warning(
                            f"Dependency '{dep_name}' required by '{component.name}' "
                            "not found or could not be instantiated."
                        )

        return self

    def create_construct(self, name: str, components: List[PromptComponent], context: UserContext) -> None:
        """
        Creates a new construct by adding components.
        Identity-aware: Requires UserContext.
        """
        if not context:
            raise ValueError("UserContext is required for create_construct")

        logger.info(f"Creating construct '{name}'", user_id=context.user_id, name=name)

        for component in components:
            self.add(component, context=context)

    def resolve_construct(
        self, construct_id: str, variables: Dict[str, Any], context: UserContext
    ) -> PromptConfiguration:
        """
        Resolves a construct (builds it).
        Identity-aware: Requires UserContext.
        """
        if not context:
            raise ValueError("UserContext is required for resolve_construct")

        logger.info(f"Resolving construct '{construct_id}'", user_id=context.user_id, construct_id=construct_id)

        # In a real system, we might load components by construct_id here.
        # Since Weaver is stateful in this implementation (components added via create_construct),
        # we proceed to build using the current state.
        user_input = variables.get("user_input", "")
        # Extract max_tokens if present in variables (convention)
        max_tokens = variables.get("max_tokens")
        if not isinstance(max_tokens, int):
            max_tokens = None

        return self.build(user_input=user_input, variables=variables, max_tokens=max_tokens, context=context)

    def visualize_construct(self, construct_id: str, context: UserContext) -> Dict[str, Any]:
        """
        Visualizes the construct components.
        Identity-aware: Requires UserContext.
        """
        if not context:
            raise ValueError("UserContext is required for visualize_construct")

        logger.info(f"Visualizing construct '{construct_id}'", user_id=context.user_id, construct_id=construct_id)

        return {"construct_id": construct_id, "components": [c.model_dump() for c in self.components]}

    def _estimate_tokens(self, text: str) -> int:
        """
        Estimate tokens using tiktoken.
        """
        encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text))

    def build(
        self,
        user_input: str,
        variables: Optional[Dict[str, Any]] = None,
        max_tokens: Optional[int] = None,
        context: Optional[UserContext] = None,
    ) -> PromptConfiguration:
        """
        Build the final prompt configuration.

        Args:
            user_input: The input data from the user.
            variables: Optional variables to render components.
            max_tokens: Maximum allowed estimated tokens. If exceeded, low priority components are dropped.
            context: Optional UserContext (though encouraged).
        """
        if variables is None:
            variables = {}

        # 2. Optimization Logic
        active_components = list(self.components)
        dropped_components_list: List[str] = []

        while True:
            # Re-sort/Filter active components
            sorted_comps = self._sort_components(active_components)

            # Generate Parts
            system_parts = [c.render(**variables) for c in sorted_comps if c.type != ComponentType.PRIMITIVE]
            task_part = next((c.render(**variables) for c in sorted_comps if c.type == ComponentType.PRIMITIVE), "")
            final_user_msg = f"{task_part}\n\nINPUT DATA:\n{user_input}" if task_part else user_input
            system_msg = "\n\n".join(system_parts)

            # Check Limits
            total_text = system_msg + final_user_msg
            estimated_tokens = self._estimate_tokens(total_text)

            if max_tokens is None or estimated_tokens <= max_tokens:
                break

            logger.info(f"Optimization loop: estimated={estimated_tokens}, limit={max_tokens}")

            # Need to truncate. Find lowest priority component that is not Critical (10).
            # PRD: "truncates 'Low Priority' contexts".
            # We sort by priority ascending to find removal candidates.
            # We filter out Priority 10 (Critical) components to ensure they are preserved.
            candidates = sorted([c for c in active_components if c.priority < 10], key=lambda c: c.priority)

            if not candidates:
                logger.warning(
                    f"Token limit exceeded ({estimated_tokens} > {max_tokens}), "
                    "but only Critical (Priority 10) components remain. Cannot truncate further."
                )
                break

            # Remove the lowest priority one
            to_remove = candidates[0]
            logger.info(
                f"Token limit exceeded ({estimated_tokens} > {max_tokens}). "
                f"Dropping component '{to_remove.name}' (Priority: {to_remove.priority})."
            )
            active_components.remove(to_remove)
            dropped_components_list.append(to_remove.name)

            if not active_components:
                break

        # Final Build with active_components
        sorted_comps = self._sort_components(active_components)
        system_parts = [c.render(**variables) for c in sorted_comps if c.type != ComponentType.PRIMITIVE]
        task_part = next((c.render(**variables) for c in sorted_comps if c.type == ComponentType.PRIMITIVE), "")
        final_user_msg = f"{task_part}\n\nINPUT DATA:\n{user_input}" if task_part else user_input

        # 3. Provenance Capture
        metadata = {
            "role": next((c.name for c in active_components if c.type == ComponentType.ROLE), "None"),
            "mode": next((c.name for c in active_components if c.type == ComponentType.MODE), "None"),
            "schema": self._response_model.__name__ if self._response_model else "None",
        }

        if context:
            metadata["owner_id"] = context.user_id

        return PromptConfiguration(
            system_message="\n\n".join(system_parts),
            user_message=final_user_msg,
            response_model=self._response_model,
            provenance_metadata=metadata,
            dropped_components=dropped_components_list,
        )
