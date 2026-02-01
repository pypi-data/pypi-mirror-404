from typing import Any, Dict, Optional

class BaseAPIException(Exception):
    """Base exception for all API exceptions"""
    def __init__(
        self,
        message: str = "An error occurred",
        status_code: int = 500,
        errors: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.errors = errors or {}
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        output = {
            'success': False,
            'message': self.message
        }
        if self.errors:
            output['errors'] = self.errors
        return output

class ValidationException(BaseAPIException):
    """Validation error exception"""
    def __init__(self, errors: Dict[str, Any]):
        super().__init__(
            message="Validation error",
            status_code=422,
            errors=errors
        )

class NotFoundException(BaseAPIException):
    """Resource not found exception"""
    def __init__(self, message: str = "Resource not found"):
        super().__init__(
            message=message,
            status_code=404
        )

class ItemNotFoundException(BaseAPIException):
    """Item not found exception"""
    def __init__(self, message: str = "Item not found"):
        super().__init__(
            message=message,
            status_code=404
        )

class UnauthorizedException(BaseAPIException):
    """Unauthorized access exception"""
    def __init__(self, message: str = "Unauthorized access"):
        super().__init__(
            message=message,
            status_code=401
        )

class ForbiddenException(BaseAPIException):
    """Forbidden access exception"""
    def __init__(self, message: str = "Forbidden access"):
        super().__init__(
            message=message,
            status_code=403
        )

class BadRequestException(BaseAPIException):
    """Bad request exception"""
    def __init__(self, message: str = "Bad request", errors: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=400,
            errors=errors
        )

class ConflictException(BaseAPIException):
    """Conflict exception"""
    def __init__(self, message: str = "Resource conflict"):
        super().__init__(
            message=message,
            status_code=409
        )

class MethodNotAllowedException(BaseAPIException):
    """Method not allowed exception"""
    def __init__(self, message: str = "Method not allowed"):
        super().__init__(
            message=message,
            status_code=405
        )