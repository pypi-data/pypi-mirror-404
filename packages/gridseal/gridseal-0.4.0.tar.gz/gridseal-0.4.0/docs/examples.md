# GridSeal Integration Examples

This document demonstrates how to integrate GridSeal into real-world LLM workflows.

## Table of Contents

1. [Ollama Local LLM Workflow](#1-ollama-local-llm-workflow)
2. [Langfuse + AWS Bedrock Agentic Workflow](#2-langfuse--aws-bedrock-agentic-workflow)

---

## 1. Ollama Local LLM Workflow

This example shows how to use GridSeal with Ollama for fully local, air-gapped AI verification.

### Prerequisites

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull a model
ollama pull llama3.2

# Install dependencies
pip install gridseal requests
```

### Basic RAG with Verification

```python
import requests
from gridseal import GridSeal

# Initialize GridSeal with local storage
gs = GridSeal(
    verification={
        "checks": ["grounding", "relevance"],
        "threshold": 0.6,
        "on_fail": "flag",
    },
    audit={
        "backend": "sqlite",
        "path": "./ollama_audit.db",
    },
)


def ollama_generate(prompt: str, model: str = "llama3.2") -> str:
    """Call Ollama's local API."""
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": model,
            "prompt": prompt,
            "stream": False,
        },
    )
    response.raise_for_status()
    return response.json()["response"]


@gs.verify
@gs.audit
def answer_question(query: str, context: list[str]) -> str:
    """Answer a question using Ollama with verification."""
    context_text = "\n\n".join(context)
    prompt = f"""Based on the following context, answer the question.

Context:
{context_text}

Question: {query}

Answer:"""

    return ollama_generate(prompt)


# Example usage
if __name__ == "__main__":
    # Your knowledge base documents
    documents = [
        "GridSeal is an AI governance platform by Celestir LLC.",
        "GridSeal provides hallucination detection via grounding checks.",
        "The audit store uses hash-chain integrity for tamper-evident logging.",
        "GridSeal supports SQLite and PostgreSQL backends.",
    ]

    # Ask a question
    result = answer_question(
        query="What verification features does GridSeal provide?",
        context=documents,
    )

    print(f"Answer: {result.response}")
    print(f"Verification Passed: {result.passed}")
    print(f"Grounding Score: {result.grounding_score:.2f}")
    print(f"Audit ID: {result.audit_id}")

    # Check for flags
    if not result.passed:
        print(f"Warnings: {result.flags}")
```

### Ollama with Streaming and Selective Prediction

```python
import requests
from gridseal import GridSeal, VerificationResult

gs = GridSeal(
    verification={
        "checks": ["grounding", "confidence"],
        "threshold": 0.7,
    },
    audit={"backend": "sqlite", "path": "./ollama_audit.db"},
)


def ollama_chat(messages: list[dict], model: str = "llama3.2") -> str:
    """Call Ollama chat API."""
    response = requests.post(
        "http://localhost:11434/api/chat",
        json={
            "model": model,
            "messages": messages,
            "stream": False,
        },
    )
    response.raise_for_status()
    return response.json()["message"]["content"]


class OllamaRAGPipeline:
    """RAG pipeline with verification and human-in-the-loop routing."""

    def __init__(self, gridseal: GridSeal, confidence_threshold: float = 0.8):
        self.gs = gridseal
        self.confidence_threshold = confidence_threshold
        self.review_queue: list[dict] = []

    def answer(self, query: str, context: list[str]) -> dict:
        """Answer with verification and routing."""

        @self.gs.verify
        @self.gs.audit
        def _generate(query: str, context: list[str]) -> str:
            context_text = "\n---\n".join(context)
            messages = [
                {
                    "role": "system",
                    "content": (
                        "You are a helpful assistant. Answer questions based only "
                        "on the provided context. If the context doesn't contain "
                        "enough information, say so."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Context:\n{context_text}\n\nQuestion: {query}",
                },
            ]
            return ollama_chat(messages)

        result = _generate(query, context)

        # Route based on confidence
        grounding = result.grounding_score or 0
        confidence = result.confidence_score or 1.0

        if result.passed and grounding >= self.confidence_threshold:
            return {
                "answer": result.response,
                "status": "auto_approved",
                "confidence": grounding,
                "audit_id": result.audit_id,
            }
        elif grounding >= 0.5:
            return {
                "answer": result.response,
                "status": "low_confidence",
                "confidence": grounding,
                "audit_id": result.audit_id,
                "warning": "Response may need human review",
            }
        else:
            # Queue for human review
            self.review_queue.append({
                "query": query,
                "draft_answer": result.response,
                "confidence": grounding,
                "audit_id": result.audit_id,
            })
            return {
                "answer": None,
                "status": "queued_for_review",
                "audit_id": result.audit_id,
            }


# Usage
pipeline = OllamaRAGPipeline(gs, confidence_threshold=0.75)

result = pipeline.answer(
    query="What databases does GridSeal support?",
    context=[
        "GridSeal supports SQLite for local development.",
        "PostgreSQL is available for enterprise deployments.",
        "The memory backend is used for testing.",
    ],
)

print(f"Status: {result['status']}")
print(f"Answer: {result.get('answer', 'Queued for review')}")
```

---

## 2. Langfuse + AWS Bedrock Agentic Workflow

This example shows GridSeal complementing Langfuse observability with AWS Bedrock in an agentic workflow.

### Prerequisites

```bash
pip install gridseal boto3 langfuse
```

### Architecture

```
User Query
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│                     Agentic Workflow                        │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐                 │
│  │  Plan   │───▶│ Execute │───▶│ Verify  │                 │
│  │  Agent  │    │  Agent  │    │  Agent  │                 │
│  └─────────┘    └─────────┘    └─────────┘                 │
│       │              │              │                       │
│       ▼              ▼              ▼                       │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                 AWS Bedrock                          │   │
│  │            (Claude 3.5 Sonnet)                       │   │
│  └─────────────────────────────────────────────────────┘   │
│       │              │              │                       │
└───────┼──────────────┼──────────────┼───────────────────────┘
        │              │              │
        ▼              ▼              ▼
   ┌─────────┐    ┌─────────┐    ┌─────────┐
   │Langfuse │    │Langfuse │    │GridSeal │
   │ Trace   │    │ Trace   │    │ Verify  │
   └─────────┘    └─────────┘    │ + Audit │
                                 └─────────┘
```

### Bedrock Client Setup

```python
import json
import boto3
from typing import Any


class BedrockClient:
    """AWS Bedrock client for Claude models."""

    def __init__(
        self,
        model_id: str = "anthropic.claude-3-5-sonnet-20241022-v2:0",
        region: str = "us-east-1",
    ):
        self.client = boto3.client("bedrock-runtime", region_name=region)
        self.model_id = model_id

    def generate(
        self,
        prompt: str,
        system: str | None = None,
        max_tokens: int = 4096,
    ) -> str:
        """Generate response from Bedrock."""
        messages = [{"role": "user", "content": prompt}]

        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "messages": messages,
        }

        if system:
            body["system"] = system

        response = self.client.invoke_model(
            modelId=self.model_id,
            body=json.dumps(body),
        )

        result = json.loads(response["body"].read())
        return result["content"][0]["text"]
```

### Langfuse + GridSeal Integration

```python
import os
from langfuse import Langfuse
from langfuse.decorators import observe, langfuse_context
from gridseal import GridSeal
from gridseal.adapters import LangfuseAdapter

# Initialize Langfuse
langfuse = Langfuse(
    public_key=os.environ["LANGFUSE_PUBLIC_KEY"],
    secret_key=os.environ["LANGFUSE_SECRET_KEY"],
    host=os.environ.get("LANGFUSE_HOST", "https://cloud.langfuse.com"),
)

# Initialize GridSeal with Langfuse adapter
# This syncs Langfuse traces to GridSeal's audit store
adapter = LangfuseAdapter(
    public_key=os.environ["LANGFUSE_PUBLIC_KEY"],
    secret_key=os.environ["LANGFUSE_SECRET_KEY"],
)

gs = GridSeal(
    mode="adapter",
    verification={
        "checks": ["grounding", "citation", "relevance"],
        "threshold": 0.7,
        "thresholds": {
            "citation": 0.6,  # Lower threshold for NLI
        },
    },
    audit={
        "backend": "postgresql",
        "connection": os.environ["DATABASE_URL"],
    },
    adapter=adapter,
)

# Bedrock client
bedrock = BedrockClient()
```

### Agentic Workflow with Verification

```python
from dataclasses import dataclass
from typing import Callable


@dataclass
class AgentAction:
    """An action the agent wants to take."""
    tool: str
    input: dict[str, Any]
    reasoning: str


@dataclass
class AgentResult:
    """Result of an agent execution."""
    output: str
    actions_taken: list[AgentAction]
    verification_passed: bool
    audit_id: str | None


class VerifiedAgent:
    """Agent with GridSeal verification at each step."""

    def __init__(
        self,
        gridseal: GridSeal,
        bedrock: BedrockClient,
        tools: dict[str, Callable],
        knowledge_base: list[str],
    ):
        self.gs = gridseal
        self.bedrock = bedrock
        self.tools = tools
        self.knowledge_base = knowledge_base

    @observe(name="plan")
    def plan(self, query: str, context: str) -> list[AgentAction]:
        """Plan the actions to take."""
        prompt = f"""You are a planning agent. Given the user query and context,
determine what actions to take.

Available tools: {list(self.tools.keys())}

Context:
{context}

User Query: {query}

Output a JSON list of actions:
[{{"tool": "tool_name", "input": {{}}, "reasoning": "why"}}]
"""
        response = self.bedrock.generate(prompt)

        # Parse actions (simplified - real impl would be more robust)
        import re
        json_match = re.search(r'\[.*\]', response, re.DOTALL)
        if json_match:
            actions_data = json.loads(json_match.group())
            return [AgentAction(**a) for a in actions_data]
        return []

    @observe(name="execute")
    def execute(self, actions: list[AgentAction]) -> list[str]:
        """Execute planned actions."""
        results = []
        for action in actions:
            if action.tool in self.tools:
                result = self.tools[action.tool](**action.input)
                results.append(f"{action.tool}: {result}")
            else:
                results.append(f"{action.tool}: Tool not found")
        return results

    @observe(name="synthesize")
    def synthesize(
        self,
        query: str,
        context: str,
        action_results: list[str],
    ) -> str:
        """Synthesize final answer from action results."""
        prompt = f"""Based on the context and action results, answer the user's question.

Context:
{context}

Action Results:
{chr(10).join(action_results)}

User Query: {query}

Provide a clear, factual answer based only on the information above.
"""
        return self.bedrock.generate(prompt)

    def run(self, query: str) -> AgentResult:
        """Run the full agent workflow with verification."""
        context = "\n---\n".join(self.knowledge_base)

        # Plan
        actions = self.plan(query, context)

        # Execute
        action_results = self.execute(actions)

        # Synthesize with GridSeal verification
        @self.gs.verify
        @self.gs.audit(metadata={"agent": "verified_agent", "query": query})
        def verified_synthesize(query: str, context: list[str]) -> str:
            return self.synthesize(query, "\n".join(context), action_results)

        result = verified_synthesize(query, self.knowledge_base)

        return AgentResult(
            output=result.response,
            actions_taken=actions,
            verification_passed=result.passed,
            audit_id=result.audit_id,
        )


# Example tools
def search_database(query: str) -> str:
    """Simulated database search."""
    return f"Found 3 records matching '{query}'"


def get_user_info(user_id: str) -> str:
    """Simulated user lookup."""
    return f"User {user_id}: Active, Premium tier"


# Usage
agent = VerifiedAgent(
    gridseal=gs,
    bedrock=bedrock,
    tools={
        "search_database": search_database,
        "get_user_info": get_user_info,
    },
    knowledge_base=[
        "Our company offers three tiers: Basic, Standard, and Premium.",
        "Premium users get priority support and advanced features.",
        "Database queries are logged for compliance purposes.",
        "All user data is encrypted at rest and in transit.",
    ],
)

result = agent.run("What benefits does a premium user get?")

print(f"Answer: {result.output}")
print(f"Verification: {'PASSED' if result.verification_passed else 'FAILED'}")
print(f"Audit ID: {result.audit_id}")
print(f"Actions: {[a.tool for a in result.actions_taken]}")
```

### Full Agentic RAG with Bedrock and Langfuse

```python
from langfuse.decorators import observe, langfuse_context


class BedrockRAGAgent:
    """
    Production RAG agent with:
    - Langfuse for observability
    - GridSeal for verification and compliance
    - AWS Bedrock for LLM
    """

    def __init__(self):
        self.bedrock = BedrockClient()
        self.gs = GridSeal(
            verification={
                "checks": ["grounding", "relevance", "confidence"],
                "threshold": 0.65,
            },
            audit={
                "backend": "postgresql",
                "connection": os.environ["DATABASE_URL"],
            },
        )

    @observe(name="retrieve")
    def retrieve(self, query: str) -> list[str]:
        """Retrieve relevant documents (placeholder for vector DB)."""
        # In production, this would query Pinecone, Weaviate, etc.
        return [
            "Document 1: Policy on data retention...",
            "Document 2: Security guidelines...",
            "Document 3: Compliance requirements...",
        ]

    @observe(name="generate")
    def generate(self, query: str, context: list[str]) -> str:
        """Generate answer using Bedrock."""
        context_text = "\n\n".join(f"[{i+1}] {doc}" for i, doc in enumerate(context))

        response = self.bedrock.generate(
            prompt=f"""Answer the question based on the provided context.
Cite sources using [1], [2], etc.

Context:
{context_text}

Question: {query}

Answer:""",
            system="You are a helpful assistant that answers questions accurately based on provided context.",
        )

        # Log to Langfuse
        langfuse_context.update_current_observation(
            input={"query": query, "context_count": len(context)},
            output=response,
            metadata={"model": "claude-3.5-sonnet"},
        )

        return response

    @observe(name="rag_pipeline")
    def answer(self, query: str) -> dict:
        """Full RAG pipeline with verification."""
        # Retrieve
        context = self.retrieve(query)

        # Generate with verification
        @self.gs.verify
        @self.gs.audit(metadata={
            "pipeline": "bedrock_rag",
            "trace_id": langfuse_context.get_current_trace_id(),
        })
        def verified_generate(query: str, context: list[str]) -> str:
            return self.generate(query, context)

        result = verified_generate(query, context)

        # Build response
        response = {
            "answer": result.response,
            "sources": context,
            "verification": {
                "passed": result.passed,
                "grounding_score": result.grounding_score,
                "relevance_score": result.relevance_score,
                "confidence_score": result.confidence_score,
            },
            "audit_id": result.audit_id,
            "trace_id": langfuse_context.get_current_trace_id(),
        }

        # Log verification result to Langfuse
        langfuse_context.update_current_trace(
            metadata={
                "verification_passed": result.passed,
                "grounding_score": result.grounding_score,
                "audit_id": result.audit_id,
            },
        )

        return response


# Usage
agent = BedrockRAGAgent()

response = agent.answer("What are our data retention policies?")

print(f"Answer: {response['answer'][:200]}...")
print(f"Grounding Score: {response['verification']['grounding_score']:.2f}")
print(f"Audit ID: {response['audit_id']}")
print(f"Langfuse Trace: {response['trace_id']}")

# Flush Langfuse events
langfuse.flush()
```

### Compliance Dashboard Query

After running workflows, query the audit store for compliance:

```python
from gridseal.audit import AuditStore
from gridseal.core.config import AuditConfig

# Connect to audit store
store = AuditStore(AuditConfig(
    backend="postgresql",
    connection=os.environ["DATABASE_URL"],
))

# Query recent failed verifications
failed_records = store.query(
    verification_passed=False,
    limit=100,
)

print(f"Failed verifications: {len(failed_records)}")

for record in failed_records[:5]:
    print(f"  - {record.id}: {record.query[:50]}...")
    print(f"    Score: {record.verification_results.get('grounding', {}).get('score', 'N/A')}")

# Verify audit log integrity
if store.verify_integrity():
    print("Audit log integrity: VALID")
else:
    print("Audit log integrity: COMPROMISED")

# Export for compliance review
store.export(
    output="./compliance_report.json",
    format="json",
    start_date="2026-01-01",
    end_date="2026-01-31",
)
```

---

## Summary

| Use Case | GridSeal Role | Key Features Used |
|----------|---------------|-------------------|
| Ollama Local | Primary verification | `@gs.verify`, `@gs.audit`, SQLite backend |
| Bedrock + Langfuse | Compliance layer | Adapter mode, PostgreSQL, citation check |

GridSeal provides the verification and compliance layer regardless of:
- LLM provider (Ollama, Bedrock, OpenAI, etc.)
- Observability tool (Langfuse, LangSmith, or none)
- Deployment (local, cloud, air-gapped)
