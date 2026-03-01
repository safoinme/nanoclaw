"""Step: Process a document in an E2B sandbox."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Annotated

from zenml import step
from zenml.utils.metadata_utils import log_metadata

from src.shared.schemas import ProcessedDocument

logger = logging.getLogger(__name__)


@step
def process_in_sandbox(
    document_path: Path,
) -> Annotated[ProcessedDocument, "processed_doc"]:
    """Process document in E2B Code Interpreter sandbox."""
    from e2b_code_interpreter import Sandbox

    from src.shared.config import E2B_API_KEY

    file_type = document_path.suffix.lstrip(".")
    content_bytes = document_path.read_bytes()

    sbx = Sandbox(api_key=E2B_API_KEY)
    try:
        # Upload file to sandbox
        remote_path = f"/tmp/{document_path.name}"
        sbx.files.write(remote_path, content_bytes)

        # Extract text based on file type
        if file_type == "pdf":
            code = f"""
import subprocess
subprocess.run(["pip", "install", "pymupdf"], capture_output=True)
import fitz
doc = fitz.open("{remote_path}")
text = "\\n".join(page.get_text() for page in doc)
print(text[:5000])
"""
        elif file_type in ("csv", "xlsx"):
            code = f"""
import subprocess
subprocess.run(["pip", "install", "pandas", "openpyxl"], capture_output=True)
import pandas as pd
df = pd.read_{'csv' if file_type == 'csv' else 'excel'}("{remote_path}")
print(f"Shape: {{df.shape}}")
print(f"Columns: {{list(df.columns)}}")
print(df.head(20).to_string())
"""
        else:
            code = f"""
with open("{remote_path}", "r", errors="replace") as f:
    text = f.read()
print(text[:5000])
"""

        execution = sbx.run_code(code)
        extracted_text = ""
        for log in execution.logs.stdout:
            extracted_text += log

        log_metadata({"file_type": file_type, "extracted_length": len(extracted_text)})
    finally:
        sbx.kill()

    return ProcessedDocument(
        original_path=str(document_path),
        file_type=file_type,
        summary=extracted_text[:500],
        key_points=[],
    )
