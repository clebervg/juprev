from slowapi import Limiter
from slowapi.util import get_remote_address

# Identifica o cliente pelo IP real (funciona atrás de proxy com X-Forwarded-For).
limiter = Limiter(key_func=get_remote_address)
