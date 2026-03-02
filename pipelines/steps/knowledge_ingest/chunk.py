"""Split raw content into chunks for concept extraction."""

import re

from zenml import step

from src.shared.schemas import ContentChunk


def _split_on_headers(text: str) -> list[tuple[str, str]]:
    """Split text on markdown headers, returning (section_title, body) pairs."""
    # Match lines starting with 1-6 #'s
    header_pattern = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)

    sections: list[tuple[str, str]] = []
    last_end = 0
    last_title = ""

    for match in header_pattern.finditer(text):
        # Capture text before this header
        if last_end < match.start():
            body = text[last_end : match.start()].strip()
            if body:
                sections.append((last_title, body))
        last_title = match.group(2).strip()
        last_end = match.end()

    # Capture remaining text
    remaining = text[last_end:].strip()
    if remaining:
        sections.append((last_title, remaining))

    # If no headers found, return the whole text
    if not sections and text.strip():
        sections = [("", text.strip())]

    return sections


@step(enable_cache=True)
def chunk(raw: dict, max_chunk_words: int = 500) -> list[dict]:
    """Split raw content into chunks.

    Splits on markdown headers first, then merges small sections up to
    max_chunk_words. Returns dicts (not ContentChunk) to avoid Pydantic
    class-identity issues across ZenML step boundaries.
    """
    text = raw.get("text", "")
    if not text:
        return []

    sections = _split_on_headers(text)

    chunks: list[dict] = []
    current_text = ""
    current_section = ""

    for title, body in sections:
        words_in_body = len(body.split())

        # If adding this section would exceed the limit, flush current
        if current_text and len(current_text.split()) + words_in_body > max_chunk_words:
            chunks.append(
                ContentChunk(
                    text=current_text.strip(),
                    chunk_index=len(chunks),
                    source_section=current_section,
                    word_count=len(current_text.split()),
                ).model_dump()
            )
            current_text = ""
            current_section = ""

        # If a single section is larger than max, add it directly
        if not current_text and words_in_body > max_chunk_words:
            # Split on paragraphs
            paragraphs = re.split(r"\n\n+", body)
            para_buf = ""
            for para in paragraphs:
                if para_buf and len(para_buf.split()) + len(para.split()) > max_chunk_words:
                    chunks.append(
                        ContentChunk(
                            text=para_buf.strip(),
                            chunk_index=len(chunks),
                            source_section=title,
                            word_count=len(para_buf.split()),
                        ).model_dump()
                    )
                    para_buf = ""
                para_buf += "\n\n" + para if para_buf else para

            if para_buf.strip():
                current_text = para_buf
                current_section = title
        else:
            if title:
                current_text += f"\n\n## {title}\n\n{body}" if current_text else f"## {title}\n\n{body}"
            else:
                current_text += f"\n\n{body}" if current_text else body
            if not current_section:
                current_section = title

    # Flush remaining
    if current_text.strip():
        chunks.append(
            ContentChunk(
                text=current_text.strip(),
                chunk_index=len(chunks),
                source_section=current_section,
                word_count=len(current_text.split()),
            ).model_dump()
        )

    return chunks
