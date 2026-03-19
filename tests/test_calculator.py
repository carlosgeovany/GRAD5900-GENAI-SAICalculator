import unittest

from aidwise.calculator import AidCalculator
from aidwise.csv_loader import dataframe_to_inputs, template_dataframe


class AidCalculatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.calculator = AidCalculator()

    def test_canonical_demo_matches_expected_outputs(self) -> None:
        result = self.calculator.calculate(AidCalculator.canonical_demo_input())
        self.assertEqual(result.formula_type, "Formula A")
        self.assertEqual(result.sai, 5041)
        self.assertFalse(result.maximum_pell_eligible)
        self.assertTrue(result.minimum_pell_eligible)
        self.assertTrue(result.assets_required)

    def test_dependent_nonfiler_gets_negative_1500_and_max_pell(self) -> None:
        aid_input = AidCalculator.canonical_demo_input()
        aid_input.parent_filing_status = "Not required to file"
        result = self.calculator.calculate(aid_input)
        self.assertEqual(result.sai, -1500)
        self.assertTrue(result.maximum_pell_eligible)

    def test_student_info_sample_matches_live_workbook_calculation_branch(self) -> None:
        result = self.calculator.calculate(AidCalculator.student_info_sample_input())
        self.assertEqual(result.formula_type, "Formula A")
        self.assertEqual(result.sai, 37075)
        self.assertFalse(result.minimum_pell_eligible)
        self.assertFalse(result.maximum_pell_eligible)
        self.assertTrue(result.assets_required)

    def test_independent_with_dependents_uses_formula_c(self) -> None:
        aid_input = AidCalculator.canonical_demo_input()
        aid_input.dependency_status = "Independent"
        aid_input.student_family_size = 3
        aid_input.student_marital_status = "Single"
        result = self.calculator.calculate(aid_input)
        self.assertEqual(result.formula_type, "Formula C")

    def test_income_drop_reduces_or_holds_sai(self) -> None:
        comparison = self.calculator.compare_income_change(
            AidCalculator.canonical_demo_input(),
            income_delta=-5_000,
        )
        self.assertLessEqual(comparison.scenario.sai, comparison.baseline.sai)

    def test_template_csv_loads_into_aid_input(self) -> None:
        dataframe = template_dataframe()
        aid_inputs = dataframe_to_inputs(dataframe)
        self.assertEqual(len(aid_inputs), 1)
        self.assertEqual(aid_inputs[0].dependency_status, "Dependent")


if __name__ == "__main__":
    unittest.main()
