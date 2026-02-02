"""Custom JSON response handlers for FastAPI."""
import json
from fastapi.responses import JSONResponse
from ipulse_shared_core_ftredge.utils.json_encoder import EnsureJSONEncoderCompatibility, convert_to_json_serializable


class CustomJSONResponse(JSONResponse):
    """Custom JSON response with enhanced serialization support."""

    def render(self, content) -> bytes:
        # First preprocess content with our utility function
        if isinstance(content, dict) and "data" in content and hasattr(content["data"], "model_dump"):
            # If content["data"] is a Pydantic model, use model_dump with exclude_unset=True
            # and exclude_computed=True to prevent serialization of computed fields
            content = dict(content)  # Create a copy to avoid modifying the original
            content["data"] = content["data"].model_dump(
                exclude_unset=True,
                exclude_computed=True
            )

        # Now convert all problematic types to JSON serializable values
        json_safe_content = convert_to_json_serializable(content)

        # Use the CustomJSONEncoder for additional safety
        return json.dumps(
            json_safe_content,
            ensure_ascii=False,
            allow_nan=False,
            indent=None,
            separators=(",", ":"),
            cls=EnsureJSONEncoderCompatibility
        ).encode("utf-8")
