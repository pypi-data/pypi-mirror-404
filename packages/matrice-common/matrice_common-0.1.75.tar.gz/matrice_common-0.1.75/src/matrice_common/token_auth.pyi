"""Auto-generated stub for module: token_auth."""
from typing import Any

from .utils import process_error_log
from .utils import process_error_log
from .utils import process_error_log
from .utils import process_error_log
from .utils import process_error_log
from .utils import process_error_log
from .utils import process_error_log
from .utils import process_error_log

# Classes
class AuthToken:
    # Implements a custom authentication scheme.

    def __init__(self: Any, access_key: Any, secret_key: Any, refresh_token: Any) -> None: ...

    def is_expired(self: Any, buffer_seconds: int = 300) -> bool:
        """
        Check if token is expired or will expire within buffer_seconds.
        
                Args:
                    buffer_seconds: Number of seconds before actual expiry to consider token expired.
                                  Default is 300 (5 minutes) to allow proactive refresh.
        
                Returns:
                    True if token is None, has no expiry, or will expire within buffer_seconds.
        """
        ...

    def set_bearer_token(self: Any) -> Any:
        """
        Obtain an authentication bearer token using the provided refresh token.
        """
        ...

class RefreshToken:
    # Implements a custom authentication scheme.

    def __init__(self: Any, access_key: Any, secret_key: Any) -> None: ...

    def is_expired(self: Any, buffer_seconds: int = 300) -> bool:
        """
        Check if token is expired or will expire within buffer_seconds.
        
                Args:
                    buffer_seconds: Number of seconds before actual expiry to consider token expired.
                                  Default is 300 (5 minutes) to allow proactive refresh.
        
                Returns:
                    True if token is None, has no expiry, or will expire within buffer_seconds.
        """
        ...

    def set_bearer_token(self: Any) -> Any:
        """
        Obtain a bearer token using the provided access key and secret key.
        """
        ...

