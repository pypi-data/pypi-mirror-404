from typing import Any, Dict, List, Optional

import jinja2
import tiktoken
from coreason_identity.models import UserContext
from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field
from tiktoken import Encoding

from coreason_construct.schemas.base import PromptComponent
from coreason_construct.weaver import Weaver

app = FastAPI(title="Coreason Construct Compiler", version="1.0.0")


class BlueprintRequest(BaseModel):
    user_input: str
    variables: Dict[str, Any] = Field(default_factory=dict)
    components: List[PromptComponent]
    max_tokens: Optional[int] = None


class OptimizationRequest(BaseModel):
    text: str
    limit: int
    strategy: str = Field(..., pattern="^prune_middle$")


class CompilationResponse(BaseModel):
    system_prompt: str
    token_count: int
    warnings: List[str] = []


class OptimizationResponse(BaseModel):
    text: str


def prune_middle(text: str, limit: int, encoding: Encoding) -> str:
    tokens = encoding.encode(text)
    if len(tokens) <= limit:
        return text

    # If limit is very small (e.g. 0 or 1), handle gracefully
    if limit <= 0:
        return ""

    # Calculate how many tokens to keep at start and end
    # We want start + end = limit

    start_count = (limit + 1) // 2
    end_count = limit - start_count

    start_tokens = tokens[:start_count]
    end_tokens = tokens[-end_count:] if end_count > 0 else []

    # Cast to str explicitly if mypy complains, but Encoding.decode usually returns str
    decoded: str = encoding.decode(start_tokens + end_tokens)
    return decoded


class ConstructServer:
    def handle_request(self, request: BlueprintRequest, context: UserContext) -> CompilationResponse:
        weaver = Weaver(context_data=request.variables)

        # Use identity-aware methods
        weaver.create_construct(name="request_construct", components=request.components, context=context)

        # Prepare variables to include user_input if needed by resolve_construct logic
        resolve_vars = request.variables.copy()
        if "user_input" not in resolve_vars:
            resolve_vars["user_input"] = request.user_input

        # Inject max_tokens into variables so resolve_construct can pick it up
        if request.max_tokens is not None:
            resolve_vars["max_tokens"] = request.max_tokens

        try:
            config = weaver.resolve_construct(construct_id="request_construct", variables=resolve_vars, context=context)
        except jinja2.exceptions.UndefinedError as e:
            raise HTTPException(status_code=400, detail=f"Missing variable in template: {e}") from e

        encoding = tiktoken.get_encoding("cl100k_base")
        token_count = len(encoding.encode(config.system_message))

        return CompilationResponse(
            system_prompt=config.system_message, token_count=token_count, warnings=config.dropped_components
        )


server = ConstructServer()


def get_current_user_context() -> UserContext:
    # In a real app, this would parse headers/tokens.
    # For now, we simulate a default user.
    return UserContext(
        user_id="http-user", email="http@coreason.ai", groups=["http"], scopes=[], claims={"source": "http"}
    )


@app.post("/v1/compile", response_model=CompilationResponse)
async def compile_blueprint(
    request: BlueprintRequest,
    context: UserContext = Depends(get_current_user_context),  # noqa: B008
) -> CompilationResponse:
    return server.handle_request(request, context)


@app.post("/v1/optimize", response_model=OptimizationResponse)
async def optimize_text(request: OptimizationRequest) -> OptimizationResponse:
    encoding = tiktoken.get_encoding("cl100k_base")
    optimized_text = prune_middle(request.text, request.limit, encoding)

    return OptimizationResponse(text=optimized_text)
