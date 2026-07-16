import os
import time
from typing import List, Optional
from ecip_core.common.logger import get_logger
from ecip_core.output.models.formatted_response import FormattedResponse
from ecip_core.query.models.coordinator_response import CoordinatorResponse
from ecip_core.citations.models.citation import Citation

logger = get_logger(__name__)

# ANSI colour codes
_ANSI_ENABLED = os.environ.get("NO_COLOR", "") == "" and os.environ.get("ECIP_NO_COLOR", "") == ""

_RESET  = "\033[0m"   if _ANSI_ENABLED else ""
_BOLD   = "\033[1m"   if _ANSI_ENABLED else ""
_DIM    = "\033[2m"   if _ANSI_ENABLED else ""
_CYAN   = "\033[96m"  if _ANSI_ENABLED else ""
_GREEN  = "\033[92m"  if _ANSI_ENABLED else ""
_YELLOW = "\033[93m"  if _ANSI_ENABLED else ""
_RED    = "\033[91m"  if _ANSI_ENABLED else ""

_DIVIDER = "─" * 60


class ResponseFormatter:
    """
    Converts a CoordinatorResponse into a consistently formatted,
    human-readable CLI output.

    Rendering is completely separate from business logic — the formatter
    never modifies inference data, only presents it.
    """

    def __init__(self, ansi: bool = _ANSI_ENABLED):
        self._ansi = ansi
        self._reset  = "\033[0m"   if ansi else ""
        self._bold   = "\033[1m"   if ansi else ""
        self._dim    = "\033[2m"   if ansi else ""
        self._cyan   = "\033[96m"  if ansi else ""
        self._green  = "\033[92m"  if ansi else ""
        self._yellow = "\033[93m"  if ansi else ""
        self._red    = "\033[91m"  if ansi else ""

    # ─── Public API ───────────────────────────────────────────────────────

    def format(
        self,
        response: CoordinatorResponse,
        question: str = "",
        duration_ms: float = 0.0,
        warnings: Optional[List[str]] = None
    ) -> FormattedResponse:
        """
        Main entry point. Accepts a CoordinatorResponse and returns
        a FormattedResponse with a rendered string ready for printing.
        """
        logger.info("Formatting started")

        try:
            if not response.answer or not response.answer.strip():
                logger.warning("Empty answer received")

            citations_text = self._format_citations(response.citations)

            if not citations_text:
                logger.warning("Empty citations")

            rendered = self._render(
                question=question,
                answer=response.answer,
                intent=response.intent.intent if response.intent else "",
                citations_text=citations_text,
                warnings=warnings or [],
                model=response.model,
                duration_ms=duration_ms,
                retrieved_chunks=len(response.citations)
            )

            result = FormattedResponse(
                question=question,
                answer=response.answer,
                intent=response.intent.intent if response.intent else "",
                citations_text=citations_text,
                warnings=warnings or [],
                model=response.model,
                duration_ms=duration_ms,
                retrieved_chunks=len(response.citations),
                rendered=rendered
            )

            logger.info("Formatting completed")
            return result

        except Exception as e:
            logger.error(f"Rendering failure: {e}")
            raise

    # ─── Internal rendering helpers ───────────────────────────────────────

    def _format_citations(self, citations: list) -> List[str]:
        """Convert citation objects (Citation or HybridResult) into display strings."""
        lines = []
        for c in citations:
            if isinstance(c, Citation):
                fname = c.file_path.split("/")[-1]
                method = f" › {c.method_name}" if c.method_name else ""
                conf   = f"  ({c.confidence:.0%})" if c.confidence else ""
                lines.append(f"{fname}{method}  L{c.start_line}–{c.end_line}{conf}")
            else:
                # HybridResult fallback
                fname = getattr(c, "file_path", "").split("/")[-1]
                method = getattr(c, "method_name", "")
                s = getattr(c, "start_line", 0)
                e = getattr(c, "end_line", 0)
                method_part = f" › {method}" if method else ""
                lines.append(f"{fname}{method_part}  L{s}–{e}")
        return lines

    def _section(self, title: str) -> str:
        return f"\n{self._cyan}{self._bold}{title}{self._reset}\n{self._dim}{_DIVIDER}{self._reset}"

    def _render(
        self,
        question: str,
        answer: str,
        intent: str,
        citations_text: List[str],
        warnings: List[str],
        model: str,
        duration_ms: float,
        retrieved_chunks: int
    ) -> str:
        parts = []

        # ── Question ──────────────────────────────────────────────────────
        if question:
            parts.append(
                f"\n{self._bold}{self._cyan}Q:{self._reset} {question}"
            )
            parts.append(f"{self._dim}{_DIVIDER}{self._reset}")

        # ── Answer ────────────────────────────────────────────────────────
        answer_text = answer.strip() if answer else f"{self._yellow}(no answer){self._reset}"
        parts.append(f"\n{answer_text}\n")

        # ── Warnings ──────────────────────────────────────────────────────
        if warnings:
            parts.append(self._section("⚠  Warnings"))
            for w in warnings:
                parts.append(f"  {self._yellow}• {w}{self._reset}")

        # ── Citations ─────────────────────────────────────────────────────
        parts.append(self._section("📎 Citations"))
        if citations_text:
            for line in citations_text:
                parts.append(f"  {self._green}▸{self._reset} {line}")
        else:
            parts.append(f"  {self._dim}(no source citations){self._reset}")

        # ── Execution Stats ───────────────────────────────────────────────
        parts.append(self._section("⚙  Execution"))
        parts.append(f"  Model            : {self._bold}{model}{self._reset}")
        parts.append(f"  Intent           : {intent}")
        duration_label = (
            f"{duration_ms:.0f} ms" if duration_ms < 1000
            else f"{duration_ms/1000:.2f} s"
        )
        parts.append(f"  Duration         : {duration_label}")
        parts.append(f"  Retrieved chunks : {retrieved_chunks}")
        parts.append(f"\n{self._dim}{_DIVIDER}{self._reset}\n")

        return "\n".join(parts)

    def format_stream_footer(
        self,
        response: CoordinatorResponse,
        duration_ms: float,
        warnings: Optional[List[str]] = None
    ) -> str:
        """
        Formats only the citations, warnings, and execution metrics.
        Used when the main answer text has already been streamed.
        """
        logger.info("Formatting stream footer started")
        citations_text = self._format_citations(response.citations)
        parts = []

        # ── Warnings ──────────────────────────────────────────────────────
        if warnings:
            parts.append(self._section("⚠  Warnings"))
            for w in warnings:
                parts.append(f"  {self._yellow}• {w}{self._reset}")

        # ── Citations ─────────────────────────────────────────────────────
        parts.append(self._section("📎 Citations"))
        if citations_text:
            for line in citations_text:
                parts.append(f"  {self._green}▸{self._reset} {line}")
        else:
            parts.append(f"  {self._dim}(no source citations){self._reset}")

        # ── Execution Stats ───────────────────────────────────────────────
        parts.append(self._section("⚙  Execution"))
        parts.append(f"  Model            : {self._bold}{response.model}{self._reset}")
        intent = response.intent.intent if response.intent else ""
        parts.append(f"  Intent           : {intent}")
        duration_label = (
            f"{duration_ms:.0f} ms" if duration_ms < 1000
            else f"{duration_ms/1000:.2f} s"
        )
        parts.append(f"  Duration         : {duration_label}")
        parts.append(f"  Retrieved chunks : {len(response.citations)}")
        parts.append(f"\n{self._dim}{_DIVIDER}{self._reset}\n")

        logger.info("Formatting stream footer completed")
        return "\n".join(parts)
