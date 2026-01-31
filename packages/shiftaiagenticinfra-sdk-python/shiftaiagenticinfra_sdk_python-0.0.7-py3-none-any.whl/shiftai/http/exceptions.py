"""
Exception hierarchy for API errors.
"""


class ApiException(Exception):
    """Base exception for API errors."""
    
    def __init__(self, status_code: int, message: str, response_body: str = None):
        self.status_code = status_code
        self.response_body = response_body
        super().__init__(message)
    
    def __str__(self):
        if self.response_body:
            return f"API error {self.status_code}: {super().__str__()}\nResponse: {self.response_body}"
        return f"API error {self.status_code}: {super().__str__()}"


class UnauthorizedException(ApiException):
    """Exception for 401 Unauthorized errors."""
    
    def __init__(self, message: str = "Unauthorized", response_body: str = None):
        super().__init__(401, message, response_body)


class BadRequestException(ApiException):
    """Exception for 400 Bad Request errors."""
    
    def __init__(self, message: str = "Bad Request", response_body: str = None):
        super().__init__(400, message, response_body)


class NotFoundException(ApiException):
    """Exception for 404 Not Found errors."""
    
    def __init__(self, message: str = "Not Found", response_body: str = None):
        super().__init__(404, message, response_body)


class ServerException(ApiException):
    """Exception for 5xx Server errors."""
    
    def __init__(self, status_code: int, message: str = "Server Error", response_body: str = None):
        if status_code < 500 or status_code >= 600:
            raise ValueError(f"ServerException requires 5xx status code, got {status_code}")
        super().__init__(status_code, message, response_body)

