from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address


def _get_rate_limit_key(request: Request) -> str:
    """Exempt OPTIONS preflight requests from rate limiting."""
    if request.method == "OPTIONS":
        return "options-exempt"
    return get_remote_address(request)


limiter = Limiter(key_func=_get_rate_limit_key, default_limits=["200/minute"])
