"""Agent outer loop hooks for knowledge ingest steps.

on_failure logs error metadata so re-running the pipeline with caching
skips already-succeeded steps and only retries the failed ones.
"""

from zenml import get_step_context
from zenml.utils.metadata_utils import log_metadata


def on_step_failure(exception: BaseException) -> None:
    """Log failure details to ZenML metadata for the monitoring agent."""
    try:
        ctx = get_step_context()
        log_metadata({
            "failure_error": str(exception),
            "failure_type": type(exception).__name__,
            "step_name": ctx.step_run.name,
            "pipeline_run_id": str(ctx.pipeline_run.id),
        })
    except RuntimeError:
        pass


def on_step_success() -> None:
    """Log success confirmation to metadata."""
    try:
        ctx = get_step_context()
        log_metadata({"completed": True})
    except RuntimeError:
        pass
