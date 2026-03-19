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

AidWise expects one student per row. The CSV must include every column in the `AidInput` schema, even if some values are left blank or set to `0`.

A starter template is included here:

- `data/templates/student_input_template.csv`

The safest workflow is:

1. Copy `data/templates/student_input_template.csv`
2. Keep the header row exactly as-is
3. Add one student per row
4. Leave unused numeric fields as `0`
5. Leave optional date fields blank if they do not apply

### Formatting rules

- One student per row
- The first row must be the header row
- Column names must match exactly
- Date fields should use `YYYY-MM-DD`
- Numeric fields should be plain numbers like `108000` or `600.50`
- Yes/no fields should use `Yes` or `No`
- Blank optional date cells are allowed
- Blank numeric cells are treated as `0`

### Required header columns

Use this exact header order:

```csv
dependency_status,parent_family_size,parent_1_dob,parent_2_dob,parent_schedule_abhdef,parent_schedule_c,parent_received_benefits,parent_state,parent_filing_status,parent_agi,parent_ira_deductions,parent_tax_exempt_interest,parent_untaxed_pensions,parent_foreign_income_exclusion,parent_taxable_grants,parent_education_credits,parent_federal_work_study,parent_income_tax_paid,parent_1_wages,parent_1_schedule_c_income,parent_2_wages,parent_2_schedule_c_income,parent_child_support,parent_cash_savings,parent_investments,parent_business_farm,student_filing_status,student_agi,student_ira_deductions,student_tax_exempt_interest,student_untaxed_pensions,student_foreign_income_exclusion,student_taxable_grants,student_education_credits,student_federal_work_study,student_income_tax_paid,student_wages,student_schedule_c_income,spouse_wages,spouse_schedule_c_income,student_child_support,student_cash_savings,student_investments,student_business_farm,student_family_size,student_marital_status,student_dob,student_schedule_abhdef,student_schedule_c,student_received_benefits,student_state
```

### Column guide

Core identifiers:

- `dependency_status`: `Dependent` or `Independent`
- `parent_family_size`: household size for dependent-student parent calculation
- `student_family_size`: household size for the student calculation
- `student_marital_status`: for example `Single`, `Married`, `Remarried`, `Separated`, `Divorced`, `Widowed`
- `parent_filing_status`: for example `Married filing Jointly`, `Married filing Separate`, `Single`, `Head of Household`, `Qualifying surviving spouse`, `Not required to file`
- `student_filing_status`: for example `Single`, `Married filing Jointly`, `Married filing Separate`, `Head of Household`, `Not required to file`

Date fields:

- `parent_1_dob`
- `parent_2_dob`
- `student_dob`

Parent yes/no fields:

- `parent_schedule_abhdef`
- `parent_schedule_c`
- `parent_received_benefits`

Student yes/no fields:

- `student_schedule_abhdef`
- `student_schedule_c`
- `student_received_benefits`

Parent location and income fields:

- `parent_state`
- `parent_agi`
- `parent_ira_deductions`
- `parent_tax_exempt_interest`
- `parent_untaxed_pensions`
- `parent_foreign_income_exclusion`
- `parent_taxable_grants`
- `parent_education_credits`
- `parent_federal_work_study`
- `parent_income_tax_paid`

Parent earnings and assets:

- `parent_1_wages`
- `parent_1_schedule_c_income`
- `parent_2_wages`
- `parent_2_schedule_c_income`
- `parent_child_support`
- `parent_cash_savings`
- `parent_investments`
- `parent_business_farm`

Student and spouse income fields:

- `student_agi`
- `student_ira_deductions`
- `student_tax_exempt_interest`
- `student_untaxed_pensions`
- `student_foreign_income_exclusion`
- `student_taxable_grants`
- `student_education_credits`
- `student_federal_work_study`
- `student_income_tax_paid`
- `student_wages`
- `student_schedule_c_income`
- `spouse_wages`
- `spouse_schedule_c_income`

Student asset fields:

- `student_child_support`
- `student_cash_savings`
- `student_investments`
- `student_business_farm`
- `student_state`

### Minimal row behavior

Even though every header must be present, many rows will use only part of the schema:

- A dependent student will mostly use the parent fields plus a smaller set of student fields
- An independent student will mostly use the student and spouse fields
- If a field does not apply, keep the column and use `0`, `No`, or a blank date

### Example row

The included template already contains a working example row. A shortened illustration looks like this:

```csv
dependency_status,parent_family_size,parent_1_dob,parent_2_dob,parent_schedule_abhdef,parent_schedule_c,parent_received_benefits,parent_state,parent_filing_status,parent_agi,parent_income_tax_paid,parent_1_wages,student_filing_status,student_agi,student_family_size,student_marital_status,student_dob,student_state
Dependent,6,1976-06-05,1983-08-10,No,No,No,CT,Married filing Jointly,108000,10100,108000,Single,0,1,Single,2006-02-06,CT
```

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
