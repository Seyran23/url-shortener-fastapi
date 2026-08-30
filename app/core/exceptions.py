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


class LinkNotFoundError(AppError):
    """Link not found."""
    status_code = 404
    error_code = "link_not_found"
    
class AliasAlreadyExistsError(AppError):
    """This alias has already been taken."""
    status_code = 409
    error_code = "alias_already_exists"

class LinkNotActiveError(AppError):
    """This link is not active."""
    status_code = 410
    error_code = "link_is_not_active"
    
class LinkExpiredError(AppError):
    """This link has expired. Extend its expiration date before activating it."""
    status_code = 409
    error_code = "link_expired"

class ClickLimitReachedError(AppError):
    """This link has reached its click limit. Increase the limit before activating it."""
    status_code = 409
    error_code = "click_limit_reached"

class LinkUnavailableError(AppError):
    """This link is not available."""
    status_code = 410
    error_code = "link_unavailable"

class RateLimitExceededError(AppError):
    """Too many requests. Please try again later."""
    status_code = 429
    error_code = "rate_limit_exceeded"

class InvalidTelegramLinkCodeError(AppError):
    """This code is invalid or has expired."""
    status_code = 400
    error_code = "invalid_telegram_link_code"

class TelegramChatAlreadyLinkedError(AppError):
    """This Telegram account is already linked to a different account."""
    status_code = 409
    error_code = "telegram_chat_already_linked"

