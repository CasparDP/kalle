"""reviewer2 — adversarial peer review pipeline for academic PDFs."""

from reviewer2.core import call_llm
from reviewer2.pipeline import PipelineError, run
from reviewer2.render_text import render_text

__version__ = "1.1.0"
__all__ = [
    "call_llm",
    "render_text",
    "run",
    "PipelineError",
    "__version__",
]
