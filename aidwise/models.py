from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import date


@dataclass(slots=True)
class AidInput:
    dependency_status: str
    parent_family_size: int = 4
    parent_1_dob: date | None = None
    parent_2_dob: date | None = None
    parent_schedule_abhdef: str = "No"
    parent_schedule_c: str = "No"
    parent_received_benefits: str = "No"
    parent_state: str = "CT"
    parent_filing_status: str = "Married filing Jointly"
    parent_agi: float = 108000.0
    parent_ira_deductions: float = 0.0
    parent_tax_exempt_interest: float = 0.0
    parent_untaxed_pensions: float = 0.0
    parent_foreign_income_exclusion: float = 0.0
    parent_taxable_grants: float = 0.0
    parent_education_credits: float = 0.0
    parent_federal_work_study: float = 0.0
    parent_income_tax_paid: float = 10100.0
    parent_1_wages: float = 108000.0
    parent_1_schedule_c_income: float = 0.0
    parent_2_wages: float = 0.0
    parent_2_schedule_c_income: float = 0.0
    parent_child_support: float = 0.0
    parent_cash_savings: float = 600.0
    parent_investments: float = 0.0
    parent_business_farm: float = 0.0
    student_filing_status: str = "Single"
    student_agi: float = 0.0
    student_ira_deductions: float = 0.0
    student_tax_exempt_interest: float = 0.0
    student_untaxed_pensions: float = 0.0
    student_foreign_income_exclusion: float = 0.0
    student_taxable_grants: float = 0.0
    student_education_credits: float = 0.0
    student_federal_work_study: float = 0.0
    student_income_tax_paid: float = 0.0
    student_wages: float = 0.0
    student_schedule_c_income: float = 0.0
    spouse_wages: float = 0.0
    spouse_schedule_c_income: float = 0.0
    student_child_support: float = 0.0
    student_cash_savings: float = 0.0
    student_investments: float = 0.0
    student_business_farm: float = 0.0
    student_family_size: int = 1
    student_marital_status: str = "Single"
    student_dob: date | None = None
    student_schedule_abhdef: str = "No"
    student_schedule_c: str = "No"
    student_received_benefits: str = "No"
    student_state: str = "CT"

    def with_income_delta(self, income_delta: float) -> "AidInput":
        if self.dependency_status == "Dependent":
            return replace(
                self,
                parent_agi=max(self.parent_agi + income_delta, 0.0),
                parent_1_wages=max(self.parent_1_wages + income_delta, 0.0),
            )
        return replace(
            self,
            student_agi=max(self.student_agi + income_delta, 0.0),
            student_wages=max(self.student_wages + income_delta, 0.0),
        )


@dataclass(slots=True)
class CalculationResult:
    sai: int
    minimum_pell_eligible: bool
    maximum_pell_eligible: bool
    methodology: str
    formula_type: str = ""
    assets_required: bool | None = None
    rationale: list[str] = field(default_factory=list)
    warning: str = ""


@dataclass(slots=True)
class RetrievedPassage:
    source: str
    text: str
    score: float


@dataclass(slots=True)
class ScenarioComparison:
    baseline: CalculationResult
    scenario: CalculationResult
    summary: str


@dataclass(slots=True)
class QueryResponse:
    route: str
    answer: str
    evidence: list[RetrievedPassage]
    calculation: CalculationResult | None = None
    comparison: ScenarioComparison | None = None
    disclaimer: str = (
        "AidWise is an educational estimator and not an official FAFSA or Pell determination."
    )
