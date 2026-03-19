from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

from aidwise.models import AidInput, CalculationResult, ScenarioComparison


YES = "Yes"
NO = "No"
OTHER_STATE = "OTHER"
ALASKA = "AK"
HAWAII = "HI"

MARRIED_JOINT_FILING = {"Married filing Jointly"}
MARRIED_SEPARATE_FILING = {"Married filing Separate"}
UNMARRIED_STUDENT_STATUSES = {"Single", "Separated", "Divorced", "Widowed"}
MARRIED_STUDENT_STATUSES = {"Married", "Remarried"}

PARENT_IPA_BASE = {2: 29190, 3: 36330, 4: 44880, 5: 52950, 6: 61930}
SINGLE_WITH_DEPENDENTS_IPA = {2: 54950, 3: 68430, 4: 84480, 5: 99700, 6: 116590}
MARRIED_WITH_DEPENDENTS_IPA = {3: 57730, 4: 71280, 5: 84120, 6: 98370}

@dataclass(slots=True)
class SAIComponents:
    formula_type: str
    assets_required: bool
    raw_sai: int
    parent_contribution: float = 0.0
    student_income_contribution: float = 0.0
    student_asset_contribution: float = 0.0
    max_pell_threshold: float | None = None
    min_pell_threshold: float | None = None
    agi_for_pell: float = 0.0


class AidCalculator:
    methodology = (
        "Pure Python policy engine. AidWise calculates SAI, Maximum Pell, and Minimum Pell "
        "without using the Excel workbook at runtime."
    )

    @staticmethod
    def canonical_demo_input() -> AidInput:
        return AidInput(
            dependency_status="Dependent",
            parent_family_size=6,
            parent_1_dob=date(1976, 6, 5),
            parent_2_dob=date(1983, 8, 10),
            parent_schedule_abhdef=NO,
            parent_schedule_c=NO,
            parent_received_benefits=NO,
            parent_state="CT",
            parent_filing_status="Married filing Jointly",
            parent_agi=108000.0,
            parent_income_tax_paid=10100.0,
            parent_1_wages=108000.0,
            parent_cash_savings=600.0,
            student_filing_status="Single",
            student_agi=0.0,
            student_family_size=1,
            student_marital_status="Single",
            student_state="CT",
        )

    @staticmethod
    def student_info_sample_input() -> AidInput:
        return AidInput(
            dependency_status="Dependent",
            parent_family_size=6,
            parent_1_dob=date(1976, 10, 12),
            parent_2_dob=date(1974, 2, 20),
            parent_schedule_abhdef=YES,
            parent_schedule_c=YES,
            parent_received_benefits=NO,
            parent_state="MA",
            parent_filing_status="Married filing Jointly",
            parent_agi=183147.0,
            parent_untaxed_pensions=3570.0,
            parent_income_tax_paid=19500.0,
            parent_1_wages=114512.0,
            parent_1_schedule_c_income=13956.0,
            parent_cash_savings=50000.0,
            student_filing_status="Single",
            student_agi=10115.0,
            student_family_size=1,
            student_marital_status="Single",
            student_dob=date(2006, 2, 6),
            student_state="MA",
        )

    def calculate(self, aid_input: AidInput) -> CalculationResult:
        components = self._calculate_components(aid_input)
        max_pell_nonfiler = self._is_max_pell_nonfiler(aid_input)
        maximum_pell_eligible = self._is_maximum_pell_eligible(aid_input)
        minimum_pell_eligible = self._is_minimum_pell_eligible(aid_input)

        if max_pell_nonfiler:
            final_sai = -1500
        elif maximum_pell_eligible:
            final_sai = min(components.raw_sai, 0)
        else:
            final_sai = components.raw_sai

        rationale = [
            f"Formula type selected: {components.formula_type}",
            f"AGI plus foreign income exclusion used for Pell thresholds: ${components.agi_for_pell:,.0f}",
            (
                f"Maximum Pell threshold considered: ${components.max_pell_threshold:,.0f}"
                if components.max_pell_threshold is not None
                else "Maximum Pell threshold considered: not applicable"
            ),
            (
                f"Minimum Pell threshold considered: ${components.min_pell_threshold:,.0f}"
                if components.min_pell_threshold is not None
                else "Minimum Pell threshold considered: not applicable"
            ),
            f"Assets required: {YES if components.assets_required else NO}",
        ]

        if components.formula_type == "Formula A":
            rationale.append(
                f"Parent contribution: ${components.parent_contribution:,.0f}; "
                f"student income contribution: ${components.student_income_contribution:,.0f}; "
                f"student asset contribution: ${components.student_asset_contribution:,.0f}"
            )
        else:
            rationale.append(
                f"Student income contribution: ${components.student_income_contribution:,.0f}; "
                f"student asset contribution: ${components.student_asset_contribution:,.0f}"
            )

        details: dict[str, Any] = {
            "raw_sai_before_pell_adjustment": components.raw_sai,
            "agi_for_pell": round(components.agi_for_pell, 2),
            "max_pell_threshold": components.max_pell_threshold,
            "min_pell_threshold": components.min_pell_threshold,
            "parent_contribution": round(components.parent_contribution, 2),
            "student_income_contribution": round(components.student_income_contribution, 2),
            "student_asset_contribution": round(components.student_asset_contribution, 2),
            "max_pell_nonfiler_rule": max_pell_nonfiler,
        }

        return CalculationResult(
            sai=int(final_sai),
            minimum_pell_eligible=minimum_pell_eligible,
            maximum_pell_eligible=maximum_pell_eligible,
            methodology=self.methodology,
            formula_type=components.formula_type,
            assets_required=components.assets_required,
            details=details,
            rationale=rationale,
        )

    def compare_income_change(
        self, aid_input: AidInput, income_delta: float
    ) -> ScenarioComparison:
        baseline = self.calculate(aid_input)
        scenario = self.calculate(aid_input.with_income_delta(income_delta))
        direction = "decreases" if income_delta < 0 else "increases"
        return ScenarioComparison(
            baseline=baseline,
            scenario=scenario,
            summary=(
                f"When income {direction} by ${abs(income_delta):,.0f}, "
                f"the calculated SAI changes from {baseline.sai} to {scenario.sai}."
            ),
        )

    def _calculate_components(self, aid_input: AidInput) -> SAIComponents:
        formula_type = self._formula_type(aid_input)
        assets_required = self._assets_required(aid_input)
        agi_for_pell = self._agi_for_pell(aid_input)
        max_threshold = self._maximum_pell_threshold(aid_input)
        min_threshold = self._minimum_pell_threshold(aid_input)

        if formula_type == "Formula A":
            parent_contribution, student_income, student_assets, raw_sai = self._formula_a(
                aid_input, assets_required
            )
            return SAIComponents(
                formula_type=formula_type,
                assets_required=assets_required,
                raw_sai=raw_sai,
                parent_contribution=parent_contribution,
                student_income_contribution=student_income,
                student_asset_contribution=student_assets,
                max_pell_threshold=max_threshold,
                min_pell_threshold=min_threshold,
                agi_for_pell=agi_for_pell,
            )
        if formula_type == "Formula B":
            student_income, student_assets, raw_sai = self._formula_b(aid_input, assets_required)
            return SAIComponents(
                formula_type=formula_type,
                assets_required=assets_required,
                raw_sai=raw_sai,
                student_income_contribution=student_income,
                student_asset_contribution=student_assets,
                max_pell_threshold=max_threshold,
                min_pell_threshold=min_threshold,
                agi_for_pell=agi_for_pell,
            )
        student_income, student_assets, raw_sai = self._formula_c(aid_input, assets_required)
        return SAIComponents(
            formula_type=formula_type,
            assets_required=assets_required,
            raw_sai=raw_sai,
            student_income_contribution=student_income,
            student_asset_contribution=student_assets,
            max_pell_threshold=max_threshold,
            min_pell_threshold=min_threshold,
            agi_for_pell=agi_for_pell,
        )

    def _formula_a(self, aid_input: AidInput, assets_required: bool) -> tuple[float, float, float, int]:
        parent_total_income = (
            aid_input.parent_agi
            + aid_input.parent_ira_deductions
            + aid_input.parent_tax_exempt_interest
            + aid_input.parent_untaxed_pensions
            + aid_input.parent_foreign_income_exclusion
            - aid_input.parent_taxable_grants
            - aid_input.parent_education_credits
            - aid_input.parent_federal_work_study
        )

        parent_allowances = (
            aid_input.parent_income_tax_paid
            + self._parent_payroll_tax_allowance(aid_input)
            + self._parent_income_protection_allowance(aid_input.parent_family_size)
            + self._parent_employment_expense_allowance(aid_input)
        )
        parent_available_income = parent_total_income - parent_allowances
        parent_net_worth = (
            aid_input.parent_child_support
            + aid_input.parent_cash_savings
            + aid_input.parent_investments
            + self._adjusted_business_farm_value(aid_input.parent_business_farm)
        )
        parent_asset_contribution = (
            max(0.0, parent_net_worth) * 0.12 if assets_required else 0.0
        )
        parent_adjusted_available_income = parent_available_income + parent_asset_contribution
        parent_contribution = self._assessment_from_adjusted_available_income(
            parent_adjusted_available_income
        )

        student_total_income = (
            aid_input.student_agi
            + aid_input.student_ira_deductions
            + aid_input.student_tax_exempt_interest
            + aid_input.student_untaxed_pensions
            + aid_input.student_foreign_income_exclusion
            - aid_input.student_taxable_grants
            - aid_input.student_education_credits
            - aid_input.student_federal_work_study
        )
        student_allowances = (
            aid_input.student_income_tax_paid
            + self._dependent_student_payroll_tax_allowance(aid_input)
            + 11_510
            + max(0.0, -parent_adjusted_available_income)
        )
        student_available_income = student_total_income - student_allowances
        student_income_contribution = max(student_available_income * 0.5, 0.0)

        student_net_worth = (
            aid_input.student_cash_savings
            + aid_input.student_investments
            + self._adjusted_business_farm_value(aid_input.student_business_farm)
        )
        student_asset_contribution = (
            max(0.0, student_net_worth * 0.2) if assets_required else 0.0
        )

        raw_sai = max(
            -1500,
            int(
                round(
                    parent_contribution
                    + student_income_contribution
                    + student_asset_contribution
                )
            ),
        )
        return parent_contribution, student_income_contribution, student_asset_contribution, raw_sai

    def _formula_b(self, aid_input: AidInput, assets_required: bool) -> tuple[float, float, int]:
        total_income = self._student_total_income(aid_input)
        allowances = (
            aid_input.student_income_tax_paid
            + self._independent_payroll_tax_allowance(aid_input)
            + (29_350 if self._is_student_married(aid_input) else 18_310)
            + self._formula_b_employment_expense_allowance(aid_input)
        )
        student_available_income = total_income - allowances
        student_income_contribution = student_available_income * 0.5

        net_worth = (
            aid_input.student_child_support
            + aid_input.student_cash_savings
            + aid_input.student_investments
            + self._adjusted_business_farm_value(aid_input.student_business_farm)
        )
        student_asset_contribution = (
            max(0.0, net_worth * 0.2) if assets_required else 0.0
        )
        raw_sai = max(
            -1500,
            int(round(student_income_contribution + student_asset_contribution)),
        )
        return student_income_contribution, student_asset_contribution, raw_sai

    def _formula_c(self, aid_input: AidInput, assets_required: bool) -> tuple[float, float, int]:
        total_income = self._student_total_income(aid_input)
        allowances = (
            aid_input.student_income_tax_paid
            + self._independent_payroll_tax_allowance(aid_input)
            + self._formula_c_income_protection_allowance(aid_input)
            + self._formula_c_employment_expense_allowance(aid_input)
        )
        student_available_income = total_income - allowances
        net_worth = (
            aid_input.student_child_support
            + aid_input.student_cash_savings
            + aid_input.student_investments
            + self._adjusted_business_farm_value(aid_input.student_business_farm)
        )
        student_asset_contribution = (
            max(0.0, net_worth * 0.07) if assets_required else 0.0
        )
        adjusted_available_income = student_available_income + student_asset_contribution
        student_income_contribution = self._assessment_from_adjusted_available_income(
            adjusted_available_income
        )
        raw_sai = max(-1500, int(round(student_income_contribution)))
        return student_income_contribution, student_asset_contribution, raw_sai

    def _student_total_income(self, aid_input: AidInput) -> float:
        return (
            aid_input.student_agi
            + aid_input.student_ira_deductions
            + aid_input.student_tax_exempt_interest
            + aid_input.student_untaxed_pensions
            + aid_input.student_foreign_income_exclusion
            - aid_input.student_taxable_grants
            - aid_input.student_education_credits
            - aid_input.student_federal_work_study
        )

    def _formula_type(self, aid_input: AidInput) -> str:
        if aid_input.dependency_status == "Dependent":
            return "Formula A"
        if aid_input.student_family_size > 2:
            return "Formula C"
        if self._is_student_unmarried(aid_input) and aid_input.student_family_size > 1:
            return "Formula C"
        return "Formula B"

    def _is_maximum_pell_eligible(self, aid_input: AidInput) -> bool:
        if self._is_max_pell_nonfiler(aid_input):
            return True

        threshold = self._maximum_pell_threshold(aid_input)
        if threshold is None:
            return False
        agi_for_pell = self._agi_for_pell(aid_input)
        return 0 < agi_for_pell <= threshold

    def _is_minimum_pell_eligible(self, aid_input: AidInput) -> bool:
        threshold = self._minimum_pell_threshold(aid_input)
        if threshold is None:
            return False
        return self._agi_for_pell(aid_input) <= threshold

    def _maximum_pell_threshold(self, aid_input: AidInput) -> float | None:
        if self._is_max_pell_nonfiler(aid_input):
            return None

        poverty = self._poverty_guideline(
            aid_input.parent_state if aid_input.dependency_status == "Dependent" else aid_input.student_state,
            aid_input.parent_family_size if aid_input.dependency_status == "Dependent" else max(1, aid_input.student_family_size),
        )
        if aid_input.dependency_status == "Dependent":
            return poverty * (2.25 if self._number_of_parents(aid_input) == 1 else 1.75)
        if self._is_independent_single_parent(aid_input):
            return poverty * 2.25
        return poverty * 1.75

    def _minimum_pell_threshold(self, aid_input: AidInput) -> float | None:
        poverty = self._poverty_guideline(
            aid_input.parent_state if aid_input.dependency_status == "Dependent" else aid_input.student_state,
            aid_input.parent_family_size if aid_input.dependency_status == "Dependent" else max(1, aid_input.student_family_size),
        )
        if aid_input.dependency_status == "Dependent":
            return poverty * (3.25 if self._number_of_parents(aid_input) == 1 else 2.75)
        if self._is_independent_single_parent(aid_input):
            return poverty * 4.0
        if self._is_independent_parent_not_single(aid_input):
            return poverty * 3.5
        return poverty * 2.75

    def _is_max_pell_nonfiler(self, aid_input: AidInput) -> bool:
        if aid_input.dependency_status == "Dependent":
            return aid_input.parent_filing_status == "Not required to file"
        return aid_input.student_filing_status == "Not required to file"

    def _assets_required(self, aid_input: AidInput) -> bool:
        if aid_input.dependency_status == "Dependent":
            exception_applies = aid_input.parent_state == "Outside of the US"
            if exception_applies:
                return True
            no_assets = (
                aid_input.parent_schedule_abhdef != YES
                and (
                    aid_input.parent_schedule_c != YES
                    or aid_input.parent_received_benefits == YES
                    or (
                        aid_input.parent_schedule_c == YES
                        and -10_001
                        < (aid_input.parent_1_schedule_c_income + aid_input.parent_2_schedule_c_income)
                        < 10_001
                    )
                )
                and aid_input.parent_agi < 60_000
            )
            return not (no_assets or self._is_maximum_pell_eligible(aid_input))

        no_assets = (
            aid_input.student_schedule_abhdef != YES
            and (
                aid_input.student_schedule_c != YES
                or aid_input.student_received_benefits == YES
                or (
                    aid_input.student_schedule_c == YES
                    and -10_001
                    < (aid_input.student_schedule_c_income + aid_input.spouse_schedule_c_income)
                    < 10_001
                )
            )
            and aid_input.student_agi < 60_000
        )
        return not (no_assets or self._is_maximum_pell_eligible(aid_input))

    def _agi_for_pell(self, aid_input: AidInput) -> float:
        if aid_input.dependency_status == "Dependent":
            return aid_input.parent_agi + aid_input.parent_foreign_income_exclusion
        return aid_input.student_agi + aid_input.student_foreign_income_exclusion

    def _parent_income_protection_allowance(self, family_size: int) -> float:
        family_size = max(2, family_size)
        if family_size in PARENT_IPA_BASE:
            return float(PARENT_IPA_BASE[family_size])
        return float(PARENT_IPA_BASE[6] + (family_size - 6) * 6990)

    def _formula_c_income_protection_allowance(self, aid_input: AidInput) -> float:
        if self._is_student_married(aid_input):
            family_size = max(3, aid_input.student_family_size)
            if family_size in MARRIED_WITH_DEPENDENTS_IPA:
                return float(MARRIED_WITH_DEPENDENTS_IPA[family_size])
            return float(MARRIED_WITH_DEPENDENTS_IPA[6] + (family_size - 6) * 11110)
        family_size = max(2, aid_input.student_family_size)
        if family_size in SINGLE_WITH_DEPENDENTS_IPA:
            return float(SINGLE_WITH_DEPENDENTS_IPA[family_size])
        return float(SINGLE_WITH_DEPENDENTS_IPA[6] + (family_size - 6) * 13180)

    def _parent_employment_expense_allowance(self, aid_input: AidInput) -> float:
        combined_earned_income = self._parent_earned_income(aid_input)
        return min(5000.0, combined_earned_income * 0.35)

    def _formula_b_employment_expense_allowance(self, aid_input: AidInput) -> float:
        if not self._is_student_married(aid_input):
            return 0.0
        return min(5000.0, self._student_earned_income(aid_input) * 0.35)

    def _formula_c_employment_expense_allowance(self, aid_input: AidInput) -> float:
        if self._is_student_married(aid_input):
            return min(5000.0, self._student_earned_income(aid_input) * 0.35)
        return min(5000.0, self._earned_student_only(aid_input) * 0.35)

    def _parent_earned_income(self, aid_input: AidInput) -> float:
        return max(aid_input.parent_1_wages + aid_input.parent_1_schedule_c_income, 0.0) + max(
            aid_input.parent_2_wages + aid_input.parent_2_schedule_c_income, 0.0
        )

    def _earned_student_only(self, aid_input: AidInput) -> float:
        return max(aid_input.student_wages + aid_input.student_schedule_c_income, 0.0)

    def _student_earned_income(self, aid_input: AidInput) -> float:
        return self._earned_student_only(aid_input) + max(
            aid_input.spouse_wages + aid_input.spouse_schedule_c_income, 0.0
        )

    def _parent_payroll_tax_allowance(self, aid_input: AidInput) -> float:
        parent1 = max(aid_input.parent_1_wages + aid_input.parent_1_schedule_c_income, 0.0)
        parent2 = max(aid_input.parent_2_wages + aid_input.parent_2_schedule_c_income, 0.0)
        status = aid_input.parent_filing_status
        total = parent1 + parent2

        if status in MARRIED_SEPARATE_FILING:
            medicare = self._medicare_allowance(parent1, 125000) + self._medicare_allowance(parent2, 125000)
        elif status in MARRIED_JOINT_FILING:
            medicare = self._medicare_allowance(total, 250000)
        else:
            medicare = self._medicare_allowance(total, 200000)

        oasdi_cap = 20906.4 if status in MARRIED_JOINT_FILING | MARRIED_SEPARATE_FILING or self._number_of_parents(aid_input) > 1 else 10453.2
        oasdi = min(total * 0.062, oasdi_cap)
        return medicare + oasdi

    def _dependent_student_payroll_tax_allowance(self, aid_input: AidInput) -> float:
        student_earned = self._earned_student_only(aid_input)
        return self._medicare_allowance(student_earned, 200000) + min(student_earned * 0.062, 10453.2)

    def _independent_payroll_tax_allowance(self, aid_input: AidInput) -> float:
        student_earned = self._earned_student_only(aid_input)
        spouse_earned = max(aid_input.spouse_wages + aid_input.spouse_schedule_c_income, 0.0)
        total = student_earned + spouse_earned

        if self._is_student_married(aid_input):
            medicare = self._medicare_allowance(total, 250000)
            oasdi = min(total * 0.062, 20906.4)
        else:
            medicare = self._medicare_allowance(student_earned, 200000)
            oasdi = min(student_earned * 0.062, 10453.2)
        return medicare + oasdi

    @staticmethod
    def _medicare_allowance(earned_income: float, threshold: float) -> float:
        earned_income = max(earned_income, 0.0)
        if earned_income <= threshold:
            return earned_income * 0.0145
        return threshold * 0.0145 + (earned_income - threshold) * 0.0235

    @staticmethod
    def _adjusted_business_farm_value(net_worth: float) -> float:
        net_worth = max(net_worth, 0.0)
        if net_worth < 1:
            return 0.0
        if net_worth <= 175000:
            return net_worth * 0.4
        if net_worth <= 520000:
            return 70000 + (net_worth - 175000) * 0.5
        if net_worth <= 870000:
            return 242500 + (net_worth - 520000) * 0.6
        return 452500 + (net_worth - 870000)

    @staticmethod
    def _assessment_from_adjusted_available_income(aai: float) -> float:
        if aai < -8500:
            return -1870.0
        if aai <= 21800:
            return aai * 0.22
        if aai <= 27300:
            return 4796 + (aai - 21800) * 0.25
        if aai <= 32800:
            return 6171 + (aai - 27300) * 0.29
        if aai <= 38400:
            return 7766 + (aai - 32800) * 0.34
        if aai <= 43900:
            return 9670 + (aai - 38400) * 0.40
        return 11870 + (aai - 43900) * 0.47

    def _number_of_parents(self, aid_input: AidInput) -> int:
        count = int(aid_input.parent_1_dob is not None) + int(aid_input.parent_2_dob is not None)
        if count:
            return count
        if aid_input.parent_filing_status in MARRIED_JOINT_FILING | MARRIED_SEPARATE_FILING:
            return 2
        return 1

    @staticmethod
    def _is_student_unmarried(aid_input: AidInput) -> bool:
        return aid_input.student_marital_status in UNMARRIED_STUDENT_STATUSES

    @staticmethod
    def _is_student_married(aid_input: AidInput) -> bool:
        return aid_input.student_marital_status in MARRIED_STUDENT_STATUSES

    def _is_independent_single_parent(self, aid_input: AidInput) -> bool:
        return self._is_student_unmarried(aid_input) and aid_input.student_family_size > 1

    def _is_independent_parent_not_single(self, aid_input: AidInput) -> bool:
        return self._is_student_married(aid_input) and aid_input.student_family_size > 2

    def _poverty_guideline(self, state: str, family_size: int) -> float:
        family_size = max(1, family_size)
        bucket = self._state_bucket(state)
        if bucket == ALASKA:
            base, increment = 18810, 6730
        elif bucket == HAWAII:
            base, increment = 17310, 6190
        else:
            base, increment = 15060, 5380
        return float(base + max(family_size - 1, 0) * increment)

    @staticmethod
    def _state_bucket(state: str) -> str:
        value = str(state or "").strip().upper()
        if value == ALASKA:
            return ALASKA
        if value == HAWAII:
            return HAWAII
        return OTHER_STATE
