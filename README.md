# AidWise

AidWise is a grounded financial aid estimation app for Student Aid Index (SAI) and Pell Grant eligibility. This version uses the official PDF for grounded policy retrieval and the provided Excel workbook for deterministic calculations through local Excel automation.

Current version: `0.1.0`

## What is implemented now

- A Streamlit interface for structured SAI and Pell inputs
- A workbook-backed calculator that writes inputs into the `Calculator` tab and reads back:
  - SAI
  - minimum Pell indicator
  - maximum Pell indicator
  - assets-required flag
  - selected formula type
- Grounded retrieval over local policy documents in `data/policy/`
- Query routing for informational, calculation, explanation, and what-if requests
- An OpenAI explanation layer with a local fallback when no API key is configured
- Tests that validate the integration against the saved calculator-tab workbook outputs

## Current scope

The current calculation path is accurate to the supplied workbook, but it is still a first implementation of the product:

- It depends on Microsoft Excel being available locally.
- It uses the workbook directly instead of a full pure-Python translation.
- It supports the `Calculator` tab cleanly now, which is the actual calculator in your workbook.
- The `Student Info` sheet appears to contain saved values that do not match a fresh recalculation from its visible inputs, so that tab likely depends on workbook macros or a separate refresh flow.

This is still a strong foundation because it gives us a grounded end-to-end app with real workbook execution while we continue porting the logic into Python.

## Project structure

```text
.
|-- app.py
|-- aidwise/
|   |-- calculator.py
|   |-- llm.py
|   |-- models.py
|   |-- orchestrator.py
|   |-- retrieval.py
|   |-- sources.py
|   `-- routing.py
|-- data/
|   |-- models/
|   `-- policy/
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

Set environment variables:

```powershell
$env:OPENAI_API_KEY="your_api_key_here"
$env:OPENAI_MODEL="gpt-5-mini"
```

If `OPENAI_API_KEY` is not set, AidWise still runs and falls back to a local explanation template.

### 4. Add source files

Put policy documents in:

- `data/policy/`

Put the institutional workbook in:

- `data/models/`

AidWise also checks `data/policy/` for the workbook as a fallback, since the current project file was placed there.

## Run the app

```powershell
streamlit run app.py
```

## Run tests

```powershell
python -m unittest discover -s tests
```

## How the current version works

### Retrieval

The retriever scans local files in `data/policy/`, extracts text, breaks it into chunks, and returns the top chunks with simple keyword overlap scoring. This keeps the responses grounded in the official guide while we keep the retrieval layer lightweight.

### Calculation

AidWise now uses the provided workbook as the deterministic calculation engine:

1. It locates the workbook.
2. It opens Excel in the background.
3. It writes the form inputs into the workbook `Calculator` tab.
4. It forces a recalculation.
5. It reads back the workbook outputs.

This gives us workbook-aligned results without having to guess formula behavior.

### Explanation

AidWise combines:

- query routing
- retrieved evidence
- calculator outputs

and then uses the OpenAI API, when available, to generate grounded plain-language explanations. If the API is unavailable, it falls back to a deterministic explanation template.

## Verification status

- The default calculator-tab demo currently returns:
  - `Formula A`
  - `SAI = 5041`
  - `Max Pell = No`
  - `Min Pell = Yes`
  - `Assets Required = Yes`
- These values are covered by `tests/test_calculator.py`.

## Known issue

The workbook `Student Info` sheet appears to rely on additional macro-driven behavior or a refresh step. When its visible row-2 inputs are copied directly into the live `Calculator` tab and recalculated, the outputs do not match the stored `Student Info` values. That means the `Calculator` tab is currently the trustworthy path for automated validation unless we wire up the macro flow explicitly.

## Next steps

1. Trace or automate the workbook macro flow behind `Student Info`.
2. Port the workbook logic into pure Python so AidWise does not depend on local Excel.
3. Add page-aware citations for the PDF.
4. Expand validation with more workbook scenarios.

## Disclaimer

AidWise is an educational estimation and explanation system. It does not replace FAFSA, institutional aid systems, or official Department of Education determinations.
