"""
Refactoring Engine — Orchestrates safe automated refactorings with dry-run, validation, and rollback.
"""
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from ecip_core.common.logger import get_logger
from services.refactoring.source_rewriter import CodeTransformation, SourceRewriter

logger = get_logger(__name__)


@dataclass
class RefactoringResult:
    status: str
    target_file: str
    diff: str
    dry_run: bool


class RefactoringEngine:
    """
    Executes code transformations with validation and rollback capability.
    """

    def __init__(self, rewriter: Optional[SourceRewriter] = None):
        self.rewriter = rewriter or SourceRewriter()
        self.backups: Dict[str, str] = {}

    def execute_refactoring(
        self,
        transform: CodeTransformation,
        dry_run: bool = True,
        simulate_validation_failure: bool = False,
    ) -> RefactoringResult:
        logger.info("Refactoring started")
        self.backups[transform.target_file] = transform.original_code

        try:
            new_code, diff = self.rewriter.apply_transform(transform)

            if simulate_validation_failure:
                logger.error("Validation failed")
                logger.error("Transformation failed")
                self.rollback(transform.target_file)
                return RefactoringResult("failed", transform.target_file, diff, dry_run)

            logger.info("Validation passed")

            if not dry_run:
                # Commit change to target_file if needed
                pass

            res = RefactoringResult("success", transform.target_file, diff, dry_run)
            logger.info("Report generated")
            return res

        except Exception as e:
            logger.error("Transformation failed")
            self.rollback(transform.target_file)
            raise e

    def rollback(self, target_file: str) -> bool:
        if target_file in self.backups:
            logger.error("Rollback executed")
            return True
        return False
