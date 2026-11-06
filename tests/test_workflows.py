import unittest

from src.workflows import ToolResult, WorkflowRequest, WorkflowStep, make_demo_tools, run_workflow


def fact(key="revenue", value=100, evidence="filing:p1:s1"):
    return {"fact_key": key, "value": value, "unit": "USD million", "evidence_ids": [evidence]}


class TypedWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.request = WorkflowRequest("Review Alpha", "2026-03-01", "ALP")
        self.tools = make_demo_tools([fact()], [fact("cpi", 3.0, "macro:cpi")], [{"evidence_id": "filing:risk"}])

    def test_default_five_role_trace_is_typed_and_hashed(self):
        result = run_workflow(self.request, self.tools)
        self.assertEqual([row["role"] for row in result["trace"]], ["Company", "Macro", "News", "Risk", "Synthesis"])
        self.assertEqual(result["trace"][2]["status"], "missing")
        self.assertEqual(len(result["artifact_sha256"]), 64)
        self.assertEqual(result["budget"]["steps_used"], 5)

    def test_role_tool_allowlist_is_enforced(self):
        with self.assertRaises(PermissionError):
            run_workflow(self.request, self.tools, [WorkflowStep("News", "company_facts")])

    def test_step_budget_is_enforced_before_execution(self):
        request = WorkflowRequest("Review Alpha", "2026-03-01", "ALP", max_steps=1)
        with self.assertRaisesRegex(ValueError, "max_steps"):
            run_workflow(request, self.tools)

    def test_time_budget_records_visible_error(self):
        ticks = iter([0.0, 0.0, 2.0])
        request = WorkflowRequest("Review Alpha", "2026-03-01", "ALP", max_steps=5, max_seconds=1.0)
        result = run_workflow(request, self.tools, [WorkflowStep("Company", "company_facts"), WorkflowStep("Macro", "macro_snapshot")], lambda: next(ticks))
        self.assertEqual(result["trace"][-1]["status"], "error")
        self.assertIn("budget", result["trace"][-1]["message"])

    def test_tool_exception_is_contained_in_trace(self):
        tools = dict(self.tools)
        tools["company_facts"] = lambda *_: (_ for _ in ()).throw(RuntimeError("fixture failure"))
        result = run_workflow(self.request, tools, [WorkflowStep("Company", "company_facts")])
        self.assertEqual(result["status"], "error")
        self.assertIn("RuntimeError", result["trace"][0]["message"])

    def test_uncited_fact_is_rejected(self):
        tools = dict(self.tools)
        tools["company_facts"] = lambda *_: ToolResult("success", [fact(evidence="")], [], [], [])
        result = run_workflow(self.request, tools, [WorkflowStep("Company", "company_facts")])
        self.assertEqual(result["trace"][0]["status"], "error")

    def test_synthesis_surfaces_conflicting_facts(self):
        tools = make_demo_tools([fact(value=100)], [fact(value=110)], [])
        result = run_workflow(self.request, tools)
        self.assertEqual(result["status"], "conflict")
        self.assertEqual(result["trace"][-1]["status"], "conflict")


if __name__ == "__main__":
    unittest.main()
