"""Approval routing – for now just logs; future: Slack/Telegram/email hooks."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


class ApprovalRouter:
    """Route draft notifications to the approval channel."""

    async def notify_draft_ready(self, draft_id: int, title: str, preview_url: str) -> None:
        """Notify the reviewer that a draft is ready.

        MVP: logs to stdout. Future: send Slack message, email, or Telegram.
        """
        logger.info(
            "DRAFT READY FOR REVIEW | id=%d | title='%s' | review_url=%s",
            draft_id,
            title[:80],
            preview_url,
        )
        # TODO: integrate Slack webhook
        # TODO: integrate Telegram bot
        # TODO: integrate email notification
