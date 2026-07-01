import streamlit as st 
import json 
import os
import tempfile
from src.main import run_pipeline

st.set_page_config(page_title="Candidate Transformer Engine", layout="wide")
st.title("Multi-Source Candidate Data Transformer Engine")

# Fully mapped, compliance-ready testing schema config
default_config = {
  "fields": [
    {"path": "candidate_name", "from": "full_name", "type": "string", "required": True},
    {"path": "primary_email", "from": "emails[0]", "type": "string"},
    {"path": "formatted_phone", "from": "phones[0]", "type": "string", "normalize": "E164"},
    {"path": "city_location", "from": "location.city", "type": "string"},
    {"path": "country_code", "from": "location.country", "type": "string"},
    {"path": "extracted_skills", "from": "skills[].name", "type": "array"}
  ],
  "include_confidence": True,
  "on_missing": "null"
}

col1, col2 = st.columns([1, 2])

with col1:
    st.header("1. Ingestion Inputs")
    uploaded_files = st.file_uploader(
        "Drop Processing Source Targets (CSV, PDF, JSON)",
        type=["csv", "pdf", "json"],
        accept_multiple_files=True
    )

    st.header("2. Runtime Config Strategy")
    config_text = st.text_area(
        "Edit JSON Output Spec Configuration",
        value=json.dumps(default_config, indent=2),
        height=350
    )

    run_button = st.button("Run Transformation Pipeline", type="primary")

with col2:
    st.header("3. Unified Normalized Projection Output")

    if run_button and uploaded_files:
        try:
            config = json.loads(config_text)

            # Execute context inside a clean isolated temp path structure
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_paths = []
                for uploaded_file in uploaded_files:
                    temp_path = os.path.join(temp_dir, uploaded_file.name)
                    with open(temp_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    temp_paths.append(temp_path)

                with st.spinner("Executing normalization & merge rules..."):
                    results = run_pipeline(temp_paths, config)

                st.success(f"Successfully processed {len(results)} distinct canonical profiles.")
                st.json(results)

        except json.JSONDecodeError:
            st.error("Syntax Error: Configuration input contains un-parsable structural syntax text.")
        except Exception as pipeline_fault:
            st.error(f"Pipeline processing aborted: {str(pipeline_fault)}")
    elif run_button:
        st.warning("Action Deferred: Please attach at least one file to execute processing loops.")