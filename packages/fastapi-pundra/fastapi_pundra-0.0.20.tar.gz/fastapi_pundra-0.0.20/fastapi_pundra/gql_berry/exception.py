from graphql import GraphQLError

class NotFoundError(GraphQLError):
    def __init__(self, message: str):
        super().__init__(
            message=message,
            extensions={
                "code": "NOT_FOUND",
                "category": "NotFound",
            }
        )


class DtoValidationError(GraphQLError):
    @staticmethod
    def format_validation_errors(validation_errors) -> dict:
        errors = {}
        for error in validation_errors:
            field = error['loc'][0]
            message = f"{field} {error['msg']}"
            if field not in errors:
                errors[field] = []
            errors[field].append(message)
        return errors

    def __init__(self, message: str, validation_errors=None):
        extensions = {
            "code": "VALIDATION_ERROR",
            "category": "Validation",
        }
        
        if validation_errors:
            formatted_errors = self.format_validation_errors(validation_errors)
            extensions["validation_errors"] = formatted_errors

        super().__init__(
            message=message,
            extensions=extensions
        )

class BadRequestError(GraphQLError):
    def __init__(self, message: str):
        super().__init__(
            message=message,
            extensions={
                "code": "BAD_REQUEST",
                "category": "BadRequest",
            }
        )

class ForbiddenError(GraphQLError):
    def __init__(self, message: str):
        super().__init__(
            message=message,
            extensions={
                "code": "FORBIDDEN",
                "category": "Forbidden",
            }
        )

class ConflictError(GraphQLError):
    def __init__(self, message: str):
        super().__init__(
            message=message,
            extensions={
                "code": "CONFLICT",
                "category": "Conflict",
            }
        )

class DuplicateError(GraphQLError):
    def __init__(self, message: str):
        super().__init__(
            message=message,
            extensions={
                "code": "DUPLICATE",
                "category": "Duplicate",
            }
        )

class InternalServerError(GraphQLError):
    def __init__(self, message: str = "An unexpected error occurred"):
        super().__init__(
            message=message,
            extensions={
                "code": "INTERNAL_SERVER_ERROR",
                "category": "ServerError",
            }
        )


class RateLimitError(GraphQLError):
    def __init__(self, message: str, remaining_time: int = None):
        extensions = {
            "code": "RATE_LIMIT_EXCEEDED",
            "category": "RateLimit",
        }
            
        super().__init__(
            message=message,
            extensions=extensions
        )