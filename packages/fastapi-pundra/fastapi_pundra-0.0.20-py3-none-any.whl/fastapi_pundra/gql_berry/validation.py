import functools
from typing import Type
import pydantic
from fastapi_pundra.gql_berry.exception import DtoValidationError

def dto_validation(dto_class: Type[pydantic.BaseModel]):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                # Find the input data argument (usually the last one)
                input_data = next((v for k, v in kwargs.items() if hasattr(v, '__dict__')), None)
                if input_data:
                    validated_data = dto_class(**input_data.__dict__)
                    # Replace the input data with validated data
                    kwargs = {k: validated_data if v == input_data else v for k, v in kwargs.items()}
                return func(*args, **kwargs)
            except pydantic.ValidationError as e:
                raise DtoValidationError(
                    message="Validation error",
                    validation_errors=e.errors()
                )
        return wrapper
    return decorator 