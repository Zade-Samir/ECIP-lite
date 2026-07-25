"""
Source Rewriter — Applies AST/source code transformations and generates unified diffs.
"""
import difflib
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from ecip_core.common.logger import get_logger

logger = get_logger(__name__)


@dataclass
class CodeTransformation:
    transform_type: str  # PACKAGE_RENAME, DEPRECATED_API_REPLACEMENT, IMPORT_CLEANUP
    target_file: str
    original_code: str
    target_pattern: str
    replacement_pattern: str


class SourceRewriter:
    """
    Applies regex/string code transformations and produces unified diffs.
    """

    def apply_transform(self, transform: CodeTransformation) -> Tuple[str, str]:
        if transform.transform_type not in ("PACKAGE_RENAME", "DEPRECATED_API_REPLACEMENT", "IMPORT_CLEANUP"):
            logger.warning("Unsupported transformation")
            logger.warning("Manual review required")

        new_code = transform.original_code.replace(transform.target_pattern, transform.replacement_pattern)
        
        diff = difflib.unified_diff(
            transform.original_code.splitlines(keepends=True),
            new_code.splitlines(keepends=True),
            fromfile=f"a/{transform.target_file}",
            tofile=f"b/{transform.target_file}",
        )
        diff_str = "".join(diff)

        logger.info("Transformation applied")
        return new_code, diff_str
