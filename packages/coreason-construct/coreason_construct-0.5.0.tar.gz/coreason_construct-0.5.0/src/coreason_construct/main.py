# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason_construct

import argparse
import json
import sys

from coreason_identity.models import UserContext

from coreason_construct.schemas.base import PromptComponent
from coreason_construct.weaver import Weaver


def get_cli_context() -> UserContext:
    return UserContext(
        user_id="cli-user", email="cli@coreason.ai", groups=["system"], scopes=[], claims={"source": "cli"}
    )


def create_command(args: argparse.Namespace, context: UserContext) -> None:
    try:
        with open(args.components_file, "r") as f:
            data = json.load(f)
            # Assuming data is list of components
            components = [PromptComponent(**c) for c in data]
    except Exception as e:
        print(f"Error reading components file: {e}", file=sys.stderr)
        return

    weaver = Weaver()
    weaver.create_construct(args.name, components, context)
    print(f"Construct '{args.name}' created.")


def resolve_command(args: argparse.Namespace, context: UserContext) -> None:
    weaver = Weaver()
    # In a persistent system, we would load the construct here.
    # Since Weaver is currently ephemeral, this assumes the construct state is somehow managed or re-hydrated.
    # For CLI demo purposes, we proceed with an empty weaver but calling the correct method with context.

    variables = {}
    if args.variables_file:
        try:
            with open(args.variables_file, "r") as f:
                variables = json.load(f)
        except Exception as e:
            print(f"Error reading variables file: {e}", file=sys.stderr)
            return

    config = weaver.resolve_construct(args.construct_id, variables, context)
    print(config.model_dump_json(indent=2))


def visualize_command(args: argparse.Namespace, context: UserContext) -> None:
    weaver = Weaver()
    result = weaver.visualize_construct(args.construct_id, context)
    print(json.dumps(result, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description="Coreason Construct CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    create_parser = subparsers.add_parser("create")
    create_parser.add_argument("--name", required=True)
    create_parser.add_argument("--components-file", required=True)

    resolve_parser = subparsers.add_parser("resolve")
    resolve_parser.add_argument("--construct-id", required=True)
    resolve_parser.add_argument("--variables-file")

    visualize_parser = subparsers.add_parser("visualize")
    visualize_parser.add_argument("--construct-id", required=True)

    args = parser.parse_args()
    context = get_cli_context()

    if args.command == "create":
        create_command(args, context)
    elif args.command == "resolve":
        resolve_command(args, context)
    elif args.command == "visualize":
        visualize_command(args, context)


if __name__ == "__main__":  # pragma: no cover
    main()
