# Copyright (c) 2026 Celestir LLC
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Claim extraction and verification for LLM responses."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from gridseal.core.types import ClaimVerification


@dataclass
class ExtractedClaim:
    """A claim extracted from text with position information."""

    text: str
    span_start: int
    span_end: int


def extract_claims(text: str) -> list[ExtractedClaim]:
    """
    Extract verifiable claims from text.

    Uses sentence segmentation and heuristics to identify
    statements that make factual assertions.

    Args:
        text: The text to extract claims from

    Returns:
        List of ExtractedClaim with text and span positions
    """
    claims: list[ExtractedClaim] = []

    # Split into sentences
    sentence_pattern = r'(?<=[.!?])\s+(?=[A-Z])'
    sentences = re.split(sentence_pattern, text)

    current_pos = 0
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            # Find position in original text
            match = text.find(sentence, current_pos) if sentence else -1
            if match >= 0:
                current_pos = match + len(sentence)
            continue

        # Find the actual position in original text
        start_pos = text.find(sentence, current_pos)
        if start_pos == -1:
            start_pos = current_pos

        end_pos = start_pos + len(sentence)

        # Skip non-claims (questions, greetings, etc.)
        if _is_likely_claim(sentence):
            claims.append(ExtractedClaim(
                text=sentence,
                span_start=start_pos,
                span_end=end_pos,
            ))

        current_pos = end_pos

    return claims


def _is_likely_claim(sentence: str) -> bool:
    """
    Determine if a sentence is likely a verifiable claim.

    Filters out questions, greetings, and meta-statements.
    """
    sentence_lower = sentence.lower().strip()

    # Skip questions
    if sentence.endswith("?"):
        return False

    # Skip greetings and pleasantries
    skip_patterns = [
        r"^(hi|hello|hey|good morning|good afternoon|good evening)",
        r"^(thank you|thanks|please)",
        r"^(i hope|i think|i believe|in my opinion)",
        r"^(let me|allow me|i would|i can)",
        r"^(sure|of course|certainly|absolutely)",
        r"^(however|but|although|while)",
    ]

    for pattern in skip_patterns:
        if re.match(pattern, sentence_lower):
            return False

    # Skip very short sentences (likely incomplete)
    if len(sentence.split()) < 4:
        return False

    # Skip sentences that are just references
    if sentence_lower.startswith("see ") or sentence_lower.startswith("refer to"):
        return False

    # Skip meta-statements about inability
    if "i don't have" in sentence_lower or "i cannot" in sentence_lower:
        return False

    if "i'm not able" in sentence_lower or "i am not able" in sentence_lower:
        return False

    return True


def match_claim_to_context(
    claim: ExtractedClaim,
    context: list[str],
    similarity_fn: callable | None = None,
) -> tuple[str | None, float]:
    """
    Find the best matching context for a claim.

    Args:
        claim: The claim to match
        context: List of context documents
        similarity_fn: Optional function to compute similarity

    Returns:
        Tuple of (best_matching_context, similarity_score)
    """
    if not context:
        return None, 0.0

    if similarity_fn is None:
        # Simple word overlap similarity
        claim_words = set(claim.text.lower().split())

        best_match = None
        best_score = 0.0

        for ctx in context:
            ctx_words = set(ctx.lower().split())
            if not ctx_words:
                continue

            overlap = len(claim_words & ctx_words)
            score = overlap / max(len(claim_words), 1)

            if score > best_score:
                best_score = score
                best_match = ctx

        return best_match, best_score

    # Use provided similarity function
    best_match = None
    best_score = 0.0

    for ctx in context:
        score = similarity_fn(claim.text, ctx)
        if score > best_score:
            best_score = score
            best_match = ctx

    return best_match, best_score
