import unittest

from src.payroll_support import (
    AuthService,
    InMemoryKnowledgeRepository,
    InMemoryMetricsRepository,
    InMemoryPayrollRepository,
    InMemoryTicketRepository,
    PayrollSupportService,
    RuleBasedNLPEngine,
)


class PayrollSupportServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.metrics_repo = InMemoryMetricsRepository()
        self.service = PayrollSupportService(
            auth_service=AuthService({"E1001"}),
            nlp_engine=RuleBasedNLPEngine(),
            knowledge_repo=InMemoryKnowledgeRepository(),
            payroll_repo=InMemoryPayrollRepository(),
            ticket_repo=InMemoryTicketRepository(),
            metrics_repo=self.metrics_repo,
        )

    def test_security_route_for_unauthorized_user(self) -> None:
        result = self.service.handle_message("E9999", "Show me my payslip")
        self.assertEqual(result.route, "security")

    def test_payroll_route_for_payslip_query_and_summary(self) -> None:
        result = self.service.handle_message("E1001", "What was my payslip amount?")
        self.assertEqual(result.route, "payroll")
        self.assertIn("latest payslip amount", result.message)
        self.assertEqual(
            result.payslip_summary,
            {
                "gross_pay": 5212.37,
                "total_deductions": 962.02,
                "net_pay": 4250.35,
            },
        )

    def test_knowledge_route_for_tax_question(self) -> None:
        result = self.service.handle_message("E1001", "How is my tax calculated?")
        self.assertEqual(result.route, "knowledge_base")

    def test_escalation_route_for_unknown(self) -> None:
        result = self.service.handle_message("E1001", "I need help with something unique")
        self.assertEqual(result.route, "hr_escalation")
        self.assertIn("HR ticket", result.message)

    def test_metrics_are_recorded(self) -> None:
        self.service.handle_message("E1001", "How is my tax calculated?")
        self.service.handle_message("E1001", "I need help with something unique")
        self.service.handle_message("E9999", "Show me my payslip")

        summary = self.metrics_repo.get_summary()
        self.assertEqual(summary.total_interactions, 3)
        self.assertAlmostEqual(summary.deflection_rate, 1 / 3)
        self.assertAlmostEqual(summary.handoff_rate, 1 / 3)
        self.assertAlmostEqual(summary.error_rate, 1 / 3)


if __name__ == "__main__":
    unittest.main()
