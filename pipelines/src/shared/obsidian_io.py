"""Obsidian vault read/write utilities."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import frontmatter

from src.shared.config import VAULT_ROOT


def read_note(path: str | Path) -> tuple[dict, str]:
    """Read a note, returning (frontmatter_dict, body_content)."""
    path = Path(path)
    if not path.is_absolute():
        path = VAULT_ROOT / path
    post = frontmatter.load(str(path))
    return dict(post.metadata), post.content


def write_note(
    path: str | Path,
    content: str,
    metadata: dict | None = None,
) -> Path:
    """Write a note atomically (temp + rename). Creates parent dirs."""
    path = Path(path)
    if not path.is_absolute():
        path = VAULT_ROOT / path
    path.parent.mkdir(parents=True, exist_ok=True)

    post = frontmatter.Post(content, **(metadata or {}))
    text = frontmatter.dumps(post)

    # Atomic write: temp file in same dir, then rename
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=".md.tmp")
    try:
        os.write(fd, text.encode("utf-8"))
        os.close(fd)
        os.replace(tmp, str(path))
    except Exception:
        os.close(fd) if not os.get_inheritable(fd) else None
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise
    return path


def generate_wikilink(title: str) -> str:
    """Generate an Obsidian wikilink from a title."""
    return f"[[{title}]]"


def search_vault_by_tags(
    tags: list[str],
    root: Path | None = None,
) -> list[Path]:
    """Find notes that contain any of the given tags."""
    root = root or VAULT_ROOT
    results: list[Path] = []
    for md_file in root.rglob("*.md"):
        try:
            meta, _ = read_note(md_file)
            note_tags = meta.get("tags", [])
            if isinstance(note_tags, str):
                note_tags = [note_tags]
            if any(t in note_tags for t in tags):
                results.append(md_file)
        except Exception:
            continue
    return results


def search_vault_by_type(
    note_type: str,
    root: Path | None = None,
) -> list[Path]:
    """Find notes with a specific 'type' in frontmatter."""
    root = root or VAULT_ROOT
    results: list[Path] = []
    for md_file in root.rglob("*.md"):
        try:
            meta, _ = read_note(md_file)
            if meta.get("type") == note_type:
                results.append(md_file)
        except Exception:
            continue
    return results


def list_inbox_notes(inbox_path: Path | None = None) -> list[Path]:
    """List all markdown files in the inbox folder."""
    inbox = inbox_path or (VAULT_ROOT / "00-Inbox")
    if not inbox.exists():
        return []
    return sorted(inbox.glob("*.md"))
