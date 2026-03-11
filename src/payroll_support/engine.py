from __future__ import annotations

from dataclasses import dataclass


@dataclass
class IntentResult:
    intent: str
    confidence: float


class RuleBasedNLPEngine:
    """Pilot NLP engine using keyword classification."""

    def classify(self, message: str) -> IntentResult:
        text = message.lower().strip()

        if any(k in text for k in ("payslip", "salary", "paid", "payment")):
            return IntentResult(intent="payroll_data", confidence=0.92)

        if any(k in text for k in ("tax", "pension", "overtime", "deduction")):
            return IntentResult(intent="knowledge_lookup", confidence=0.89)

        if any(k in text for k in ("complaint", "wrong", "issue", "urgent", "escalate")):
            return IntentResult(intent="escalation", confidence=0.94)

        return IntentResult(intent="unknown", confidence=0.41)
