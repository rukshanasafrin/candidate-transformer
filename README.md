# Multi-Source Candidate Data Transformer Engine

A production-grade, extensible data engineering pipeline built with Python and Streamlit that ingests, cleanses, merges, and projects candidate profiles from disparate structured (`CSV`, `JSON`) and unstructured (`PDF`) sources into a single, schema-validated canonical Source of Truth.


##  Architecture & Core Design Decisions

This engine relies on an asymmetrical **Extract-Transform-Load-Project (ETLP)** modular pattern designed for data isolation and zero-loss entity stitching. 

```

+------------------------------------+
|  Ingestion Layer (Adapters)        | ---> CSV / JSON / PDF Raw Extraction
+------------------------------------+
|
v
+------------------------------------+
| Normalization Engine (Normalizers) | ---> E.164, ISO 8601, Parameters Stripping
+------------------------------------+
|
v
+------------------------------------+
| Identify confidence scores (Merge) | ---> Priority Resolution & Scalar Field Overwrites
+------------------------------------+
|
v
+------------------------------------+
|  Canonical Profile Schema (Truth)  | ---> Strict Pydantic Data Matrix
+------------------------------------+
|
v
+------------------------------------+
|  Runtime Output Layer (Projector)  | ---> Dot-Notation Traverser & Null Fallbacks
+------------------------------------+

```

## 📈 Confidence Score Construction Framework

Confidence metrics are not arbitrarily assigned; they are computed dynamically by the `Merger` engine using two core factors: **Source Tier Reliability** and **Multi-Source Cross-Verification**.

### 1. Base Source Tiers
Different ingestion paths carry baseline structural integrity values based on human intervention vs. automated extraction:
* `ats_json` (**0.90**): High Confidence. Structured system of record directly entered or verified within an ATS database.
* `recruiter_csv` (**0.80**): Medium-High Confidence. Formatted tabular structure manually compiled by an expert recruiter.
* `resume_pdf` (**0.60**): Medium-Low Confidence. Unstructured raw document extraction vulnerable to regex bounding/layout layout parsing limitations.
* `recruiter_notes` (**0.50**): Low Confidence. Subjective free-text input or parsed conversational updates.

### 2. Scalar Field Confidence Resolution
For single-value parameters (e.g., `full_name`, `current_company`), the engine implements a **Winner-Take-All Conflict Resolution Rule**:
* The field value from the highest-priority source becomes the visible profile metric.
* If a subsequent record matches the candidate but originates from a lower-tier source, the profile value is preserved, preventing degradation.

### 3. Skill & List Confidence Cross-Verification
For multi-value array lists (such as `skills`), confidence scales dynamically with cross-source validation:
* **Initial Rule:** A skill extracted from a single source inherits that source's base confidence factor (e.g., a PDF regex skill match initializes at `0.70`).
* **Cross-Verification Bonus:** If a skill is discovered across *multiple* incoming files (e.g., both the PDF resume match and the Recruiter CSV mention `"React"`), the system confirms the attribute data. 
* The source identifier is appended to the skill's tracking metadata array, and the confidence score is dynamically bumped up to a maximum threshold of `0.95`, establishing a data verification trail.


## 🛡️ Edge Case Engineering Matrix

The engine is defensively hardened against the following 5 runtime edge scenarios:
1. **Conflicting Emails Across Sources:** The identity stitching module uses its Source Confidence configuration matrix to establish the dominant tracking path while safely logging alternate addresses safely inside the unique flattened tracking lists without dropping historical source markers.
2. **Invalid Phone/Date Metadata:** Unparseable variables run through isolated safety `try/except` closures, downgrading gracefully to `null` properties rather than breaking the loop.
3. **Missing or Corrupted Ingestion Source Files:** File iteration processing loops run in fully decoupled tracking environments. If a file is completely missing or throws structural read faults, it prints warnings to stdout and skips that file, continuing with remaining valid data sheets.
4. **Duplicate Skill Spellings/Capitalizations:** Tokens are fully stripped of alphanumeric characters, forced lowercase, and evaluated using a canonical reference table before schema injection.
5. **Multiple Candidates with Similar Names:** The entity resolution module strictly forbids loose matching. Merges require validated overlapping identifiers (Email $\rightarrow$ Phone $\rightarrow$ Exact Match Name + Current Corporate Entity). If none match, a new canonical entity profile is spun up.

## 📦 Directory File Layout Map

```text
candidate-transformer/
├── README.md                  # Detailed Project Manifest Documentation
├── requirements.txt           # Structural Target Pinned Libraries
├── src/
│   ├── __init__.py
│   ├── main.py                # End-to-End Pipeline Program Controller Loop
│   ├── app.py                 # Streamlit UI Dashboard Application Frontend
│   ├── adapters/
│   │   ├── __init__.py
│   │   ├── base_adapter.py     # Framework Contract Model Blueprint Class
│   │   ├── structured_csv.py   # Row-by-Row Tabular Data Parser
│   │   ├── structured_json.py  # Deep Nested Object Finder Ingestion Link
│   │   └── unstructured_pdf.py # Regular Expression Multiline Text Extraction Extractor
│   ├── engine/
│   │   ├── __init__.py
│   │   ├── normalizer.py      # Core 5-Attribute Cleanse Processing Utilities
│   │   ├── merger.py          # Entity Stitching Logic & Resolution Center
│   │   └── schemas.py         # Type Hinting Validations via Pydantic Data Schemas
│   └── projection/
│       ├── __init__.py
│       └── projector.py       # Runtime Output Selector & Recursive Path Resolver

```

## 🚀 Setup and Local Run Steps

Follow these exact steps to compile and run the engine locally on your machine.

### 1. Prerequisites
Ensure you have Python 3.10+ installed on your system.

### 2. Clone and Environment Initialization
Clone the repository to your machine and move into the project directory:
```bash
git clone <your-public-github-repo-link>
cd candidate-transformer

```

Create an isolated virtual environment to prevent package version conflicts:

```bash
python -m venv venv

```

Activate the virtual environment depending on your operating system:

* **Mac / Linux:** `source venv/bin/activate`
* **Windows (CMD):** `venv\Scripts\activate.bat`
* **Windows (PowerShell):** `venv\Scripts\Activate.ps1`

### 3. Install Required Dependencies

Install the pinned libraries directly via `requirements.txt`:

```bash
pip install -r requirements.txt

```

### 4. Launching the UI Dashboard Engine

Execute the Streamlit application compiler:

```bash
streamlit run src/app.py

```

Once initialized, your local server will instantly open up a browser tab. If it doesn't open automatically, navigate manually to:

```text
http://localhost:8501

```


