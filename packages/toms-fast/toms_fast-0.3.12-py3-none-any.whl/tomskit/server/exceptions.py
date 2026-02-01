"""
Exception handling module.

Provides unified exception base classes for layered exception handling:
- ServiceException: Business layer exception base class (framework-agnostic)
- APIException: Framework layer exception base class (inherits from HTTPException)
- raise_api_error: Quick function to raise APIException
- format_validation_errors: Utility function to format Pydantic ValidationError
"""

from typing import Optional, Any
from fastapi import HTTPException
from pydantic import ValidationError


# ============================================================================
# Exception Base Classes
# ============================================================================

class ServiceException(Exception):
    """
    Business exception base class.
    
    Used in Service layer (business logic layer) to raise business exceptions.
    
    Features:
    - Framework-agnostic: No dependency on FastAPI/HTTP, can be used in any business layer
    - Business semantics: Exception names reflect business meaning
    - Business context: Contains detailed business-related information
    - Serializable: Exception information can be converted to transferable format
    
    Attributes:
        code (str): Business error code, e.g., "USER_NOT_FOUND"
        message (str): User-friendly error message
        detail (dict): Detailed error information (business context)
        original_exception (Exception, optional): Original exception (if any)
    
    Example:
        >>> raise ServiceException(
        ...     code="USER_NOT_FOUND",
        ...     message="User not found",
        ...     detail={"user_id": "123"}
        ... )
    """
    
    def __init__(
        self,
        code: str,
        message: str,
        detail: Optional[dict] = None,
        original_exception: Optional[Exception] = None,
    ):
        """
        Initialize business exception.
        
        Args:
            code: Business error code, e.g., "USER_NOT_FOUND"
            message: User-friendly error message
            detail: Detailed error information (business context), defaults to empty dict
            original_exception: Original exception (if any), used for log tracking
        """
        self.code = code
        self.message = message
        self.detail = detail or {}
        self.original_exception = original_exception
        super().__init__(self.message)
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(code={self.code!r}, message={self.message!r})"


class APIException(HTTPException):
    """
    Framework unified exception base class.
    
    Used in framework layer for unified exception handling, inherits from FastAPI's HTTPException.
    
    Features:
    - Inherits from HTTPException (FastAPI native)
    - Contains unified response format
    - Can be handled by global exception handlers
    
    Attributes:
        code (str): Error code, e.g., "user_not_found"
        message (str): User-friendly error message
        status_code (int): HTTP status code
        detail (dict): Detailed error information
        original_exception (Exception, optional): Original Service exception (optional, for logging)
    
    Response format:
        {
            "code": "user_not_found",
            "message": "User not found",
            "status": 404
        }
        
        If detail is provided, it will be merged to the top level:
        {
            "code": "user_not_found",
            "message": "User not found",
            "status": 404,
            "user_id": "123",  # content from detail
            ...
        }
    
    Example:
        >>> raise APIException(
        ...     code="user_not_found",
        ...     message="User not found",
        ...     status_code=404,
        ...     detail={"user_id": "123"}
        ... )
    """
    
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400,
        detail: Optional[dict] = None,
        original_exception: Optional[Exception] = None,
    ):
        """
        Initialize framework exception.
        
        Args:
            code: Error code, e.g., "user_not_found"
            message: User-friendly error message
            status_code: HTTP status code, defaults to 400
            detail: Detailed error information, defaults to None (if provided, merged to response top level)
            original_exception: Original Service exception (optional, for log tracking)
        """
        self.code = code
        self.message = message
        self.original_exception = original_exception
        
        # HTTPException's detail parameter is used for response content
        # Format to unified structure: code, message, status at top level
        # If detail is provided, merge to top level (instead of nesting in detail field)
        if detail:
            response_detail = {
                "code": code,
                "message": message,
                "status": status_code,
                **detail,  # Merge detail directly using dict unpacking (more efficient)
            }
        else:
            response_detail = {
                "code": code,
                "message": message,
                "status": status_code,
            }
        
        super().__init__(status_code=status_code, detail=response_detail)
    
    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}"
            f"(code={self.code!r}, message={self.message!r}, status_code={self.status_code})"
        )


# ============================================================================
# Quick Exception Raising
# ============================================================================

# Default error codes and messages for common HTTP status codes
_DEFAULT_ERROR_MESSAGES = {
    400: ("bad_request", "Bad Request"),
    401: ("unauthorized", "Unauthorized"),
    403: ("forbidden", "Forbidden"),
    404: ("not_found", "Not Found"),
    409: ("conflict", "Conflict"),
    422: ("validation_error", "Validation Error"),
    500: ("internal_server_error", "Internal Server Error"),
    502: ("bad_gateway", "Bad Gateway"),
    503: ("service_unavailable", "Service Unavailable"),
    504: ("gateway_timeout", "Gateway Timeout"),
}


def raise_api_error(
    status_code: int,
    code: Optional[str] = None,
    message: Optional[str] = None,
    detail: Optional[dict] = None,
) -> None:
    """
    Quickly raise APIException.
    
    Uses unified response format with code, message, and status fields.
    
    Args:
        status_code: HTTP status code
        code: Error code (optional), auto-generated from status_code if not provided
        message: Error message (optional), auto-generated from status_code if not provided
        detail: Detailed error information dict (optional), merged to response top level
    
    Example:
        >>> # Basic usage (using default code and message)
        >>> raise_api_error(404)
        
        >>> # Specify code and message
        >>> raise_api_error(404, code="page_not_found", message="Page not found")
        
        >>> # Add detail information (merged to response top level)
        >>> raise_api_error(
        ...     status_code=404,
        ...     code="user_not_found",
        ...     message="User not found",
        ...     detail={"user_id": "123", "field": "id"}
        ... )
    
    Response format:
        {
            "code": "not_found",
            "message": "Not Found",
            "status": 404
        }
        
        If detail is provided:
        {
            "code": "user_not_found",
            "message": "User not found",
            "status": 404,
            "user_id": "123",
            "field": "id"
        }
    """
    # Get default code and message based on status_code
    default_code, default_message = _DEFAULT_ERROR_MESSAGES.get(
        status_code, (f"http_{status_code}", f"HTTP {status_code} Error")
    )
    
    # Determine final code and message
    final_code = code if code is not None else default_code
    final_message = message if message is not None else default_message
    
    # Raise APIException
    raise APIException(
        code=final_code,
        message=final_message,
        status_code=status_code,
        detail=detail,
    )


# ============================================================================
# ValidationError Formatting Utilities
# ============================================================================

# Sensitive field list (input values for these fields should not be returned in response)
# Pre-compute lowercase versions for efficient matching
_SENSITIVE_FIELDS = {"password", "token", "secret", "api_key", "access_token", "refresh_token"}
_SENSITIVE_FIELDS_LOWER = {field.lower() for field in _SENSITIVE_FIELDS}


def _get_field_path(loc: tuple[Any, ...]) -> str:
    """
    Convert field location tuple to path string.
    
    Args:
        loc: Field location tuple, e.g., ("user", "profile", "name") or ("items", 0, "name")
    
    Returns:
        Field path string, e.g., "user.profile.name" or "items.0.name"
    
    Example:
        >>> _get_field_path(("email",))
        "email"
        >>> _get_field_path(("user", "profile", "name"))
        "user.profile.name"
        >>> _get_field_path(("items", 0, "name"))
        "items.0.name"
    """
    return ".".join(str(x) for x in loc)


def _should_include_input(field_path: str) -> bool:
    """
    Determine whether input value should be included in response.
    
    Sensitive field input values should never be returned to avoid leaking sensitive information.
    However, validation errors for sensitive fields (field, message, type) are still included
    to notify users of validation issues.
    
    Args:
        field_path: Field path, e.g., "user.password" or "email"
    
    Returns:
        True if input value should be included (non-sensitive fields), False otherwise (sensitive fields)
    
    Note:
        - This function only determines whether to include the input VALUE
        - Field, message, and type are always included regardless of sensitivity
        - For sensitive fields: field/message/type are included, but input value is never included
    """
    field_lower = field_path.lower()
    # Check if any sensitive field keyword appears in the field path
    return not any(sensitive in field_lower for sensitive in _SENSITIVE_FIELDS_LOWER)


def _format_single_error(error: Any) -> dict[str, Any]:
    """
    Format a single field error.
    
    Args:
        error: Pydantic error dict containing loc, msg, type, input fields
    
    Returns:
        Formatted error dict containing field, message, type, input (if applicable)
    
    Note:
        - All fields (including sensitive fields) will include field, message, type
          to ensure users are notified of validation errors
        - For sensitive fields: input value is never included (even if present)
        - For non-sensitive fields: input value is included only if present (not None)
    """
    # Pydantic's ErrorDetails can be accessed as dict or object
    # Try dict access first (faster), fallback to getattr
    if isinstance(error, dict):
        loc = error.get("loc", ())
        msg = error.get("msg", "")
        error_type = error.get("type", "")
        input_value = error.get("input")
    else:
        loc = getattr(error, "loc", ())
        msg = getattr(error, "msg", "")
        error_type = getattr(error, "type", "")
        input_value = getattr(error, "input", None)
    
    field_path = _get_field_path(loc)
    error_dict: dict[str, Any] = {
        "field": field_path,
        "message": msg,
        "type": error_type,
    }
    
    # Only include input value for non-sensitive fields
    # For sensitive fields, we never include input value to avoid leaking sensitive information
    # However, field/message/type are always included so users are notified of validation errors
    if _should_include_input(field_path) and input_value is not None:
        error_dict["input"] = input_value
    
    return error_dict


def format_validation_errors(validation_error: ValidationError) -> dict[str, Any]:
    """
    Format Pydantic ValidationError to unified error format.
    
    Convert Pydantic's ValidationError to detailed field error list,
    used in exception handlers to generate unified error responses.
    
    Args:
        validation_error: Pydantic ValidationError instance
    
    Returns:
        Dict containing errors list:
        {
            "errors": [
                {
                    "field": "email",
                    "message": "value is not a valid email address",
                    "type": "value_error.email",
                    "input": "invalid-email"
                },
                {
                    "field": "age",
                    "message": "field required",
                    "type": "missing",
                    "input": null
                },
                ...
            ]
        }
    
    Example:
        >>> from pydantic import BaseModel, ValidationError
        >>> 
        >>> class User(BaseModel):
        ...     email: str
        ...     age: int
        >>> 
        >>> try:
        ...     User(email="invalid", age="not-int")
        ... except ValidationError as e:
        ...     errors = format_validation_errors(e)
        ...     print(errors)
        {
            "errors": [
                {
                    "field": "email",
                    "message": "value is not a valid email address",
                    "type": "value_error.email",
                    "input": "invalid"
                },
                {
                    "field": "age",
                    "message": "value is not a valid integer",
                    "type": "type_error.integer",
                    "input": "not-int"
                }
            ]
        }
    
    Note:
        - Sensitive fields (e.g., password, token) input values are not included in response
        - Supports nested field paths, e.g., "user.profile.name"
        - Supports array indices, e.g., "items.0.name"
    """
    return {"errors": [_format_single_error(error) for error in validation_error.errors()]}
