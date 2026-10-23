"""kalle — adversarial peer review pipeline for academic PDFs."""

from kalle.core import call_llm
from kalle.pipeline import PipelineError, run
from kalle.render_text import render_text

__version__ = "2.0.0"
__all__ = [
    "call_llm",
    "render_text",
    "run",
    "PipelineError",
    "__version__",
]
