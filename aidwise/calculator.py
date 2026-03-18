from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
import shutil
import tempfile

import pythoncom

from aidwise.models import AidInput, CalculationResult, ScenarioComparison
from aidwise.sources import find_workbook

try:
    import win32com.client
except ImportError:  # pragma: no cover
    win32com = None


YES = "Yes"
NO = "No"


class PrototypeAidCalculator:
    """Fallback logic when the official workbook cannot be executed."""

    methodology = (
        "Fallback heuristic mode. The official workbook was not available, so AidWise "
        "used a simplified estimate instead of the validated Excel model."
    )

    def calculate(self, aid_input: AidInput) -> CalculationResult:
        if aid_input.dependency_status == "Dependent":
            income_total = aid_input.parent_agi + aid_input.student_agi
            asset_total = (
                aid_input.parent_cash_savings
                + aid_input.parent_investments
                + aid_input.parent_business_farm
                + aid_input.student_cash_savings
                + aid_input.student_investments
                + aid_input.student_business_farm
            )
            family_size = aid_input.parent_family_size
        else:
            income_total = aid_input.student_agi
            asset_total = (
                aid_input.student_cash_savings
                + aid_input.student_investments
                + aid_input.student_business_farm
            )
            family_size = aid_input.student_family_size

        discretionary_income = max(income_total - max(family_size - 1, 0) * 6_000, 0)
        sai = max(-1_500, round(discretionary_income * 0.22 + asset_total * 0.12) - 1_500)

        return CalculationResult(
            sai=sai,
            minimum_pell_eligible=sai <= 7_395,
            maximum_pell_eligible=sai <= 0,
            methodology=self.methodology,
            rationale=[
                f"Fallback income basis: ${income_total:,.0f}",
                f"Fallback asset basis: ${asset_total:,.0f}",
            ],
            warning=(
                "Excel automation or the official workbook was unavailable, so this estimate "
                "uses fallback logic."
            ),
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
                f"the estimated SAI changes from {baseline.sai} to {scenario.sai}."
            ),
        )


class WorkbookAidCalculator:
    methodology = (
        "Workbook-backed mode. AidWise uses the provided Excel calculator through local "
        "Excel automation so the estimate follows the supplied institutional model."
    )

    def __init__(self, workbook_path: str | Path | None = None):
        self.workbook_path = Path(workbook_path) if workbook_path else find_workbook()
        self.fallback = PrototypeAidCalculator()

    def is_ready(self) -> bool:
        return self.workbook_path is not None and win32com is not None

    def calculate(self, aid_input: AidInput) -> CalculationResult:
        if not self.is_ready():
            return self.fallback.calculate(aid_input)

        excel = None
        workbook = None
        temp_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                suffix=self.workbook_path.suffix,
                delete=False,
            ) as temp_file:
                temp_path = Path(temp_file.name)
            shutil.copy2(self.workbook_path, temp_path)

            pythoncom.CoInitialize()
            excel = win32com.client.DispatchEx("Excel.Application")
            excel.Visible = False
            excel.DisplayAlerts = False
            excel.AutomationSecurity = 3
            workbook = excel.Workbooks.Open(str(temp_path), ReadOnly=False)
            sheet = workbook.Worksheets("Calculator")

            for cell, value in self._to_workbook_values(aid_input).items():
                sheet.Range(cell).Value = value

            excel.CalculateFullRebuild()

            formula_type = self._text(sheet.Range("O16").Value)
            sai_value = sheet.Range("O17").Value
            max_pell = self._is_yes(sheet.Range("O18").Value)
            min_pell = self._is_yes(sheet.Range("O19").Value)
            assets_required = self._is_yes(sheet.Range("O20").Value)

            result = CalculationResult(
                sai=int(round(float(sai_value))),
                minimum_pell_eligible=min_pell,
                maximum_pell_eligible=max_pell,
                methodology=self.methodology,
                formula_type=formula_type,
                assets_required=assets_required,
                rationale=[
                    f"Workbook formula selected: {formula_type}",
                    f"Assets required by workbook: {YES if assets_required else NO}",
                    f"Workbook source: {self.workbook_path.name}",
                ],
            )
            if self.workbook_path.parent.name.lower() != "models":
                result.warning = (
                    "The workbook was found outside `data/models/`, but AidWise still used it "
                    "successfully."
                )
            return result
        except Exception as exc:
            fallback = self.fallback.calculate(aid_input)
            fallback.warning = (
                "AidWise could not execute the official workbook and fell back to the starter "
                f"calculator. Error: {exc}"
            )
            return fallback
        finally:
            if workbook is not None:
                workbook.Close(False)
            if excel is not None:
                excel.Quit()
            if temp_path is not None and temp_path.exists():
                temp_path.unlink(missing_ok=True)
            pythoncom.CoUninitialize()

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
                f"the workbook-backed SAI changes from {baseline.sai} to {scenario.sai}."
            ),
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

    def load_calculator_demo_input(self) -> AidInput:
        if self.workbook_path is None:
            return self.canonical_demo_input()

        from openpyxl import load_workbook

        workbook = load_workbook(self.workbook_path, data_only=True, keep_vba=True)
        sheet = workbook["Calculator"]
        return AidInput(
            dependency_status=self._text(sheet["B3"].value) or "Dependent",
            parent_family_size=int(sheet["B5"].value or 4),
            parent_1_dob=self._date(sheet["B6"].value),
            parent_2_dob=self._date(sheet["B7"].value),
            parent_schedule_abhdef=self._text(sheet["B8"].value) or NO,
            parent_schedule_c=self._text(sheet["B9"].value) or NO,
            parent_received_benefits=self._text(sheet["B10"].value) or NO,
            parent_state=self._text(sheet["B11"].value) or "CT",
            parent_filing_status=self._text(sheet["B13"].value) or "Married filing Jointly",
            parent_agi=float(sheet["B14"].value or 0),
            parent_ira_deductions=float(sheet["B15"].value or 0),
            parent_tax_exempt_interest=float(sheet["B16"].value or 0),
            parent_untaxed_pensions=float(sheet["B17"].value or 0),
            parent_foreign_income_exclusion=float(sheet["B18"].value or 0),
            parent_taxable_grants=float(sheet["B19"].value or 0),
            parent_education_credits=float(sheet["B20"].value or 0),
            parent_federal_work_study=float(sheet["B21"].value or 0),
            parent_income_tax_paid=float(sheet["B22"].value or 0),
            parent_1_wages=float(sheet["B23"].value or 0),
            parent_1_schedule_c_income=float(sheet["B24"].value or 0),
            parent_2_wages=float(sheet["B25"].value or 0),
            parent_2_schedule_c_income=float(sheet["B26"].value or 0),
            parent_child_support=float(sheet["B27"].value or 0),
            parent_cash_savings=float(sheet["B28"].value or 0),
            parent_investments=float(sheet["B29"].value or 0),
            parent_business_farm=float(sheet["B30"].value or 0),
            student_filing_status=self._text(sheet["B32"].value) or "Single",
            student_agi=float(sheet["B33"].value or 0),
            student_ira_deductions=float(sheet["B34"].value or 0),
            student_tax_exempt_interest=float(sheet["B35"].value or 0),
            student_untaxed_pensions=float(sheet["B36"].value or 0),
            student_foreign_income_exclusion=float(sheet["B37"].value or 0),
            student_taxable_grants=float(sheet["B38"].value or 0),
            student_education_credits=float(sheet["B39"].value or 0),
            student_federal_work_study=float(sheet["B40"].value or 0),
            student_income_tax_paid=float(sheet["B41"].value or 0),
            student_wages=float(sheet["B42"].value or 0),
            student_schedule_c_income=float(sheet["B43"].value or 0),
            spouse_wages=float(sheet["B44"].value or 0),
            spouse_schedule_c_income=float(sheet["B45"].value or 0),
            student_child_support=float(sheet["B46"].value or 0),
            student_cash_savings=float(sheet["B47"].value or 0),
            student_investments=float(sheet["B48"].value or 0),
            student_business_farm=float(sheet["B49"].value or 0),
            student_family_size=int(sheet["B51"].value or 1),
            student_marital_status=self._text(sheet["B52"].value) or "Single",
            student_dob=self._date(sheet["B53"].value),
            student_schedule_abhdef=self._text(sheet["B54"].value) or NO,
            student_schedule_c=self._text(sheet["B55"].value) or NO,
            student_received_benefits=self._text(sheet["B56"].value) or NO,
            student_state=self._text(sheet["B57"].value) or "CT",
        )

    @staticmethod
    def _date(value: object) -> date | None:
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        return None

    @staticmethod
    def _text(value: object) -> str:
        return "" if value is None else str(value).strip()

    @staticmethod
    def _is_yes(value: object) -> bool:
        return str(value).strip().lower() == "yes"

    def _to_workbook_values(self, aid_input: AidInput) -> dict[str, object]:
        return {
            "B3": aid_input.dependency_status,
            "B5": aid_input.parent_family_size,
            "B6": self._excel_date(aid_input.parent_1_dob),
            "B7": self._excel_date(aid_input.parent_2_dob),
            "B8": aid_input.parent_schedule_abhdef,
            "B9": aid_input.parent_schedule_c,
            "B10": aid_input.parent_received_benefits,
            "B11": aid_input.parent_state,
            "B13": aid_input.parent_filing_status,
            "B14": aid_input.parent_agi,
            "B15": aid_input.parent_ira_deductions,
            "B16": aid_input.parent_tax_exempt_interest,
            "B17": aid_input.parent_untaxed_pensions,
            "B18": aid_input.parent_foreign_income_exclusion,
            "B19": aid_input.parent_taxable_grants,
            "B20": aid_input.parent_education_credits,
            "B21": aid_input.parent_federal_work_study,
            "B22": aid_input.parent_income_tax_paid,
            "B23": aid_input.parent_1_wages,
            "B24": aid_input.parent_1_schedule_c_income,
            "B25": aid_input.parent_2_wages,
            "B26": aid_input.parent_2_schedule_c_income,
            "B27": aid_input.parent_child_support,
            "B28": aid_input.parent_cash_savings,
            "B29": aid_input.parent_investments,
            "B30": aid_input.parent_business_farm,
            "B32": aid_input.student_filing_status,
            "B33": aid_input.student_agi,
            "B34": aid_input.student_ira_deductions,
            "B35": aid_input.student_tax_exempt_interest,
            "B36": aid_input.student_untaxed_pensions,
            "B37": aid_input.student_foreign_income_exclusion,
            "B38": aid_input.student_taxable_grants,
            "B39": aid_input.student_education_credits,
            "B40": aid_input.student_federal_work_study,
            "B41": aid_input.student_income_tax_paid,
            "B42": aid_input.student_wages,
            "B43": aid_input.student_schedule_c_income,
            "B44": aid_input.spouse_wages,
            "B45": aid_input.spouse_schedule_c_income,
            "B46": aid_input.student_child_support,
            "B47": aid_input.student_cash_savings,
            "B48": aid_input.student_investments,
            "B49": aid_input.student_business_farm,
            "B51": aid_input.student_family_size,
            "B52": aid_input.student_marital_status,
            "B53": self._excel_date(aid_input.student_dob),
            "B54": aid_input.student_schedule_abhdef,
            "B55": aid_input.student_schedule_c,
            "B56": aid_input.student_received_benefits,
            "B57": aid_input.student_state,
        }

    @staticmethod
    def _excel_date(value: date | None) -> object:
        if value is None:
            return ""
        return datetime.combine(value, datetime.min.time())
