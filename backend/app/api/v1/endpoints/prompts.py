"""
Prompt analysis API endpoints.

Routes:
    POST /prompts/analyze  → Analyze a natural-language prompt into a
                             structured video brief (topic, audience, mood,
                             characters, style, camera, duration, language,
                             voice).

The heavy lifting lives in PromptAnalyzerService, which depends only on the
LLMProvider abstraction — so the configured model (Gemma/Llama/…) is
irrelevant to this layer.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_current_user
from app.core.exceptions import (
    InvalidInputError,
    LLMProviderError,
    ProviderNotConfiguredError,
)
from app.models.user import User
from app.schemas.common import SuccessResponse
from app.schemas.prompt import PromptAnalysis, PromptAnalyzeRequest
from app.services.prompt_analyzer_service import PromptAnalyzerService

router = APIRouter(prefix="/prompts", tags=["Prompts"])


@router.post(
    "/analyze",
    response_model=SuccessResponse[PromptAnalysis],
    summary="Analyze a natural-language prompt into a structured video brief",
)
async def analyze_prompt(
    payload: PromptAnalyzeRequest,
    current_user: User = Depends(get_current_user),
) -> SuccessResponse[PromptAnalysis]:
    """Analyze a prompt and return the structured brief."""
    try:
        service = PromptAnalyzerService()
        analysis = await service.analyze(payload.prompt)
        return SuccessResponse(data=analysis, message="Prompt analyzed.")
    except InvalidInputError as exc:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, detail=exc.message
        ) from exc
    except ProviderNotConfiguredError as exc:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE, detail=exc.message
        ) from exc
    except LLMProviderError as exc:
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY, detail=exc.message
        ) from exc
