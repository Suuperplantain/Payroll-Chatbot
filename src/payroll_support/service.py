from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .engine import RuleBasedNLPEngine
from .repositories import (
    KnowledgeRepository,
    MetricsRepository,
    PayrollRepository,
    TicketRepository,
)
from .security import AuthService


@dataclass
class ChatResponse:
    status: str
    message: str
    route: str
    payslip_summary: dict[str, float] | None = None


class PayrollSupportService:
    def __init__(
        self,
        auth_service: AuthService,
        nlp_engine: RuleBasedNLPEngine,
        knowledge_repo: KnowledgeRepository,
        payroll_repo: PayrollRepository,
        ticket_repo: TicketRepository,
        metrics_repo: MetricsRepository,
    ) -> None:
        self.auth_service = auth_service
        self.nlp_engine = nlp_engine
        self.knowledge_repo = knowledge_repo
        self.payroll_repo = payroll_repo
        self.ticket_repo = ticket_repo
        self.metrics_repo = metrics_repo

    def handle_message(self, employee_id: str, message: str) -> ChatResponse:
        start_time = datetime.now()

        if not self.auth_service.is_authorized(employee_id):
            return self._finalize(
                start_time,
                outcome="error",
                response=ChatResponse(
                    status="error",
                    message="Authentication failed. Please verify your employee ID.",
                    route="security",
                ),
            )

        intent = self.nlp_engine.classify(message)

        if intent.intent == "payroll_data":
            snapshot = self.payroll_repo.get_latest_snapshot(employee_id)
            if snapshot is None:
                return self._escalate(start_time, employee_id, message, "No payroll snapshot available")

            payslip_summary = self.generate_payslip_summary(employee_id)
            if payslip_summary is None:
                return self._escalate(start_time, employee_id, message, "Failed to build payslip summary")

            msg = (
                f"Your latest payslip amount is £{snapshot.latest_payslip_amount:.2f} "
                f"for {snapshot.pay_date.isoformat()}. "
                f"Tax: £{snapshot.tax_deduction:.2f}, Pension: £{snapshot.pension_deduction:.2f}."
            )
            return self._finalize(
                start_time,
                outcome="automated",
                response=ChatResponse(
                    status="ok",
                    message=msg,
                    route="payroll",
                    payslip_summary=payslip_summary,
                ),
            )

        if intent.intent == "knowledge_lookup":
            answer = self.knowledge_repo.search(message)
            if answer is None:
                return self._escalate(start_time, employee_id, message, "No KB match")
            return self._finalize(
                start_time,
                outcome="automated",
                response=ChatResponse(status="ok", message=answer, route="knowledge_base"),
            )

        return self._escalate(start_time, employee_id, message, f"Intent={intent.intent}")

    def generate_payslip_summary(self, employee_id: str) -> dict[str, float] | None:
        snapshot = self.payroll_repo.get_latest_snapshot(employee_id)
        if snapshot is None:
            return None

        gross_pay = snapshot.latest_payslip_amount + snapshot.tax_deduction + snapshot.pension_deduction
        total_deductions = snapshot.tax_deduction + snapshot.pension_deduction
        net_pay = snapshot.latest_payslip_amount

        return {
            "gross_pay": round(gross_pay, 2),
            "total_deductions": round(total_deductions, 2),
            "net_pay": round(net_pay, 2),
        }

    def _escalate(
        self,
        start_time: datetime,
        employee_id: str,
        message: str,
        reason: str,
    ) -> ChatResponse:
        ticket = self.ticket_repo.create_ticket(employee_id, message, reason)
        return self._finalize(
            start_time,
            outcome="handoff",
            response=ChatResponse(
                status="ok",
                message=(
                    "I could not fully resolve this. "
                    f"I created HR ticket {ticket.ticket_id}; the HR team will follow up shortly."
                ),
                route="hr_escalation",
            ),
        )

    def _finalize(self, start_time: datetime, outcome: str, response: ChatResponse) -> ChatResponse:
        response_time = (datetime.now() - start_time).total_seconds()
        self.metrics_repo.record_interaction(outcome=outcome, response_time=response_time)
        return response
