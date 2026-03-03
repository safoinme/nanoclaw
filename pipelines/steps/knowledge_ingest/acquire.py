"""Acquire raw content from URL, PDF, or text."""

import base64
import logging

import httpx
from zenml import step

logger = logging.getLogger(__name__)


def _extract_from_html(html: str) -> str:
    """Extract readable text from HTML using readability-lxml."""
    from readability import Document

    doc = Document(html)
    # Get the readable HTML, then strip tags for plain text
    readable_html = doc.summary()

    # Simple HTML tag stripping
    import re

    text = re.sub(r"<[^>]+>", "\n", readable_html)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _process_pdf_in_sandbox(pdf_b64: str) -> str:
    """Process a base64-encoded PDF in an E2B sandbox."""
    from e2b_code_interpreter import Sandbox

    from src.shared.config import E2B_API_KEY

    code = f"""
import base64
import fitz  # PyMuPDF

pdf_bytes = base64.b64decode("{pdf_b64}")
doc = fitz.open(stream=pdf_bytes, filetype="pdf")
text_parts = []
for page in doc:
    text_parts.append(page.get_text())
print("\\n\\n".join(text_parts))
"""
    sbx = Sandbox(api_key=E2B_API_KEY)
    try:
        result = sbx.run_code(code)
        if result.error:
            raise RuntimeError(f"Sandbox error: {result.error}")
        return "\n".join(line.text for line in result.logs.stdout)
    finally:
        sbx.kill()


@step(enable_cache=False, retry={"max_retries": 3, "delay": 5, "backoff": 2})
def acquire(content: str, content_type: str, source_title: str) -> dict:
    """Acquire and normalize raw content.

    Args:
        content: URL string, base64 PDF, or raw text
        content_type: 'url', 'pdf_b64', 'text', or 'conversation'
        source_title: Human-readable source title

    Returns:
        Dict with 'text', 'source_title', 'source_url', 'content_type'
    """
    result = {
        "text": "",
        "source_title": source_title,
        "source_url": "",
        "content_type": content_type,
    }

    if content_type == "url":
        result["source_url"] = content
        logger.info("Fetching URL: %s", content)
        resp = httpx.get(content, follow_redirects=True, timeout=30)
        resp.raise_for_status()

        ct = resp.headers.get("content-type", "")
        if "pdf" in ct:
            pdf_b64 = base64.b64encode(resp.content).decode()
            result["text"] = _process_pdf_in_sandbox(pdf_b64)
        else:
            result["text"] = _extract_from_html(resp.text)

        if not source_title:
            from readability import Document

            doc = Document(resp.text)
            result["source_title"] = doc.short_title() or content

    elif content_type == "pdf_b64":
        logger.info("Processing base64 PDF")
        result["text"] = _process_pdf_in_sandbox(content)

    elif content_type in ("text", "conversation"):
        result["text"] = content.strip()

    else:
        raise ValueError(f"Unknown content_type: {content_type}")

    word_count = len(result["text"].split())
    logger.info("Acquired %d words from %s", word_count, content_type)
    return result
