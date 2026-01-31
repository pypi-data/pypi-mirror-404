#!/usr/bin/env python3
# Copyright (c) 2026 Celestir LLC
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
GridSeal + AWS Bedrock Demo

Install: pip install gridseal boto3
Run: python bedrock_demo.py

Tests GridSeal's verification capabilities with real LLM responses.
"""

import json
import boto3
from gridseal import GridSeal

# Initialize Bedrock client
bedrock = boto3.client(
    service_name="bedrock-runtime",
    region_name="us-east-1",
)

# Initialize GridSeal with all checks
gs = GridSeal(
    verification={
        "checks": ["grounding", "relevance"],
        "threshold": 0.6,
        "on_fail": "flag",
    },
    audit={
        "backend": "sqlite",
        "path": "./demo_audit.db",
    },
)


def call_bedrock(prompt: str, system: str = "") -> str:
    """Call Claude on Bedrock."""
    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1024,
        "messages": [{"role": "user", "content": prompt}],
    }
    if system:
        body["system"] = system

    response = bedrock.invoke_model(
        modelId="anthropic.claude-3-haiku-20240307-v1:0",
        body=json.dumps(body),
    )

    result = json.loads(response["body"].read())
    return result["content"][0]["text"]


@gs.verify
@gs.audit
def answer_with_context(query: str, context: list[str]) -> str:
    """Answer a question using provided context."""
    context_text = "\n".join(f"- {c}" for c in context)
    prompt = f"""Answer the question based ONLY on the provided context.

Context:
{context_text}

Question: {query}

Answer concisely and only use information from the context."""

    return call_bedrock(prompt)


@gs.verify
@gs.audit
def answer_without_grounding(query: str, context: list[str]) -> str:
    """Answer freely - likely to hallucinate."""
    # Intentionally ignore context to trigger hallucination detection
    prompt = f"""Answer this question with detailed specifics: {query}

Make up plausible-sounding details if you need to."""

    return call_bedrock(prompt)


def run_demo():
    """Run verification demo."""

    # Test context - company policy documents
    context = [
        "Acme Corp employees receive 15 days of PTO per year.",
        "PTO requests must be submitted 2 weeks in advance.",
        "Unused PTO expires at the end of the calendar year.",
        "Managers must approve PTO within 3 business days.",
        "Emergency leave does not require advance notice.",
    ]

    print("=" * 60)
    print("GridSeal + Bedrock Verification Demo")
    print("=" * 60)

    # Test 1: Grounded response (should pass)
    print("\n[TEST 1] Grounded Response")
    print("-" * 40)
    query1 = "How many PTO days do employees get?"

    result1 = answer_with_context(query1, context)
    print(f"Query: {query1}")
    print(f"Response: {result1.response}")
    print(f"Passed: {result1.passed}")
    print(f"Checks: {json.dumps({k: {'score': round(v.score, 3), 'passed': v.passed} for k, v in result1.checks.items()}, indent=2)}")
    print(f"Audit ID: {result1.audit_id}")

    # Test 2: Potentially hallucinated response (may fail)
    print("\n[TEST 2] Ungrounded Response (Hallucination Risk)")
    print("-" * 40)
    query2 = "What is Acme Corp's policy on remote work?"

    result2 = answer_with_context(query2, context)
    print(f"Query: {query2}")
    print(f"Response: {result2.response}")
    print(f"Passed: {result2.passed}")
    print(f"Checks: {json.dumps({k: {'score': round(v.score, 3), 'passed': v.passed} for k, v in result2.checks.items()}, indent=2)}")
    if result2.flags:
        print(f"Flags: {result2.flags}")

    # Test 3: Intentional hallucination
    print("\n[TEST 3] Intentional Hallucination")
    print("-" * 40)
    query3 = "What are the specific salary bands at Acme Corp?"

    result3 = answer_without_grounding(query3, context)
    print(f"Query: {query3}")
    print(f"Response: {result3.response[:200]}..." if len(result3.response) > 200 else f"Response: {result3.response}")
    print(f"Passed: {result3.passed}")
    print(f"Checks: {json.dumps({k: {'score': round(v.score, 3), 'passed': v.passed} for k, v in result3.checks.items()}, indent=2)}")
    if result3.flags:
        print(f"Flags: {result3.flags}")

    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"Test 1 (Grounded):     {'PASS' if result1.passed else 'FAIL'}")
    print(f"Test 2 (Off-topic):    {'PASS' if result2.passed else 'FAIL'}")
    print(f"Test 3 (Hallucination): {'PASS' if result3.passed else 'FAIL'}")

    # Show audit stats
    print("\n[Audit Trail]")
    from gridseal.audit import AuditStore
    from gridseal.core.config import AuditConfig
    store = AuditStore(AuditConfig(backend="sqlite", path="./demo_audit.db"))
    records = store.query(limit=10)
    print(f"Total records logged: {len(records)}")
    for r in records:
        print(f"  - {r.audit_id[:8]}... | passed={r.verification_passed} | {r.timestamp}")


if __name__ == "__main__":
    run_demo()
