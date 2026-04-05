"""Send a plain-text/HTML digest of fetched feeds via SMTP (e.g. Gmail App Password)."""

from __future__ import annotations

import asyncio
import html
import logging
import smtplib
from email.message import EmailMessage

from app.collectors.base import CollectedItem
from app.config import settings

logger = logging.getLogger(__name__)

_CONTENT_PREVIEW = 400


def _preview(content: str | None) -> str:
    if not content:
        return ""
    text = " ".join(content.split())
    if len(text) <= _CONTENT_PREVIEW:
        return text
    return text[: _CONTENT_PREVIEW - 3] + "..."


def build_digest_bodies(
    *,
    run_label: str,
    collected: list[CollectedItem],
    new_count: int,
    newly_stored: list[dict[str, str]],
    selected_summary: dict | None,
    published: bool,
) -> tuple[str, str]:
    """Return (plain, html) email bodies."""
    lines: list[str] = [
        f"LinkedIn AI Poster — fetch digest ({run_label})",
        "",
        f"Total items seen from feeds this run: {len(collected)}",
        f"New rows saved to the database (not duplicates): {new_count}",
        "",
    ]
    if selected_summary:
        lines.extend(
            [
                "Selected for this run:",
                f"  Title: {selected_summary.get('title', '')}",
                f"  Topic: {selected_summary.get('topic', '')}",
                f"  Score: {selected_summary.get('score', 0):.3f}",
                f"  Auto-published: {'yes' if published else 'no'}",
                "",
            ]
        )
    else:
        lines.extend(["No candidate was selected for posting this run.", ""])

    lines.append("— All items collected this run (every feed entry) —")
    lines.append("")
    for i, item in enumerate(collected, start=1):
        lines.append(f"{i}. [{item.source_name}] {item.title}")
        lines.append(f"   URL: {item.url}")
        prev = _preview(item.content)
        if prev:
            lines.append(f"   Preview: {prev}")
        lines.append("")

    if newly_stored:
        lines.append("— Newly stored (first time in DB) —")
        lines.append("")
        for row in newly_stored:
            lines.append(f"* {row['title']}")
            lines.append(f"  {row['url']} ({row['source']})")
            lines.append("")
    else:
        lines.append("— No new database rows (everything was already seen). —")
        lines.append("")

    plain = "\n".join(lines)

    rows_html = []
    for i, item in enumerate(collected, start=1):
        prev = _preview(item.content)
        rows_html.append(
            "<tr>"
            f"<td>{i}</td>"
            f"<td>{html.escape(item.source_name)}</td>"
            f"<td>{html.escape(item.title)}<br/>"
            f'<a href="{html.escape(item.url)}">{html.escape(item.url)}</a>'
            f"{'<br/><small>' + html.escape(prev) + '</small>' if prev else ''}"
            "</td>"
            "</tr>"
        )

    new_rows_html = ""
    if newly_stored:
        new_rows_html = "<h3>Newly stored in DB</h3><ul>" + "".join(
            f"<li>{html.escape(r['title'])} — {html.escape(r['source'])}<br/>"
            f'<a href="{html.escape(r["url"])}">{html.escape(r["url"])}</a></li>'
            for r in newly_stored
        ) + "</ul>"
    else:
        new_rows_html = "<p><em>No new rows (all items were duplicates).</em></p>"

    sel_block = ""
    if selected_summary:
        sel_block = (
            "<h3>Selected for posting</h3>"
            "<ul>"
            f"<li><strong>Title:</strong> {html.escape(str(selected_summary.get('title', '')))}</li>"
            f"<li><strong>Topic:</strong> {html.escape(str(selected_summary.get('topic', '')))}</li>"
            f"<li><strong>Score:</strong> {selected_summary.get('score', 0):.3f}</li>"
            f"<li><strong>Auto-published:</strong> {'yes' if published else 'no'}</li>"
            "</ul>"
        )
    else:
        sel_block = "<p><em>No candidate selected this run.</em></p>"

    html_body = f"""\
<html>
<body style="font-family: sans-serif;">
<h2>Fetch digest ({html.escape(run_label)})</h2>
<p>Total from feeds: <strong>{len(collected)}</strong><br/>
New in database: <strong>{new_count}</strong></p>
{sel_block}
<h3>All items collected</h3>
<table border="1" cellpadding="6" cellspacing="0" style="border-collapse: collapse; max-width: 100%;">
<tr><th>#</th><th>Source</th><th>Title &amp; link</th></tr>
{"".join(rows_html)}
</table>
{new_rows_html}
</body>
</html>"""

    return plain, html_body


def _digest_configured() -> bool:
    return bool(
        settings.smtp_user.strip()
        and settings.smtp_password.strip()
        and settings.digest_to_email.strip()
    )


def send_digest_sync(
    *,
    subject: str,
    plain_body: str,
    html_body: str,
) -> None:
    """Blocking SMTP send. Call via asyncio.to_thread from async code."""
    if not _digest_configured():
        logger.info("Email digest skipped (set SMTP_USER, SMTP_PASSWORD, DIGEST_TO_EMAIL)")
        return

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = settings.smtp_user
    msg["To"] = settings.digest_to_email
    msg.set_content(plain_body)
    msg.add_alternative(html_body, subtype="html")

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=60) as smtp:
        smtp.starttls()
        smtp.login(settings.smtp_user, settings.smtp_password)
        smtp.send_message(msg)

    logger.info("Sent fetch digest email to %s", settings.digest_to_email)


async def send_daily_digest_async(
    *,
    run_label: str,
    collected: list[CollectedItem],
    new_count: int,
    newly_stored: list[dict[str, str]],
    selected_summary: dict | None,
    published: bool,
) -> None:
    """Send digest if SMTP is configured; never raises (logs errors)."""
    if not _digest_configured():
        return
    plain, html_body = build_digest_bodies(
        run_label=run_label,
        collected=collected,
        new_count=new_count,
        newly_stored=newly_stored,
        selected_summary=selected_summary,
        published=published,
    )
    subject = f"[LinkedIn AI Poster] Fetch digest — {run_label}"
    try:
        await asyncio.to_thread(
            send_digest_sync,
            subject=subject,
            plain_body=plain,
            html_body=html_body,
        )
    except Exception:
        logger.exception("Failed to send digest email")
