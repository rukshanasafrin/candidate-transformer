import os
from typing import List, Dict, Any
from src.adapters.structured_csv import CsvAdapter
from src.adapters.structured_json import StructuredJsonAdapter
from src.adapters.unstructured_pdf import PdfResumeAdapter
from src.engine.merger import Merger
from src.projection.projector import Projector


def run_pipeline(file_paths: List[str], runtime_config: Dict[str, Any]) -> List[Dict[str, Any]]:
    # 1. Initialize Adapters
    csv_adapter = CsvAdapter(source_name="recruiter_csv")
    pdf_adapter = PdfResumeAdapter(source_name="resume_pdf")
    json_adapter = StructuredJsonAdapter(source_name="ats_json")

    raw_records = []

    # 2. Extract Data (Safeguarded against Edge Case 3: Missing/Corrupted files)
    for path in file_paths:
        if not os.path.exists(path):
            print(f"Edge Case Alert: Missing source file path omitted: {path}")
            continue

        try:
            path_lower = path.lower()
            if path_lower.endswith(".csv"):
                raw_records.extend(csv_adapter.extract(path))
            elif path_lower.endswith(".pdf"):
                raw_records.extend(pdf_adapter.extract(path))
            elif path_lower.endswith(".json"):
                raw_records.extend(json_adapter.extract(path))
        except Exception as file_error:
            print(f"Edge Case Alert: Corrupt file parsing failure skipped: {path}. Error: {file_error}")
            continue

    # 3. Merge and Resolve Entities
    merger = Merger()
    merger.process_records(raw_records)
    canonical_profiles = merger.get_canonical_profiles()

    # 4. Apply Projection Config
    projector = Projector(runtime_config)
    final_output = []

    for profile in canonical_profiles:
        try:
            projected_data = projector.apply(profile)
            final_output.append(projected_data)
        except Exception as projection_error:
            print(f"Profile skipped during validation validation: {projection_error}")
            continue

    return final_output