import string

API_V1_PREFIX = "/api/v1"
HEALTH_PREFIX = "/health"
AUTH_PREFIX = "/auth"
USERS_PREFIX = "/users"
LINKS_PREFIX = "/links"


LOGIN_PATH = f"{API_V1_PREFIX}{AUTH_PREFIX}/login"

RESERVED_ALIASES = {
    API_V1_PREFIX.strip("/").split("/")[0],
    HEALTH_PREFIX.strip("/"),
    "docs", "redoc", "openapi.json",
}

TELEGRAM_LINK_CODE_TTL_SECONDS = 300
TELEGRAM_LINK_CODE_ALPHABET = string.ascii_uppercase + string.digits
TELEGRAM_LINK_CODE_PREFIX = "telegram_link_code:"