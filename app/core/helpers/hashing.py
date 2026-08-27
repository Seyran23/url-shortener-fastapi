import hashlib


def hash_visitor(ip_address: str, user_agent: str | None) -> str:
    return hashlib.sha256(f"{ip_address}:{user_agent}".encode()).hexdigest()
