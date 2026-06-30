from typing import Dict, Any, List
from src.engine.schemas import CanonicalCandidateProfile
from src.engine.normalizer import Normalizer


class Projector:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.fields_config = config.get("fields", [])
        self.include_confidence = config.get("include_confidence", True)
        self.on_missing = config.get("on_missing", "null")  # "null", "omit", or "error"

    def _resolve_path(self, data: Dict[str, Any], path: str) -> Any:
        """A highly robust path resolver handling recursive dot notations, arrays, and lists."""
        if not path or not data:
            return None

        # Deep recursive handler for dot notation (e.g., location.city or location.country)
        if "." in path and "[]" not in path:
            parts = path.split(".")
            current_data = data
            for part in parts:
                if isinstance(current_data, dict):
                    if "[" in part and "]" in part:
                        key, idx = part.split("[")
                        idx = int(idx.replace("]", ""))
                        val_list = current_data.get(key, [])
                        current_data = val_list[idx] if len(val_list) > idx else None
                    else:
                        current_data = current_data.get(part)
                else:
                    return None
            return current_data

        # Handle explicit indexed array positions (e.g., emails[0])
        if "[" in path and "]" in path and "[]" not in path:
            key, idx = path.split("[")
            idx = int(idx.replace("]", ""))
            val_list = data.get(key, [])
            return val_list[idx] if len(val_list) > idx else None

        # Handle multi-item sub-key array extractions (e.g., skills[].name)
        if "[]" in path:
            key, subkey = path.split("[].")
            val_list = data.get(key, [])
            return [self._resolve_path(item, subkey) if isinstance(item, dict) else None for item in val_list]

        return data.get(path)

    def apply(self, profile: CanonicalCandidateProfile) -> Dict[str, Any]:
        profile_dict = profile.model_dump()
        projected: Dict[str, Any] = {}

        for field_def in self.fields_config:
            target_key = field_def["path"]
            source_path = field_def.get("from", target_key)

            # Extract the raw structural value
            value = self._resolve_path(profile_dict, source_path)

            # Apply runtime field transform filters if explicitly configured
            if field_def.get("normalize") == "E164":
                value = Normalizer.normalize_phone(value)
            elif field_def.get("normalize") == "canonical":
                if isinstance(value, list):
                    value = [Normalizer.normalize_skill(v) for v in value]
                else:
                    value = Normalizer.normalize_skill(value)

            # Strict Missing Values Verification Matrix Policy
            if value is None or (isinstance(value, list) and not value):
                if self.on_missing == "error" and field_def.get("required"):
                    raise ValueError(f"Required field '{target_key}' is missing.")
                elif self.on_missing == "omit":
                    continue
                else:
                    value = None

            projected[target_key] = value

        # Handle Metadata and Tracking Schema Toggles
        if self.include_confidence:
            projected["overall_confidence"] = profile_dict.get("overall_confidence", 0.85)
            projected["provenance"] = profile_dict.get("provenance", [])

        return projected