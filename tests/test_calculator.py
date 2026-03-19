import unittest

from aidwise.calculator import WorkbookAidCalculator


class WorkbookAidCalculatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.calculator = WorkbookAidCalculator()
        self.base_input = WorkbookAidCalculator.canonical_demo_input()

    def test_calculator_demo_matches_workbook_outputs(self) -> None:
        result = self.calculator.calculate(self.base_input)
        self.assertEqual(result.formula_type, "Formula A")
        self.assertEqual(result.sai, 5041)
        self.assertFalse(result.maximum_pell_eligible)
        self.assertTrue(result.minimum_pell_eligible)
        self.assertTrue(result.assets_required)

    def test_income_drop_reduces_or_holds_sai(self) -> None:
        comparison = self.calculator.compare_income_change(self.base_input, income_delta=-5_000)
        self.assertLessEqual(comparison.scenario.sai, comparison.baseline.sai)

    def test_student_info_row_flow_matches_live_workbook_path(self) -> None:
        result = self.calculator.calculate_student_info_row(2)
        self.assertEqual(result.sai, -1499)
        self.assertTrue(result.minimum_pell_eligible)
        self.assertTrue(result.maximum_pell_eligible)
        self.assertIn("Student Info flow", result.methodology)


if __name__ == "__main__":
    unittest.main()
