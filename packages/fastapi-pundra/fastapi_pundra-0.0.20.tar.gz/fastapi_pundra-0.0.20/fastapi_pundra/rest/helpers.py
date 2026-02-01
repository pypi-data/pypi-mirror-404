from fastapi import Request
from sqlalchemy import desc
from pydantic import BaseModel

async def the_query(request: Request, name: str | None = None) -> dict[str, str] | str | None:
    """Get the query parameters from the request."""
    data = {}

    if request.query_params:
        data =  request.query_params
    elif request.headers.get("Content-Type") == "application/json":
        data = await request.json()
    else:
        data = await request.form()

    if name:
        return data.get(name)
    return data

def the_sorting(request: Request, query, default_sort=""):
    """Sort a SQLAlchemy query based on query parameters.
    
    Example:
        # For a request with URL: /api/items?sort=name,-created_at
        # This will sort by name (ascending) and created_at (descending)
    """
    sort_params = request.query_params.get("sort") or default_sort
    
    if sort_params:
        sort_fields = sort_params.split(",")
        ordering = []
        model_class = query.column_descriptions[0]['entity']
        
        # Get all valid column names from the model
        valid_columns = model_class.__table__.columns.keys()

        for field in sort_fields:
            field_name = field[1:] if field.startswith("-") else field
            
            # Check if the field exists in the model
            if field_name in valid_columns:
                if field.startswith("-"):
                    ordering.append(desc(getattr(model_class, field_name)))
                else:
                    ordering.append(getattr(model_class, field_name))
                
        if ordering:
            query = query.order_by(*ordering)
        
    return query

def get_serialize_data(schema: BaseModel, data: dict) -> dict:
    """Get the serialized data."""
    return schema.model_validate(data).model_dump()