from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import get_settings

_s = get_settings()

# Keyed by client IP. Behind a reverse proxy run uvicorn with --proxy-headers so the real
# client address is used, otherwise every user shares one bucket.
limiter = Limiter(key_func=get_remote_address, default_limits=[_s.rate_limit_default])
