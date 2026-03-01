"""Pipeline: Document Processor — process files in E2B sandbox.

On-demand: triggered via snapshot.

DAG:
  receive_document --> process_in_sandbox --> summarize_document
"""

from __future__ import annotations

from zenml import pipeline

from steps.process_in_sandbox import process_in_sandbox
from steps.receive_document import receive_document
from steps.summarize_document import summarize_document


@pipeline(tags=["document", "on-demand"])
def document_processor(file_path: str = "") -> None:
    """Receive file, process in E2B sandbox, summarize, save to vault."""
    doc_path = receive_document(file_path=file_path)
    processed = process_in_sandbox(document_path=doc_path)
    summarize_document(processed_doc=processed)
