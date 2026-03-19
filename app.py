from __future__ import annotations

import pandas as pd
import streamlit as st

from aidwise.calculator import AidCalculator
from aidwise.csv_loader import dataframe_to_inputs, load_student_csv
from aidwise.models import QueryResponse
from aidwise.orchestrator import AidWiseOrchestrator
from aidwise.sources import template_csv_path


st.set_page_config(page_title="AidWise", page_icon=":bar_chart:", layout="wide")


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
            st.write(f"Formula type: `{response.calculation.formula_type}`")
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


def build_results_table(dataframe: pd.DataFrame, orchestrator: AidWiseOrchestrator) -> pd.DataFrame:
    aid_inputs = dataframe_to_inputs(dataframe)
    results = [orchestrator.calculator.calculate(aid_input) for aid_input in aid_inputs]

    output = dataframe.copy()
    output.insert(0, "row_number", range(1, len(output) + 1))
    output["formula_type"] = [result.formula_type for result in results]
    output["sai"] = [result.sai for result in results]
    output["minimum_pell"] = ["Yes" if result.minimum_pell_eligible else "No" for result in results]
    output["maximum_pell"] = ["Yes" if result.maximum_pell_eligible else "No" for result in results]
    output["assets_required"] = ["Yes" if result.assets_required else "No" for result in results]
    return output


def main() -> None:
    orchestrator = AidWiseOrchestrator()
    st.title("AidWise")
    st.write(
        "A grounded aid estimator for Student Aid Index and Pell eligibility. "
        "This proof of concept uses a pure Python calculator and a CSV upload of student records."
    )

    st.sidebar.header("Project status")
    sources = orchestrator.retriever.available_sources()
    st.sidebar.write(f"Policy sources loaded: {len(sources)}")
    for source in sources:
        st.sidebar.write(f"- {source}")

    template_path = template_csv_path()
    st.sidebar.caption(
        f"Template CSV: {template_path}"
    )

    upload_tab, chat_tab = st.tabs(["Upload CSV", "Ask questions"])

    with upload_tab:
        st.subheader("Student input CSV")
        st.write(
            "Upload a CSV whose columns match the AidWise input schema. "
            "Each row is treated as one student scenario."
        )
        uploader = st.file_uploader("Upload student CSV", type=["csv"])

        if uploader is None:
            st.info("Upload a CSV file to calculate SAI, Maximum Pell, and Minimum Pell.")
            if template_path.exists():
                st.write("A starter template is available in the project:")
                st.code(str(template_path))
            return

        try:
            dataframe = load_student_csv(uploader)
        except Exception as exc:
            st.error(f"Could not load CSV: {exc}")
            return

        results_table = build_results_table(dataframe, orchestrator)
        st.session_state["student_dataframe"] = dataframe
        st.session_state["results_table"] = results_table
        st.session_state["aid_inputs"] = dataframe_to_inputs(dataframe)

        st.subheader("Calculated results")
        st.dataframe(results_table, use_container_width=True)

        selected_row = st.selectbox(
            "Select a row for detailed explanation",
            options=list(results_table["row_number"]),
            index=0,
        )
        st.session_state["selected_row_number"] = selected_row
        selected_index = int(selected_row) - 1
        selected_input = st.session_state["aid_inputs"][selected_index]

        estimate_col, compare_col = st.columns([2, 1])
        with estimate_col:
            if st.button("Explain selected row", type="primary"):
                response = orchestrator.estimate(selected_input)
                st.session_state["last_response"] = response
        with compare_col:
            income_delta = st.number_input(
                "What-if income change",
                value=-5000.0,
                step=1000.0,
                help="Negative values simulate an income decrease.",
            )
            if st.button("Compare scenario"):
                response = orchestrator.compare_income_change(selected_input, income_delta)
                st.session_state["last_response"] = response

        response = st.session_state.get("last_response")
        if response:
            render_response(response)

    with chat_tab:
        st.subheader("Policy and explanation Q&A")
        aid_inputs = st.session_state.get("aid_inputs")
        selected_row = st.session_state.get("selected_row_number", 1)
        if not aid_inputs:
            st.info("Upload a CSV first so AidWise can answer questions about a specific student row.")
            return

        query = st.text_input(
            "Ask why this student got these results",
            placeholder="Why is row 1 eligible for minimum Pell but not maximum Pell?",
        )
        if st.button("Ask AidWise"):
            selected_input = aid_inputs[int(selected_row) - 1]
            response = orchestrator.answer(query, aid_input=selected_input)
            st.session_state["chat_response"] = response

        response = st.session_state.get("chat_response")
        if response:
            st.caption(f"Answering for uploaded CSV row {selected_row}.")
            render_response(response)


if __name__ == "__main__":
    main()
