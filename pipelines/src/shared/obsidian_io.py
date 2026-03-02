"""Obsidian vault read/write utilities via ZenML artifact store.

When a ZenML artifact store is active, reads/writes go to the vault/ prefix
in the artifact store (typically S3). Falls back to local filesystem when
no artifact store is configured (dev/testing).
"""

from __future__ import annotations

import logging
import os
import tempfile
from pathlib import Path

import frontmatter

from src.shared.config import VAULT_PREFIX, VAULT_ROOT

logger = logging.getLogger(__name__)

_artifact_store = None
_use_local = None


def _resolve_backend() -> None:
    """Determine whether to use artifact store or local filesystem."""
    global _artifact_store, _use_local

    if _use_local is not None:
        return

    try:
        from zenml.client import Client

        client = Client()
        _artifact_store = client.active_stack.artifact_store
        # Check if the artifact store is remote (S3, GCS, etc.)
        if hasattr(_artifact_store, "path") and _artifact_store.path.startswith("s3://"):
            _use_local = False
            logger.info("Using artifact store for vault I/O: %s", _artifact_store.path)
        else:
            _use_local = True
            logger.info("Artifact store is local, using filesystem vault I/O")
    except Exception:
        _use_local = True
        logger.info("No ZenML artifact store available, using local filesystem")


def get_artifact_store():
    """Return the active ZenML artifact store instance."""
    _resolve_backend()
    return _artifact_store


def _s3_key(key: str) -> str:
    """Return the full S3 path for a vault key.

    ZenML artifact store requires absolute paths within the bucket,
    e.g. 's3://pyzen-obsidian/vault/01-Knowledge/concepts/foo.md'.
    """
    store = get_artifact_store()
    base = store.path.rstrip("/")
    if key.startswith(base):
        return key
    return f"{base}/{key}"


def vault_key(folder: str, filename: str) -> str:
    """Construct a vault key: 'vault/{folder}/{filename}'."""
    return f"{VAULT_PREFIX}/{folder}/{filename}"


def read_note(key: str) -> tuple[dict, str]:
    """Read a markdown note, returning (frontmatter_dict, body_content).

    Args:
        key: Either a vault key ('vault/01-Knowledge/concepts/foo.md')
             or a local path.
    """
    _resolve_backend()

    if _use_local:
        path = Path(key)
        if not path.is_absolute():
            # Strip vault prefix if present for local paths
            rel = key.removeprefix(f"{VAULT_PREFIX}/")
            path = VAULT_ROOT / rel
        post = frontmatter.load(str(path))
        return dict(post.metadata), post.content

    store = get_artifact_store()
    with store.open(_s3_key(key), "r") as f:
        raw = f.read()
    post = frontmatter.loads(raw)
    return dict(post.metadata), post.content


def write_note(key: str, content: str, metadata: dict | None = None) -> str:
    """Write a markdown note with optional frontmatter.

    Args:
        key: Vault key (e.g. 'vault/01-Knowledge/concepts/foo.md')
        content: Markdown body content
        metadata: Optional frontmatter dict

    Returns:
        The key/path where the note was written.
    """
    _resolve_backend()

    post = frontmatter.Post(content, **(metadata or {}))
    text = frontmatter.dumps(post)

    if _use_local:
        path = Path(key)
        if not path.is_absolute():
            rel = key.removeprefix(f"{VAULT_PREFIX}/")
            path = VAULT_ROOT / rel
        path.parent.mkdir(parents=True, exist_ok=True)

        fd, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=".md.tmp")
        try:
            os.write(fd, text.encode("utf-8"))
            os.close(fd)
            os.replace(tmp, str(path))
        except Exception:
            try:
                os.close(fd)
            except OSError:
                pass
            if os.path.exists(tmp):
                os.unlink(tmp)
            raise
        return str(path)

    store = get_artifact_store()
    with store.open(_s3_key(key), "w") as f:
        f.write(text)
    logger.debug("Wrote vault note: %s", key)
    return key


def list_vault_notes(prefix: str = "") -> list[str]:
    """List all .md keys under the vault prefix.

    Args:
        prefix: Optional sub-prefix (e.g. '01-Knowledge/concepts')

    Returns:
        List of full keys (e.g. ['vault/01-Knowledge/concepts/foo.md', ...])
    """
    _resolve_backend()

    search_prefix = f"{VAULT_PREFIX}/{prefix}" if prefix else VAULT_PREFIX

    if _use_local:
        local_dir = VAULT_ROOT / prefix if prefix else VAULT_ROOT
        if not local_dir.exists():
            return []
        return [
            f"{VAULT_PREFIX}/{p.relative_to(VAULT_ROOT)}"
            for p in local_dir.rglob("*.md")
        ]

    store = get_artifact_store()
    try:
        all_keys = store.listdir(_s3_key(search_prefix))
        base = store.path.rstrip("/") + "/"
        return [
            k.removeprefix(base) if k.startswith(base) else
            f"{search_prefix}/{k}" if not k.startswith(search_prefix) else k
            for k in all_keys
            if k.endswith(".md")
        ]
    except Exception:
        logger.warning("Failed to list vault notes at prefix: %s", search_prefix)
        return []


def search_vault_by_tags(tags: list[str]) -> list[str]:
    """Find vault notes that contain any of the given tags."""
    results: list[str] = []
    for key in list_vault_notes():
        try:
            meta, _ = read_note(key)
            note_tags = meta.get("tags", [])
            if isinstance(note_tags, str):
                note_tags = [note_tags]
            if any(t in note_tags for t in tags):
                results.append(key)
        except Exception:
            continue
    return results


def search_vault_by_type(note_type: str) -> list[str]:
    """Find vault notes with a specific 'type' in frontmatter."""
    results: list[str] = []
    for key in list_vault_notes():
        try:
            meta, _ = read_note(key)
            if meta.get("type") == note_type:
                results.append(key)
        except Exception:
            continue
    return results


def note_exists(key: str) -> bool:
    """Check if a note exists in the vault."""
    _resolve_backend()

    if _use_local:
        path = Path(key)
        if not path.is_absolute():
            rel = key.removeprefix(f"{VAULT_PREFIX}/")
            path = VAULT_ROOT / rel
        return path.exists()

    store = get_artifact_store()
    try:
        return store.exists(_s3_key(key))
    except Exception:
        return False


def generate_wikilink(title: str) -> str:
    """Generate an Obsidian wikilink from a title."""
    return f"[[{title}]]"
