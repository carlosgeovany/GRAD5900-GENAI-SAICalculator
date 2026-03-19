# AidWise

AidWise is a grounded proof of concept for estimating Student Aid Index (SAI), Maximum Pell, and Minimum Pell from student input data. This version no longer depends on Excel at runtime. The calculator is implemented in Python, the policy guide is used for grounded retrieval, and the app accepts student records as CSV input.

Current version: `0.2.0`

## What this version does

- Upload a CSV file with the student fields needed for the calculation
- Compute:
  - SAI
  - Minimum Pell eligibility
  - Maximum Pell eligibility
  - formula type
  - assets-required flag
- Answer policy and explanation questions about a selected student row
- Retrieve supporting passages from local policy documents in `data/policy/`
- Use the OpenAI API for grounded explanations when available
- Fall back to a deterministic local explanation when no API key is configured

## What changed in `v0.2.0`

- Removed the Excel workbook from the runtime path
- Replaced workbook execution with a pure Python calculation engine
- Switched the user input flow from manual form entry to CSV upload
- Kept the grounded Q&A and explanation workflow so users can ask why a student got a result

## Project structure

```text
.
|-- app.py
|-- aidwise/
|   |-- calculator.py
|   |-- csv_loader.py
|   |-- llm.py
|   |-- models.py
|   |-- orchestrator.py
|   |-- retrieval.py
|   |-- routing.py
|   `-- sources.py
|-- data/
|   |-- policy/
|   `-- templates/
|-- tests/
|-- requirements.txt
`-- README.md
```

## Setup

### 1. Create and activate a virtual environment

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```powershell
pip install -r requirements.txt
```

### 3. Configure OpenAI

```powershell
$env:OPENAI_API_KEY="your_api_key_here"
$env:OPENAI_MODEL="gpt-5-mini"
```

If `OPENAI_API_KEY` is not set, AidWise still runs and uses a local fallback explanation.

### 4. Add the policy guide

Put the official policy document in:

- `data/policy/`

Supported file types:

- `.pdf`
- `.txt`
- `.md`

## CSV input format

AidWise expects one student per row. The CSV must include every field in the `AidInput` schema.

A starter template is included here:

- `data/templates/student_input_template.csv`

Key columns include:

- `dependency_status`
- `parent_family_size`
- `parent_filing_status`
- `parent_agi`
- `parent_income_tax_paid`
- `parent_1_wages`
- `student_filing_status`
- `student_agi`
- `student_family_size`
- `student_marital_status`

The template includes all required columns, including optional fields that default to `0`, `No`, or blank dates.

## Run the app

```powershell
streamlit run app.py
```

Workflow:

1. Upload a CSV file.
2. Review the calculated results table.
3. Select a student row.
4. Ask AidWise to explain the result or run a what-if income comparison.
5. Ask follow-up questions about why that student got the displayed outcome.

## Run tests

```powershell
python -m unittest discover -s tests
```

## How the POC works

### Calculation engine

The calculator is now implemented directly in Python. It computes SAI and Pell-related outputs from structured student data without calling Excel or VBA.

### Retrieval

The retriever scans local policy files, extracts text, chunks it, and returns the top matching passages with a lightweight keyword-overlap search. This keeps explanations tied to the supplied policy guide.

### Explanation layer

AidWise combines:

- query routing
- calculated outputs
- retrieved policy evidence

and then generates a grounded explanation. When the OpenAI API is unavailable, AidWise returns a deterministic fallback explanation instead.

## Verification status

Current automated checks:

- `python -m unittest discover -s tests`
- `python -m compileall .`

The canonical demo scenario currently validates to:

- `Formula A`
- `SAI = 5041`
- `Minimum Pell = Yes`
- `Maximum Pell = No`
- `Assets Required = Yes`

## Current limitations

- This is still an educational estimator, not an official federal aid determination
- Retrieval is intentionally lightweight and does not yet use vector search
- Validation should be expanded with more policy scenarios and edge cases
- Explanations are only as grounded as the local policy files you provide

## Disclaimer

AidWise is an educational estimation and explanation system. It does not replace FAFSA, institutional aid systems, or official Department of Education determinations.
