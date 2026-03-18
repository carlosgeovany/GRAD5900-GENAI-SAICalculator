from __future__ import annotations

from datetime import date

import streamlit as st

from aidwise.calculator import WorkbookAidCalculator
from aidwise.models import AidInput, QueryResponse
from aidwise.orchestrator import AidWiseOrchestrator


st.set_page_config(page_title="AidWise", page_icon=":bar_chart:", layout="wide")

PARENT_FILING_OPTIONS = [
    "Single",
    "Head of Household",
    "Married filing Jointly",
    "Married filing Separate",
    "Qualifying surviving spouse",
    "Not required to file",
    "Non US Tax Return",
]

STUDENT_MARITAL_OPTIONS = [
    "Single",
    "Married",
    "Remarried",
    "Separated",
    "Divorced",
    "Widowed",
]

YES_NO = ["No", "Yes"]


def _select_index(options: list[str], value: str) -> int:
    try:
        return options.index(value)
    except ValueError:
        return 0


def default_input() -> AidInput:
    return WorkbookAidCalculator.canonical_demo_input()


def build_input() -> AidInput:
    defaults = st.session_state.get("aidwise_defaults")
    if defaults is None:
        defaults = default_input()
        st.session_state["aidwise_defaults"] = defaults

    general_col, dependency_col = st.columns(2)
    with general_col:
        dependency_status = st.selectbox(
            "Dependency status",
            ["Dependent", "Independent"],
            index=_select_index(["Dependent", "Independent"], defaults.dependency_status),
        )
    with dependency_col:
        parent_family_size = st.number_input(
            "Parent family size",
            min_value=1,
            step=1,
            value=int(defaults.parent_family_size),
        )

    st.markdown("### Parent inputs")
    parent_col1, parent_col2, parent_col3 = st.columns(3)
    with parent_col1:
        parent_1_dob = st.date_input(
            "Parent 1 DOB",
            value=defaults.parent_1_dob or date(1976, 6, 5),
        )
        parent_schedule_abhdef = st.selectbox(
            "Parent filed Schedule A/B/D/E/F/H",
            YES_NO,
            index=_select_index(YES_NO, defaults.parent_schedule_abhdef),
        )
        parent_received_benefits = st.selectbox(
            "Parent received federal benefits",
            YES_NO,
            index=_select_index(YES_NO, defaults.parent_received_benefits),
        )
        parent_filing_status = st.selectbox(
            "Parent filing status",
            PARENT_FILING_OPTIONS,
            index=_select_index(PARENT_FILING_OPTIONS, defaults.parent_filing_status),
        )
        parent_agi = st.number_input(
            "Parent AGI",
            min_value=0.0,
            step=1000.0,
            value=float(defaults.parent_agi),
        )
        parent_income_tax_paid = st.number_input(
            "Parent income tax paid",
            min_value=0.0,
            step=500.0,
            value=float(defaults.parent_income_tax_paid),
        )
        parent_1_wages = st.number_input(
            "Parent 1 wages",
            min_value=0.0,
            step=1000.0,
            value=float(defaults.parent_1_wages),
        )
        parent_cash_savings = st.number_input(
            "Parent cash and savings",
            min_value=0.0,
            step=500.0,
            value=float(defaults.parent_cash_savings),
        )
        parent_business_farm = st.number_input(
            "Parent business or farm net worth",
            min_value=0.0,
            step=1000.0,
            value=float(defaults.parent_business_farm),
        )
    with parent_col2:
        parent_2_dob = st.date_input(
            "Parent 2 DOB",
            value=defaults.parent_2_dob or date(1983, 8, 10),
        )
        parent_schedule_c = st.selectbox(
            "Parent filed Schedule C",
            YES_NO,
            index=_select_index(YES_NO, defaults.parent_schedule_c),
        )
        parent_state = st.text_input("Parent state", value=defaults.parent_state)
        parent_ira_deductions = st.number_input(
            "Parent IRA deductions",
            min_value=0.0,
            step=100.0,
            value=float(defaults.parent_ira_deductions),
        )
        parent_tax_exempt_interest = st.number_input(
            "Parent tax-exempt interest",
            min_value=0.0,
            step=100.0,
            value=float(defaults.parent_tax_exempt_interest),
        )
        parent_untaxed_pensions = st.number_input(
            "Parent untaxed IRA and pensions",
            min_value=0.0,
            step=100.0,
            value=float(defaults.parent_untaxed_pensions),
        )
        parent_1_schedule_c_income = st.number_input(
            "Parent 1 Schedule C income",
            step=100.0,
            value=float(defaults.parent_1_schedule_c_income),
        )
        parent_2_wages = st.number_input(
            "Parent 2 wages",
            min_value=0.0,
            step=1000.0,
            value=float(defaults.parent_2_wages),
        )
        parent_investments = st.number_input(
            "Parent investments",
            min_value=0.0,
            step=500.0,
            value=float(defaults.parent_investments),
        )
    with parent_col3:
        parent_foreign_income_exclusion = st.number_input(
            "Parent foreign income exclusion",
            min_value=0.0,
            step=100.0,
            value=float(defaults.parent_foreign_income_exclusion),
        )
        parent_taxable_grants = st.number_input(
            "Parent taxable grants",
            min_value=0.0,
            step=100.0,
            value=float(defaults.parent_taxable_grants),
        )
        parent_education_credits = st.number_input(
            "Parent education credits",
            min_value=0.0,
            step=100.0,
            value=float(defaults.parent_education_credits),
        )
        parent_federal_work_study = st.number_input(
            "Parent federal work-study",
            min_value=0.0,
            step=100.0,
            value=float(defaults.parent_federal_work_study),
        )
        parent_2_schedule_c_income = st.number_input(
            "Parent 2 Schedule C income",
            step=100.0,
            value=float(defaults.parent_2_schedule_c_income),
        )
        parent_child_support = st.number_input(
            "Parent child support received",
            min_value=0.0,
            step=100.0,
            value=float(defaults.parent_child_support),
        )

    st.markdown("### Student inputs")
    student_col1, student_col2, student_col3 = st.columns(3)
    with student_col1:
        student_filing_status = st.selectbox(
            "Student filing status",
            PARENT_FILING_OPTIONS,
            index=_select_index(PARENT_FILING_OPTIONS, defaults.student_filing_status),
        )
        student_agi = st.number_input(
            "Student AGI",
            min_value=0.0,
            step=500.0,
            value=float(defaults.student_agi),
        )
        student_income_tax_paid = st.number_input(
            "Student income tax paid",
            min_value=0.0,
            step=100.0,
            value=float(defaults.student_income_tax_paid),
        )
        student_wages = st.number_input(
            "Student wages",
            min_value=0.0,
            step=500.0,
            value=float(defaults.student_wages),
        )
        student_cash_savings = st.number_input(
            "Student cash and savings",
            min_value=0.0,
            step=100.0,
            value=float(defaults.student_cash_savings),
        )
        student_family_size = st.number_input(
            "Student family size",
            min_value=1,
            step=1,
            value=int(max(defaults.student_family_size, 1)),
        )
        student_dob = st.date_input(
            "Student DOB",
            value=defaults.student_dob or date(2006, 2, 6),
        )
    with student_col2:
        student_ira_deductions = st.number_input(
            "Student IRA deductions",
            min_value=0.0,
            step=100.0,
            value=float(defaults.student_ira_deductions),
        )
        student_tax_exempt_interest = st.number_input(
            "Student tax-exempt interest",
            min_value=0.0,
            step=100.0,
            value=float(defaults.student_tax_exempt_interest),
        )
        student_untaxed_pensions = st.number_input(
            "Student untaxed IRA and pensions",
            min_value=0.0,
            step=100.0,
            value=float(defaults.student_untaxed_pensions),
        )
        student_foreign_income_exclusion = st.number_input(
            "Student foreign income exclusion",
            min_value=0.0,
            step=100.0,
            value=float(defaults.student_foreign_income_exclusion),
        )
        student_schedule_c_income = st.number_input(
            "Student Schedule C income",
            step=100.0,
            value=float(defaults.student_schedule_c_income),
        )
        spouse_wages = st.number_input(
            "Spouse wages",
            min_value=0.0,
            step=500.0,
            value=float(defaults.spouse_wages),
        )
        student_investments = st.number_input(
            "Student investments",
            min_value=0.0,
            step=100.0,
            value=float(defaults.student_investments),
        )
    with student_col3:
        student_taxable_grants = st.number_input(
            "Student taxable grants",
            min_value=0.0,
            step=100.0,
            value=float(defaults.student_taxable_grants),
        )
        student_education_credits = st.number_input(
            "Student education credits",
            min_value=0.0,
            step=100.0,
            value=float(defaults.student_education_credits),
        )
        student_federal_work_study = st.number_input(
            "Student federal work-study",
            min_value=0.0,
            step=100.0,
            value=float(defaults.student_federal_work_study),
        )
        spouse_schedule_c_income = st.number_input(
            "Spouse Schedule C income",
            step=100.0,
            value=float(defaults.spouse_schedule_c_income),
        )
        student_child_support = st.number_input(
            "Student child support received",
            min_value=0.0,
            step=100.0,
            value=float(defaults.student_child_support),
        )
        student_business_farm = st.number_input(
            "Student business or farm net worth",
            min_value=0.0,
            step=100.0,
            value=float(defaults.student_business_farm),
        )
        student_state = st.text_input("Student state", value=defaults.student_state)

    student_meta_col1, student_meta_col2 = st.columns(2)
    with student_meta_col1:
        student_marital_status = st.selectbox(
            "Student marital status",
            STUDENT_MARITAL_OPTIONS,
            index=_select_index(STUDENT_MARITAL_OPTIONS, defaults.student_marital_status),
        )
        student_schedule_abhdef = st.selectbox(
            "Student filed Schedule A/B/D/E/F/H",
            YES_NO,
            index=_select_index(YES_NO, defaults.student_schedule_abhdef),
        )
    with student_meta_col2:
        student_schedule_c = st.selectbox(
            "Student filed Schedule C",
            YES_NO,
            index=_select_index(YES_NO, defaults.student_schedule_c),
        )
        student_received_benefits = st.selectbox(
            "Student received federal benefits",
            YES_NO,
            index=_select_index(YES_NO, defaults.student_received_benefits),
        )

    return AidInput(
        dependency_status=dependency_status,
        parent_family_size=int(parent_family_size),
        parent_1_dob=parent_1_dob,
        parent_2_dob=parent_2_dob,
        parent_schedule_abhdef=parent_schedule_abhdef,
        parent_schedule_c=parent_schedule_c,
        parent_received_benefits=parent_received_benefits,
        parent_state=parent_state.strip().upper(),
        parent_filing_status=parent_filing_status,
        parent_agi=parent_agi,
        parent_ira_deductions=parent_ira_deductions,
        parent_tax_exempt_interest=parent_tax_exempt_interest,
        parent_untaxed_pensions=parent_untaxed_pensions,
        parent_foreign_income_exclusion=parent_foreign_income_exclusion,
        parent_taxable_grants=parent_taxable_grants,
        parent_education_credits=parent_education_credits,
        parent_federal_work_study=parent_federal_work_study,
        parent_income_tax_paid=parent_income_tax_paid,
        parent_1_wages=parent_1_wages,
        parent_1_schedule_c_income=parent_1_schedule_c_income,
        parent_2_wages=parent_2_wages,
        parent_2_schedule_c_income=parent_2_schedule_c_income,
        parent_child_support=parent_child_support,
        parent_cash_savings=parent_cash_savings,
        parent_investments=parent_investments,
        parent_business_farm=parent_business_farm,
        student_filing_status=student_filing_status,
        student_agi=student_agi,
        student_ira_deductions=student_ira_deductions,
        student_tax_exempt_interest=student_tax_exempt_interest,
        student_untaxed_pensions=student_untaxed_pensions,
        student_foreign_income_exclusion=student_foreign_income_exclusion,
        student_taxable_grants=student_taxable_grants,
        student_education_credits=student_education_credits,
        student_federal_work_study=student_federal_work_study,
        student_income_tax_paid=student_income_tax_paid,
        student_wages=student_wages,
        student_schedule_c_income=student_schedule_c_income,
        spouse_wages=spouse_wages,
        spouse_schedule_c_income=spouse_schedule_c_income,
        student_child_support=student_child_support,
        student_cash_savings=student_cash_savings,
        student_investments=student_investments,
        student_business_farm=student_business_farm,
        student_family_size=int(student_family_size),
        student_marital_status=student_marital_status,
        student_dob=student_dob,
        student_schedule_abhdef=student_schedule_abhdef,
        student_schedule_c=student_schedule_c,
        student_received_benefits=student_received_benefits,
        student_state=student_state.strip().upper(),
    )


def render_response(response: QueryResponse) -> None:
    if response.calculation:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Estimated SAI", response.calculation.sai)
        col2.metric(
            "Minimum Pell",
            "Yes" if response.calculation.minimum_pell_eligible else "No",
        )
        col3.metric(
            "Maximum Pell",
            "Yes" if response.calculation.maximum_pell_eligible else "No",
        )
        col4.metric(
            "Assets Required",
            "Yes" if response.calculation.assets_required else "No",
        )
        st.caption(response.calculation.methodology)
        if response.calculation.formula_type:
            st.write(f"Workbook formula: `{response.calculation.formula_type}`")
        if response.calculation.warning:
            st.warning(response.calculation.warning)

        if response.calculation.rationale:
            st.subheader("Calculation notes")
            for item in response.calculation.rationale:
                st.write(f"- {item}")

    if response.comparison:
        st.subheader("Scenario comparison")
        st.info(response.comparison.summary)

    st.subheader("Explanation")
    st.write(response.answer)

    st.subheader("Evidence")
    if response.evidence:
        for item in response.evidence:
            st.markdown(f"**{item.source}**")
            st.write(item.text)
    else:
        st.write("No policy sources are loaded yet. Add files to `data/policy/`.")

    st.caption(response.disclaimer)


def main() -> None:
    orchestrator = AidWiseOrchestrator()
    st.title("AidWise")
    st.write(
        "A grounded aid estimator for Student Aid Index and Pell eligibility. "
        "This version uses the supplied Excel workbook through local Excel automation when available."
    )

    st.sidebar.header("Project status")
    sources = orchestrator.retriever.available_sources()
    st.sidebar.write(f"Policy sources loaded: {len(sources)}")
    for source in sources:
        st.sidebar.write(f"- {source}")

    workbook_path = getattr(orchestrator.calculator, "workbook_path", None)
    st.sidebar.write(
        f"Workbook mode: {'Ready' if orchestrator.calculator.is_ready() else 'Fallback'}"
    )
    if workbook_path:
        st.sidebar.write(f"Workbook: {workbook_path.name}")
    st.sidebar.caption(
        "AidWise checks `data/models/` first and then `data/policy/` for the workbook."
    )

    tab_estimate, tab_chat = st.tabs(["Estimate aid", "Ask questions"])

    with tab_estimate:
        st.subheader("Aid estimation")
        aid_input = build_input()
        st.session_state["aid_input"] = aid_input

        estimate_col, compare_col = st.columns([2, 1])
        with estimate_col:
            if st.button("Run estimate", type="primary"):
                response = orchestrator.estimate(aid_input)
                st.session_state["last_response"] = response
        with compare_col:
            income_delta = st.number_input(
                "What-if income change",
                value=-5000.0,
                step=1000.0,
                help="Negative values simulate an income decrease.",
            )
            if st.button("Compare scenario"):
                response = orchestrator.compare_income_change(aid_input, income_delta)
                st.session_state["last_response"] = response

        response = st.session_state.get("last_response")
        if response:
            render_response(response)

    with tab_chat:
        st.subheader("Policy and explanation Q&A")
        query = st.text_input(
            "Ask about SAI, Pell, or why a result changed",
            placeholder="What is SAI and what if family income decreases?",
        )
        if st.button("Ask AidWise"):
            aid_input = st.session_state.get("aid_input")
            response = orchestrator.answer(query, aid_input=aid_input)
            st.session_state["chat_response"] = response

        response = st.session_state.get("chat_response")
        if response:
            render_response(response)


if __name__ == "__main__":
    main()
