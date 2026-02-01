import os
from fastapi_pundra.common.helpers import base_path
from dotenv import load_dotenv
from sqlalchemy import text, Result
from collections import OrderedDict
from fastapi import Request
from urllib.parse import urlparse
from uuid import UUID
from datetime import datetime
from sqlalchemy.engine.result import Result

load_dotenv()


def raw_sql_fetch_all(query: Result) -> list[dict]:
    """Fetch all data from the query."""
    data = query.fetchall()
    result_list = []
    for row in data:
        row_dict = dict(row._asdict())
        # Convert UUID and datetime objects to strings
        for key, value in row_dict.items():
            if isinstance(value, UUID):
                row_dict[key] = str(value)
            elif isinstance(value, datetime):
                row_dict[key] = value.isoformat()
        result_list.append(row_dict)

    return result_list

def load_sql_file(file_path: str, sql_vars: dict = None) -> str:
    project_base_path = os.getenv('PROJECT_BASE_PATH', 'app')
    sql_files_path = 'sql_files'
    
    # Split the file path into components and join with SQL extension
    components = file_path.split(".")
    relative_path = os.path.join(*components) + ".sql"
    
    # Construct absolute path using base_path and project settings
    absolute_path = os.path.join(base_path(), project_base_path, sql_files_path, relative_path)
    
    with open(absolute_path, "r") as file:
        sql_content = file.read()
        
    # Replace SQL variables if provided
    if sql_vars:
        for key, value in sql_vars.items():
            placeholder = f"--sql_var:{key}"
            # Handle different types of values
            if isinstance(value, str):
                formatted_value = f"'{value}'"
            elif value is None:
                formatted_value = 'NULL'
            else:
                formatted_value = str(value)
            sql_content = sql_content.replace(placeholder, formatted_value)
    
    return text(sql_content)
    
def raw_sql_rest_paginate(request: Request, query_data: list, serializer = None, the_page: int = 1, the_per_page: int = 10, wrap: str = "data", additional_data: dict = None) -> dict:
    """Paginate raw SQL query results."""
    results = query_data

    page = int(request.query_params.get("page", the_page))
    per_page = int(request.query_params.get("per_page", the_per_page))

    # Calculate indices and total pages
    total = len(results)
    total_pages = (total + per_page - 1) // per_page
    start_index = (page - 1) * per_page
    end_index = page * per_page

    # Slice the results to get the paginated subset
    paginated_results = results[start_index:end_index]

    if serializer:
        paginated_results = [serializer(**item).model_dump() for item in paginated_results]

    # Build proper URLs using urlparse
    full_path = str(request.url)
    parsed_url = urlparse(full_path)
    path_without_query = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
    base_url = str(request.base_url)

    # Generate all pagination URLs
    first_page_url = f"{path_without_query}?page=1&per_page={per_page}"
    last_page_url = f"{path_without_query}?page={total_pages}&per_page={per_page}"
    next_page_url = f"{path_without_query}?page={page + 1}&per_page={per_page}" if page < total_pages else None
    prev_page_url = f"{path_without_query}?page={page - 1}&per_page={per_page}" if page > 1 else None

    output = OrderedDict([
        (wrap, paginated_results),
        ("total", total),
        ("per_page", per_page),
        ("current_page", page),
        ("last_page", total_pages),
        ("first_page_url", first_page_url),
        ("last_page_url", last_page_url),
        ("next_page_url", next_page_url),
        ("prev_page_url", prev_page_url),
        ("path", base_url),
        ("from", start_index + 1 if paginated_results else None),
        ("to", start_index + len(paginated_results) if paginated_results else None),
    ])

    if additional_data:
        if callable(additional_data):
            # Convert list items to a dictionary before passing to additional_data
            output["additional_data"] = additional_data(paginated_results)
        else:
            output["additional_data"] = additional_data

    return output

def raw_sql_fetch_one(query: Result, serializer = None) -> dict:
    """Fetch one data from the query."""
    data = query.fetchone()
    if data is None:
        return None
    # Convert Row to dictionary first
    data_dict = dict(data._asdict())
    if serializer:
        return serializer(**data_dict).model_dump()
    return data_dict

def raw_sql_paginate_gql(query_data: list, serializer = None, the_page: int = 1, the_per_page: int = 10, wrap: str = "data", additional_data: dict = None) -> dict:
    """Paginate raw SQL query results."""
    results = query_data
    
    # Calculate pagination values
    total = len(results)
    last_page = (total + the_per_page - 1) // the_per_page
    
    # Adjust page if it exceeds last_page
    page = min(the_page, last_page) if last_page > 0 else 1
    
    # Calculate indices
    start_index = (page - 1) * the_per_page
    end_index = page * the_per_page
    
    # Slice the results
    paginated_results = results[start_index:end_index]
    
    # Apply serializer if provided
    if serializer:
        paginated_results = [serializer(**item).model_dump() for item in paginated_results]
    
    # Calculate next and previous pages
    next_page = page + 1 if page < last_page else None
    prev_page = page - 1 if page > 1 else None
    
    output = {
        wrap: paginated_results,
        "pagination": {
            "total": total,
            "current_page": page,
            "next_page": next_page,
            "prev_page": prev_page,
            "per_page": the_per_page,
            "last_page": last_page,
            "from_item": start_index + 1 if paginated_results else None,
            "to_item": start_index + len(paginated_results) if paginated_results else None
        }
    }
    
    if additional_data:
        if callable(additional_data):
            output["additional_data"] = additional_data(paginated_results)
        else:
            output["additional_data"] = additional_data
    
    return output