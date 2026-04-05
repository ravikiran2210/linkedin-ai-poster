"""Draft review and approval API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import ApprovalResponse, DraftDetail, DraftSummary, PipelineResponse
from app.storage.db import get_session
from app.storage.repositories.post_repo import DraftPostRepo
from app.workflows.approval_pipeline import ApprovalPipeline
from app.workflows.daily_pipeline import DailyPipeline

router = APIRouter(tags=["review"])


@router.get("/drafts", response_model=list[DraftSummary])
async def list_drafts(session: AsyncSession = Depends(get_session)):
    """List all pending draft posts."""
    repo = DraftPostRepo(session)
    drafts = await repo.list_pending()
    return [
        DraftSummary(
            id=d.id,
            candidate_id=d.candidate_id,
            hook=d.hook,
            status=d.status,
            hashtags=d.hashtags,
            created_at=d.created_at,
        )
        for d in drafts
    ]


@router.get("/drafts/{draft_id}", response_model=DraftDetail)
async def get_draft(draft_id: int, session: AsyncSession = Depends(get_session)):
    """Get full details of a specific draft."""
    repo = DraftPostRepo(session)
    draft = await repo.get_by_id(draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")

    candidate = draft.candidate
    return DraftDetail(
        id=draft.id,
        candidate_id=draft.candidate_id,
        hook=draft.hook,
        body=draft.body,
        cta=draft.cta,
        full_caption=draft.full_caption,
        hashtags=draft.hashtags,
        image_strategy=draft.image_strategy,
        status=draft.status,
        created_at=draft.created_at,
        updated_at=draft.updated_at,
        topic=candidate.topic if candidate else None,
        title=candidate.normalized_title if candidate else None,
        score=candidate.final_score if candidate else None,
    )


@router.post("/approve/{draft_id}", response_model=ApprovalResponse)
async def approve_draft(draft_id: int):
    """Approve a draft and publish it to LinkedIn."""
    pipeline = ApprovalPipeline()
    result = await pipeline.approve_and_publish(draft_id)

    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])

    return ApprovalResponse(
        status=result["status"],
        draft_id=draft_id,
        linkedin_url=result.get("linkedin_url"),
        message="Post published successfully" if result["status"] == "published" else "",
    )


@router.post("/reject/{draft_id}", response_model=ApprovalResponse)
async def reject_draft(draft_id: int):
    """Reject a draft post."""
    pipeline = ApprovalPipeline()
    result = await pipeline.reject(draft_id)

    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])

    return ApprovalResponse(
        status="rejected",
        draft_id=draft_id,
        message="Draft rejected",
    )


@router.post("/pipeline/run", response_model=PipelineResponse)
async def trigger_pipeline():
    """Manually trigger the daily pipeline."""
    pipeline = DailyPipeline()
    result = await pipeline.run()
    return PipelineResponse(**result)
