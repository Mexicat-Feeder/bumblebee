"""
Swarm Engine — Archetype Classification

Reads a PRD and classifies the project into an archetype.
If no archetype fits, returns "unknown" with a recommendation.

Designed as an importable function for both CLI and dashboard use.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Callable

from .decompose import ARCHETYPE_SCAFFOLDS


# ---------------------------------------------------------------------------
# Data structures (dashboard-friendly)
# ---------------------------------------------------------------------------

@dataclass
class ArchetypeResult:
    """Result of archetype classification. Dashboard displays for human confirmation."""
    archetype: str                          # selected archetype key or "unknown"
    confidence: str = "high"                # high / medium / low
    reasoning: str = ""                     # why this archetype was chosen
    available_archetypes: list[str] = field(default_factory=list)
    scaffold_ticket_count: int = 0          # how many scaffold tickets this produces
    needs_human_input: bool = False         # true if confidence is low or unknown

    def to_dict(self) -> dict[str, Any]:
        return {
            "archetype": self.archetype,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "available_archetypes": self.available_archetypes,
            "scaffold_ticket_count": self.scaffold_ticket_count,
            "needs_human_input": self.needs_human_input,
        }


# ---------------------------------------------------------------------------
# Rule-based classification (no LLM needed for common cases)
# ---------------------------------------------------------------------------

def _rule_based_classify(prd_text: str) -> ArchetypeResult | None:
    """Try to classify without an LLM using keyword matching."""
    text = prd_text.lower()
    available = list(ARCHETYPE_SCAFFOLDS.keys())

    has_react = any(k in text for k in ["react", "vite", "jsx", "tsx", "frontend"])
    has_express = any(k in text for k in ["express", "node.js backend", "api routes", "rest api"])
    has_vue = "vue" in text
    has_static = any(k in text for k in ["static site", "html only", "no framework"])

    if has_react and has_express:
        return ArchetypeResult(
            archetype="react-express",
            confidence="high",
            reasoning="PRD mentions React/Vite frontend AND Express/API backend",
            available_archetypes=available,
            scaffold_ticket_count=6,
        )
    elif has_react and not has_express:
        return ArchetypeResult(
            archetype="react-spa",
            confidence="high",
            reasoning="PRD mentions React/Vite frontend with no explicit backend",
            available_archetypes=available,
            scaffold_ticket_count=5,
        )

    return None  # can't classify with rules alone


# ---------------------------------------------------------------------------
# LLM-based classification (for ambiguous cases)
# ---------------------------------------------------------------------------

def _llm_classify(prd_text: str, llm_fn: Callable) -> ArchetypeResult:
    """Use LLM to classify when rules aren't sufficient."""
    available = list(ARCHETYPE_SCAFFOLDS.keys())

    prompt = (
        "You are classifying a software project into an archetype.\n\n"
        f"Available archetypes: {available}\n\n"
        f"PRD (first 3000 chars):\n{prd_text[:3000]}\n\n"
        "Respond with JSON: {\"archetype\": \"<key or unknown>\", "
        "\"confidence\": \"high|medium|low\", \"reasoning\": \"<why>\"}"
    )

    try:
        response = llm_fn("You classify projects into archetypes.", prompt)
        # Parse JSON from response
        text = response.strip()
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            data = json.loads(text[start:end])
            archetype = data.get("archetype", "unknown")
            confidence = data.get("confidence", "medium")

            # Validate archetype exists
            if archetype not in ARCHETYPE_SCAFFOLDS and archetype != "unknown":
                archetype = "unknown"
                confidence = "low"

            scaffold_count = 0
            if archetype in ARCHETYPE_SCAFFOLDS:
                scaffold_count = len(ARCHETYPE_SCAFFOLDS[archetype]("test"))

            return ArchetypeResult(
                archetype=archetype,
                confidence=confidence,
                reasoning=data.get("reasoning", ""),
                available_archetypes=available,
                scaffold_ticket_count=scaffold_count,
                needs_human_input=(confidence == "low" or archetype == "unknown"),
            )
    except Exception as e:
        pass

    return ArchetypeResult(
        archetype="unknown",
        confidence="low",
        reasoning="LLM classification failed",
        available_archetypes=available,
        needs_human_input=True,
    )


# ---------------------------------------------------------------------------
# Main classification function
# ---------------------------------------------------------------------------

def classify_archetype(
    prd_text: str,
    llm_fn: Callable | None = None,
) -> ArchetypeResult:
    """
    Classify a PRD into a project archetype.
    
    Tries rule-based first (fast, no LLM cost).
    Falls back to LLM if rules can't decide.
    Returns structured result for human confirmation.
    """
    # Try rules first
    result = _rule_based_classify(prd_text)
    if result:
        return result

    # Fall back to LLM
    if llm_fn:
        return _llm_classify(prd_text, llm_fn)

    # No LLM and rules couldn't decide
    return ArchetypeResult(
        archetype="unknown",
        confidence="low",
        reasoning="Could not classify from PRD keywords and no LLM available",
        available_archetypes=list(ARCHETYPE_SCAFFOLDS.keys()),
        needs_human_input=True,
    )
