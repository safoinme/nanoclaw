"""Step: Receive a document file path for processing."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Annotated

from zenml import step

logger = logging.getLogger(__name__)


@step
def receive_document(file_path: str) -> Annotated[Path, "document_path"]:
    """Validate and return the document path."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Document not found: {file_path}")
    logger.info("Received document: %s (%d bytes)", path.name, path.stat().st_size)
    return path
