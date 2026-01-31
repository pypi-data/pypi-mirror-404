# Copyright (c) 2026 Celestir LLC
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Integration tests for LangChain integration."""

from __future__ import annotations

from unittest.mock import MagicMock

from gridseal import GridSeal
from gridseal.integrations.langchain import GridSealCallbackHandler


class TestGridSealCallbackHandler:
    """Tests for GridSealCallbackHandler."""

    def test_initialization(self) -> None:
        """Test handler initialization."""
        gs = GridSeal(audit={"backend": "memory"})
        handler = GridSealCallbackHandler(gs)

        assert handler.gs is gs
        assert handler._current_query == ""
        assert handler._current_context == []

    def test_on_llm_start(self) -> None:
        """Test on_llm_start captures query."""
        gs = GridSeal(audit={"backend": "memory"})
        handler = GridSealCallbackHandler(gs)

        handler.on_llm_start(
            serialized={},
            prompts=["What is the policy?"],
        )

        assert handler._current_query == "What is the policy?"

    def test_on_llm_start_empty_prompts(self) -> None:
        """Test on_llm_start with empty prompts."""
        gs = GridSeal(audit={"backend": "memory"})
        handler = GridSealCallbackHandler(gs)

        handler.on_llm_start(serialized={}, prompts=[])

        assert handler._current_query == ""

    def test_on_retriever_end(self) -> None:
        """Test on_retriever_end captures context."""
        gs = GridSeal(audit={"backend": "memory"})
        handler = GridSealCallbackHandler(gs)

        doc1 = MagicMock()
        doc1.page_content = "Document 1 content"
        doc2 = MagicMock()
        doc2.page_content = "Document 2 content"

        handler.on_retriever_end(documents=[doc1, doc2])

        assert handler._current_context == [
            "Document 1 content",
            "Document 2 content",
        ]

    def test_on_retriever_end_string_docs(self) -> None:
        """Test on_retriever_end with string documents."""
        gs = GridSeal(audit={"backend": "memory"})
        handler = GridSealCallbackHandler(gs)

        handler.on_retriever_end(documents=["doc1", "doc2"])

        assert handler._current_context == ["doc1", "doc2"]

    def test_on_llm_end_logs_to_store(self) -> None:
        """Test on_llm_end logs to audit store."""
        gs = GridSeal(audit={"backend": "memory"})
        handler = GridSealCallbackHandler(gs)

        handler._current_query = "Test query"
        handler._current_context = ["context1"]

        response = MagicMock()
        response.generations = [[MagicMock(text="Test response")]]

        handler.on_llm_end(response=response)

        assert gs.store.count() == 1
        record = gs.store.query()[0]
        assert record.query == "Test query"
        assert record.response == "Test response"
        assert record.metadata.get("source") == "langchain"

    def test_on_llm_end_clears_context(self) -> None:
        """Test on_llm_end clears context after logging."""
        gs = GridSeal(audit={"backend": "memory"})
        handler = GridSealCallbackHandler(gs)

        handler._current_context = ["context"]
        response = MagicMock()
        response.generations = [[MagicMock(text="Response")]]

        handler.on_llm_end(response=response)

        assert handler._current_context == []

    def test_on_llm_end_string_response(self) -> None:
        """Test on_llm_end with string response."""
        gs = GridSeal(audit={"backend": "memory"})
        handler = GridSealCallbackHandler(gs)

        handler.on_llm_end(response="Plain string response")

        assert gs.store.count() == 1
        record = gs.store.query()[0]
        assert record.response == "Plain string response"

    def test_on_chain_start_captures_query(self) -> None:
        """Test on_chain_start captures query from inputs."""
        gs = GridSeal(audit={"backend": "memory"})
        handler = GridSealCallbackHandler(gs)

        handler.on_chain_start(
            serialized={},
            inputs={"query": "Chain query"},
        )

        assert handler._current_query == "Chain query"

    def test_on_chain_start_question_input(self) -> None:
        """Test on_chain_start with 'question' input."""
        gs = GridSeal(audit={"backend": "memory"})
        handler = GridSealCallbackHandler(gs)

        handler.on_chain_start(
            serialized={},
            inputs={"question": "User question"},
        )

        assert handler._current_query == "User question"

    def test_on_chain_start_input_key(self) -> None:
        """Test on_chain_start with 'input' key."""
        gs = GridSeal(audit={"backend": "memory"})
        handler = GridSealCallbackHandler(gs)

        handler.on_chain_start(
            serialized={},
            inputs={"input": "Generic input"},
        )

        assert handler._current_query == "Generic input"

    def test_on_llm_error(self) -> None:
        """Test on_llm_error logs error."""
        gs = GridSeal(audit={"backend": "memory"})
        handler = GridSealCallbackHandler(gs)

        handler.on_llm_error(error=Exception("Test error"))

    def test_on_chain_error(self) -> None:
        """Test on_chain_error logs error."""
        gs = GridSeal(audit={"backend": "memory"})
        handler = GridSealCallbackHandler(gs)

        handler.on_chain_error(error=Exception("Chain error"))

    def test_on_tool_error(self) -> None:
        """Test on_tool_error logs error."""
        gs = GridSeal(audit={"backend": "memory"})
        handler = GridSealCallbackHandler(gs)

        handler.on_tool_error(error=Exception("Tool error"))

    def test_full_rag_flow(self) -> None:
        """Test simulated full RAG flow."""
        gs = GridSeal(audit={"backend": "memory"})
        handler = GridSealCallbackHandler(gs)

        handler.on_chain_start(
            serialized={},
            inputs={"query": "What is the policy?"},
        )

        doc = MagicMock()
        doc.page_content = "Policy document content"
        handler.on_retriever_end(documents=[doc])

        handler.on_llm_start(
            serialized={},
            prompts=["Context: Policy document content\n\nQuery: What is the policy?"],
        )

        response = MagicMock()
        response.generations = [[MagicMock(text="The policy states...")]]
        handler.on_llm_end(response=response)

        handler.on_chain_end(outputs={"result": "The policy states..."})

        assert gs.store.count() == 1
        record = gs.store.query()[0]
        assert "policy" in record.response.lower()

    def test_on_text_noop(self) -> None:
        """Test on_text is a no-op."""
        gs = GridSeal(audit={"backend": "memory"})
        handler = GridSealCallbackHandler(gs)

        handler.on_text(text="Some text")

    def test_on_agent_action_noop(self) -> None:
        """Test on_agent_action is a no-op."""
        gs = GridSeal(audit={"backend": "memory"})
        handler = GridSealCallbackHandler(gs)

        handler.on_agent_action(action=MagicMock())

    def test_on_agent_finish_noop(self) -> None:
        """Test on_agent_finish is a no-op."""
        gs = GridSeal(audit={"backend": "memory"})
        handler = GridSealCallbackHandler(gs)

        handler.on_agent_finish(finish=MagicMock())

    def test_on_tool_start_noop(self) -> None:
        """Test on_tool_start is a no-op."""
        gs = GridSeal(audit={"backend": "memory"})
        handler = GridSealCallbackHandler(gs)

        handler.on_tool_start(serialized={}, input_str="input")

    def test_on_tool_end_noop(self) -> None:
        """Test on_tool_end is a no-op."""
        gs = GridSeal(audit={"backend": "memory"})
        handler = GridSealCallbackHandler(gs)

        handler.on_tool_end(output="output")
