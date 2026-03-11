from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Protocol


@dataclass
class PayrollSnapshot:
    employee_id: str
    latest_payslip_amount: float
    pay_date: date
    tax_deduction: float
    pension_deduction: float


@dataclass
class HRTicket:
    ticket_id: str
    employee_id: str
    message: str
    reason: str


@dataclass
class MetricsSummary:
    total_interactions: int
    deflection_rate: float
    average_response_time: float
    error_rate: float
    handoff_rate: float


class KnowledgeRepository(Protocol):
    def search(self, query: str) -> str | None:
        ...


class PayrollRepository(Protocol):
    def get_latest_snapshot(self, employee_id: str) -> PayrollSnapshot | None:
        ...


class TicketRepository(Protocol):
    def create_ticket(self, employee_id: str, message: str, reason: str) -> HRTicket:
        ...


class MetricsRepository(Protocol):
    def record_interaction(self, outcome: str, response_time: float) -> None:
        ...

    def get_summary(self) -> MetricsSummary:
        ...


class InMemoryKnowledgeRepository:
    def __init__(self) -> None:
        self._entries = {
            "tax": "Tax is deducted based on your selected tax code and statutory rules.",
            "pension": "Pension deductions follow your enrolled scheme contribution rates.",
            "payslip": "Payslips are generated monthly and available after payroll processing.",
            "overtime": "Approved overtime is included in the next eligible payroll run.",
        }

    def search(self, query: str) -> str | None:
        q = query.lower()
        for keyword, answer in self._entries.items():
            if keyword in q:
                return answer
        return None


class InMemoryPayrollRepository:
    def __init__(self) -> None:
        self._snapshots = {
            "E1001": PayrollSnapshot(
                employee_id="E1001",
                latest_payslip_amount=4250.35,
                pay_date=date(2026, 2, 28),
                tax_deduction=740.12,
                pension_deduction=221.90,
            ),
            "E1002": PayrollSnapshot(
                employee_id="E1002",
                latest_payslip_amount=3888.10,
                pay_date=date(2026, 2, 28),
                tax_deduction=620.05,
                pension_deduction=190.40,
            ),
        }

    def get_latest_snapshot(self, employee_id: str) -> PayrollSnapshot | None:
        return self._snapshots.get(employee_id)


class InMemoryTicketRepository:
    def __init__(self) -> None:
        self._counter = 1
        self._tickets: list[HRTicket] = []

    def create_ticket(self, employee_id: str, message: str, reason: str) -> HRTicket:
        ticket = HRTicket(
            ticket_id=f"HR-{self._counter:04d}",
            employee_id=employee_id,
            message=message,
            reason=reason,
        )
        self._counter += 1
        self._tickets.append(ticket)
        return ticket


class InMemoryMetricsRepository:
    def __init__(self) -> None:
        self._events: list[dict[str, float | str]] = []

    def record_interaction(self, outcome: str, response_time: float) -> None:
        self._events.append({"outcome": outcome, "response_time": max(response_time, 0.0)})

    def get_summary(self) -> MetricsSummary:
        total = len(self._events)
        if total == 0:
            return MetricsSummary(
                total_interactions=0,
                deflection_rate=0.0,
                average_response_time=0.0,
                error_rate=0.0,
                handoff_rate=0.0,
            )

        automated = sum(1 for e in self._events if e["outcome"] == "automated")
        handoff = sum(1 for e in self._events if e["outcome"] == "handoff")
        error = sum(1 for e in self._events if e["outcome"] == "error")
        avg_response = sum(float(e["response_time"]) for e in self._events) / total

        return MetricsSummary(
            total_interactions=total,
            deflection_rate=automated / total,
            average_response_time=avg_response,
            error_rate=error / total,
            handoff_rate=handoff / total,
        )
