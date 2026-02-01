from typing import Any

def openapi_request_body_schema(
    schema_class: type,
    *,
    required: bool = True,
    description: str | None = None,
    content_type: str = "application/json",
    examples: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """
    Generate OpenAPI request body configuration for FastAPI routes.

    Args:
        schema_class: Pydantic model class to use for the request body schema
        required: Whether the request body is required (default: True)
        description: Optional description for the request body
        content_type: Content type for the request body (default: "application/json")
        examples: Optional dictionary of example requests (name -> example object)

    Returns:
        Dictionary containing OpenAPI requestBody configuration
    """
    content_config: dict[str, Any] = {
        "schema": schema_class.model_json_schema()
    }

    if examples:
        content_config["examples"] = examples

    config: dict[str, Any] = {
        "requestBody": {
            "content": {content_type: content_config},
            "required": required,
        }
    }

    if description:
        config["requestBody"]["description"] = description

    return config
