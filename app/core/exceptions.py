class AppError(Exception):
    status_code: int = 500
    error_code: str = "internal_error"
    
    def __init__(self, message: str | None = None):
        self.message = message or self.__class__.__doc__ or "An error occurred"
        super().__init__(self.message)
        
        
class UserAlreadyExistsError(AppError):
    """A user with this email already exists."""
    status_code = 409
    error_code = "user_already_exists"
    
class InvalidCredentialsError(AppError):
    """Incorrect email or password."""
    status_code = 401
    error_code = "invalid_credentials"
    
class UserNotFoundError(AppError):
    """User not found."""
    status_code = 404
    error_code = "user_not_found"
