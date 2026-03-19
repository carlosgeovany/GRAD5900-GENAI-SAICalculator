from __future__ import annotations

from io import BytesIO, StringIO
from pathlib import Path
from typing import BinaryIO

import pandas as pd

from aidwise.models import AidInput


def load_student_csv(uploaded_file: bytes | str | Path | BinaryIO) -> pd.DataFrame:
    if isinstance(uploaded_file, Path):
        dataframe = pd.read_csv(uploaded_file)
    elif isinstance(uploaded_file, (bytes, bytearray)):
        dataframe = pd.read_csv(BytesIO(uploaded_file))
    elif hasattr(uploaded_file, "read"):
        content = uploaded_file.read()
        if isinstance(content, bytes):
            dataframe = pd.read_csv(BytesIO(content))
        else:
            dataframe = pd.read_csv(StringIO(content))
    else:
        dataframe = pd.read_csv(uploaded_file)

    dataframe.columns = [str(column).strip() for column in dataframe.columns]
    missing = [column for column in AidInput.csv_columns() if column not in dataframe.columns]
    if missing:
        raise ValueError(
            "CSV is missing required columns: " + ", ".join(missing)
        )
    return dataframe


def dataframe_to_inputs(dataframe: pd.DataFrame) -> list[AidInput]:
    inputs: list[AidInput] = []
    for _, row in dataframe.iterrows():
        inputs.append(AidInput.from_mapping(row.to_dict()))
    return inputs


def template_dataframe() -> pd.DataFrame:
    demo = AidCalculatorTemplate.demo_row()
    return pd.DataFrame([demo], columns=AidInput.csv_columns())


class AidCalculatorTemplate:
    @staticmethod
    def demo_row() -> dict[str, object]:
        demo = AidInput(
            dependency_status="Dependent",
            parent_family_size=6,
            parent_1_dob=pd.Timestamp("1976-06-05").date(),
            parent_2_dob=pd.Timestamp("1983-08-10").date(),
            parent_schedule_abhdef="No",
            parent_schedule_c="No",
            parent_received_benefits="No",
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
        row = {column: getattr(demo, column) for column in AidInput.csv_columns()}
        return row
