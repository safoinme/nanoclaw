"""Custom ZenML materializer for VaultNote.

Dual-writes: JSON to ZenML artifact store (standard) + markdown to vault prefix.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from zenml.enums import ArtifactType, VisualizationType
from zenml.materializers.base_materializer import BaseMaterializer

from src.shared.config import vault_key
from src.shared.obsidian_io import write_note
from src.shared.schemas import VaultNote

logger = logging.getLogger(__name__)


class VaultNoteMaterializer(BaseMaterializer):
    """Materializer that saves VaultNote as JSON artifact + markdown in vault."""

    ASSOCIATED_TYPES = (VaultNote,)
    ASSOCIATED_ARTIFACT_TYPE = ArtifactType.DATA

    def load(self, data_type: type[VaultNote]) -> VaultNote:
        """Load VaultNote from JSON in the artifact store."""
        with self.artifact_store.open(self.uri + "/data.json", "r") as f:
            data = json.load(f)
        return VaultNote.model_validate(data)

    def save(self, note: VaultNote) -> None:
        """Save VaultNote as JSON artifact and markdown to vault."""
        # Inject ZenML context into the note
        try:
            from zenml import get_step_context

            ctx = get_step_context()
            note.zenml_run_id = str(ctx.pipeline_run.id)
        except Exception:
            pass

        # 1. Write JSON to standard ZenML artifact path
        data = note.model_dump(mode="json")
        with self.artifact_store.open(self.uri + "/data.json", "w") as f:
            json.dump(data, f, indent=2)

        # 2. Write markdown to vault prefix
        key = vault_key(note.folder, f"{note.slug}.md")
        frontmatter_dict = {
            "title": note.title,
            "type": note.note_type.value,
            "status": note.status.value,
            "confidence": note.confidence.value,
            "tags": note.tags,
            "wikilinks": note.wikilinks,
            "zenml_run_id": note.zenml_run_id,
        }
        if note.source_url:
            frontmatter_dict["source_url"] = note.source_url
        if note.source_title:
            frontmatter_dict["source_title"] = note.source_title

        try:
            write_note(key, note.content, frontmatter_dict)
            logger.info("Vault note written: %s", key)
        except Exception:
            logger.exception("Failed to write vault note: %s", key)

    def save_visualizations(self, note: VaultNote) -> dict[str, VisualizationType]:
        """Generate HTML preview for ZenML dashboard."""
        tags_html = " ".join(f'<span style="background:#e0e7ff;padding:2px 6px;border-radius:4px;font-size:12px">#{t}</span>' for t in note.tags)
        links_html = " ".join(f'<span style="background:#fef3c7;padding:2px 6px;border-radius:4px;font-size:12px">{wl}</span>' for wl in note.wikilinks)

        html = f"""<div style="font-family:system-ui;max-width:600px">
<h3>{note.title}</h3>
<p><strong>Type:</strong> {note.note_type.value} | <strong>Status:</strong> {note.status.value} | <strong>Confidence:</strong> {note.confidence.value}</p>
<p><strong>Folder:</strong> {note.folder}</p>
{f'<p><strong>Tags:</strong> {tags_html}</p>' if tags_html else ''}
{f'<p><strong>Links:</strong> {links_html}</p>' if links_html else ''}
<hr>
<pre style="white-space:pre-wrap;font-size:13px">{note.content[:2000]}</pre>
</div>"""

        viz_uri = self.uri + "/visualization.html"
        with self.artifact_store.open(viz_uri, "w") as f:
            f.write(html)
        return {viz_uri: VisualizationType.HTML}

    def extract_metadata(self, note: VaultNote) -> dict[str, Any]:
        """Return queryable metadata dict."""
        return {
            "title": note.title,
            "type": note.note_type.value,
            "folder": note.folder,
            "status": note.status.value,
            "confidence": note.confidence.value,
            "tags": note.tags,
            "wikilinks_count": len(note.wikilinks),
            "word_count": len(note.content.split()),
            "slug": note.slug,
        }
