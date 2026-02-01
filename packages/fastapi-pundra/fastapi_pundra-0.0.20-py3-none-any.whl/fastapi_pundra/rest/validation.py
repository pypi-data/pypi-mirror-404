from fastapi import Request, BackgroundTasks
from pydantic import BaseModel, ValidationError
from functools import wraps
from fastapi_pundra.rest.helpers import the_query
from fastapi_pundra.rest.exceptions import ValidationException, BadRequestException

def dto(schema: BaseModel):
    """ Decorator to validate the request data."""
    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, background_tasks: BackgroundTasks = None, *args, **kwargs):
            """ Wrapper to validate the request data."""
            try:
                request_data = await the_query(request)
                validated_data = schema.model_validate(request_data)
                request.state.validated_data = validated_data
                if background_tasks is not None:
                    return await func(request, background_tasks, *args, **kwargs)
                return await func(request,*args, **kwargs)
            except ValidationError as e:
                errors = {}
                for error in e.errors():
                    field = error["loc"][0]
                    message = field + " " + error["msg"]
                    if field not in errors:
                        errors[field] = []
                    errors[field].append(message)
                raise ValidationException(errors=errors)
            except ValueError:
                raise BadRequestException(message="Invalid JSON")

        return wrapper
    return decorator

__all__ = ["dto"]
