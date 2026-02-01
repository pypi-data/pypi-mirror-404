"""Document Generation Workflow Package.

Cost-optimized documentation generation pipeline.

Copyright 2025 Smart-AI-Memory
Licensed under Fair Source License 0.9
"""

# Core workflow
# Configuration
from .config import DOC_GEN_STEPS, TOKEN_COSTS

# Report formatter
from .report_formatter import format_doc_gen_report
from .workflow import DocumentGenerationWorkflow

__all__ = [
    # Workflow
    "DocumentGenerationWorkflow",
    # Configuration
    "DOC_GEN_STEPS",
    "TOKEN_COSTS",
    # Report formatter
    "format_doc_gen_report",
]
