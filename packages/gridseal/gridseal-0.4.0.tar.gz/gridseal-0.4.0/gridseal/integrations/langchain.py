# Copyright (c) 2026 Celestir LLC
# SPDX-License-Identifier: AGPL-3.0-or-later

"""LangChain integration for GridSeal."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from gridseal import GridSeal

logger = logging.getLogger(__name__)


class GridSealCallbackHandler:
    """
    LangChain callback handler for GridSeal.

    Automatically captures LangChain operations and logs them
    to GridSeal's audit store.

    This handler implements the LangChain callback interface
    without requiring LangChain as a direct dependency.
    """

    def __init__(self, gridseal: GridSeal) -> None:
        """
        Initialize callback handler.

        Args:
            gridseal: GridSeal instance to log to
        """
        self.gs = gridseal
        self._current_query = ""
        self._current_context: list[str] = []

    def on_llm_start(
        self,
        serialized: dict[str, Any],
        prompts: list[str],
        **kwargs: Any,
    ) -> None:
        """Called when LLM starts processing."""
        if prompts:
            self._current_query = prompts[0]

    def on_llm_end(
        self,
        response: Any,
        **kwargs: Any,
    ) -> None:
        """Called when LLM finishes processing."""
        try:
            if hasattr(response, "generations") and response.generations:
                text = response.generations[0][0].text
            else:
                text = str(response)

            self.gs.store.log(
                query=self._current_query,
                context=self._current_context,
                response=text,
                verification_passed=True,
                metadata={"source": "langchain"},
            )
        except Exception as e:
            logger.error(f"Failed to log LangChain response: {e}")
        finally:
            self._current_context = []

    def on_retriever_end(
        self,
        documents: list[Any],
        **kwargs: Any,
    ) -> None:
        """Called when retriever returns documents."""
        self._current_context = [
            doc.page_content if hasattr(doc, "page_content") else str(doc)
            for doc in documents
        ]

    def on_llm_error(
        self,
        error: Exception,
        **kwargs: Any,
    ) -> None:
        """Called on LLM error."""
        logger.error(f"LangChain LLM error: {error}")

    def on_chain_start(
        self,
        serialized: dict[str, Any],
        inputs: dict[str, Any],
        **kwargs: Any,
    ) -> None:
        """Called when chain starts."""
        if "query" in inputs:
            self._current_query = str(inputs["query"])
        elif "question" in inputs:
            self._current_query = str(inputs["question"])
        elif "input" in inputs:
            self._current_query = str(inputs["input"])

    def on_chain_end(
        self,
        outputs: dict[str, Any],
        **kwargs: Any,
    ) -> None:
        """Called when chain ends."""
        pass

    def on_chain_error(
        self,
        error: Exception,
        **kwargs: Any,
    ) -> None:
        """Called on chain error."""
        logger.error(f"LangChain chain error: {error}")

    def on_tool_start(
        self,
        serialized: dict[str, Any],
        input_str: str,
        **kwargs: Any,
    ) -> None:
        """Called when tool starts."""
        pass

    def on_tool_end(
        self,
        output: str,
        **kwargs: Any,
    ) -> None:
        """Called when tool ends."""
        pass

    def on_tool_error(
        self,
        error: Exception,
        **kwargs: Any,
    ) -> None:
        """Called on tool error."""
        logger.error(f"LangChain tool error: {error}")

    def on_text(
        self,
        text: str,
        **kwargs: Any,
    ) -> None:
        """Called on arbitrary text."""
        pass

    def on_agent_action(
        self,
        action: Any,
        **kwargs: Any,
    ) -> None:
        """Called on agent action."""
        pass

    def on_agent_finish(
        self,
        finish: Any,
        **kwargs: Any,
    ) -> None:
        """Called when agent finishes."""
        pass
