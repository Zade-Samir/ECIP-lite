import re
from ecip_core.common.logger import get_logger
from ecip_core.retrieval.context.models.context import Context
from ecip_core.prompt.models.prompt import Prompt
from ecip_core.inference.config.settings import settings

logger = get_logger(__name__)


class PromptBuilder:
    """
    Builds deterministic, grounded prompts for the LLM.
    """

    def __init__(self, max_tokens: int = 3000):
        self.max_tokens = max_tokens

    def build_prompt(
        self,
        question: str = "",
        context: Context | str = ""
    ) -> Prompt | str:
        """
        Builds a grounded prompt. If context is a Context object, returns a typed Prompt.
        Otherwise, returns a legacy formatted string.
        """
        # Legacy fallback mode
        if isinstance(context, str):
            return f"""You are a Senior Java Architect.

Use the provided project context if available.
If no project context is available, answer using your own knowledge.

{context}

Question:
{question}

Answer:
"""

        # Grounded Prompt Builder Mode
        logger.info("Prompt generation started")

        if not context:
            logger.warning("Missing context section")
            empty_text = self._format_prompt(
                project_name="unknown",
                class_ctx="",
                method_ctx="",
                dep_ctx="",
                citations_str="",
                question=question
            )
            return Prompt(
                prompt_text=empty_text,
                citations=[],
                token_estimate=self._estimate_tokens(empty_text)
            )

        project_name = context.project_name
        class_ctx = context.class_context
        method_ctx = context.method_context
        dep_ctx = context.dependency_context
        citations_list = context.citations

        # Check for missing context sections
        if not class_ctx:
            logger.warning("Missing context section: class_context")
        if not method_ctx:
            logger.warning("Missing context section: method_context")
        if not dep_ctx:
            logger.warning("Missing context section: dependency_context")

        # Build citations text
        citations_str = ""
        if citations_list:
            citations_str = "\n".join(
                f"- File: {c.file_path} (Lines {c.start_line}-{c.end_line}) in class {c.class_name}"
                for c in citations_list
            )

        # Assemble initial prompt text
        prompt_text = self._format_prompt(
            project_name=project_name,
            class_ctx=class_ctx,
            method_ctx=method_ctx,
            dep_ctx=dep_ctx,
            citations_str=citations_str,
            question=question
        )

        max_char_limit = self.max_tokens * 4

        if len(prompt_text) > max_char_limit:
            logger.warning("Context truncated")
            dep_ctx = ""
            prompt_text = self._format_prompt(
                project_name=project_name,
                class_ctx=class_ctx,
                method_ctx=method_ctx,
                dep_ctx=dep_ctx,
                citations_str=citations_str,
                question=question
            )

            if len(prompt_text) > max_char_limit:
                method_ctx = ""
                prompt_text = self._format_prompt(
                    project_name=project_name,
                    class_ctx=class_ctx,
                    method_ctx=method_ctx,
                    dep_ctx=dep_ctx,
                    citations_str=citations_str,
                    question=question
                )

                if len(prompt_text) > max_char_limit:
                    remaining_space = max_char_limit - (len(prompt_text) - len(class_ctx))
                    if remaining_space > 0:
                        class_ctx = class_ctx[:remaining_space] + "\n...[Truncated]..."
                    else:
                        class_ctx = "...[Truncated]..."

                    prompt_text = self._format_prompt(
                        project_name=project_name,
                        class_ctx=class_ctx,
                        method_ctx=method_ctx,
                        dep_ctx=dep_ctx,
                        citations_str=citations_str,
                        question=question
                    )

        token_estimate = self._estimate_tokens(prompt_text)
        logger.info(f"Prompt size: {len(prompt_text)} characters")
        logger.info(f"Token estimate: {token_estimate}")

        return Prompt(
            prompt_text=prompt_text,
            citations=citations_list,
            token_estimate=token_estimate
        )

    def _format_prompt(
        self,
        project_name: str,
        class_ctx: str,
        method_ctx: str,
        dep_ctx: str,
        citations_str: str,
        question: str
    ) -> str:
        system_prompt = settings.SYSTEM_PROMPT if settings else "You are a Senior Java Architect."
        return f"""System Instructions:
{system_prompt} Answer the user's question grounded strictly in the provided project context.
If the context is insufficient, state clearly that you do not have enough information. Do not invent classes, methods, or details.

Project Information:
Project Name: {project_name}

Retrieved Context:
{class_ctx if class_ctx else "None"}

Relevant Methods:
{method_ctx if method_ctx else "None"}

Dependencies:
{dep_ctx if dep_ctx else "None"}

Citations:
{citations_str if citations_str else "None"}

Response Rules:
1. Answer only from the supplied context.
2. Never invent classes, methods, or variables.
3. Cite file paths and line ranges where appropriate (e.g. [UserService.java:10-20]).
4. Clearly state when context is insufficient.
5. Avoid speculation.

User Question:
{question}
"""

    def _estimate_tokens(self, text: str) -> int:
        return int(len(text) / 4) + 1