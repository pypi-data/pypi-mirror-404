"""Module for custom authentication"""

import json
import os
import sys
from datetime import datetime, timezone, timedelta
import requests
from dateutil.parser import parse
from requests.auth import AuthBase
import logging


class RefreshToken(AuthBase):
    """Implements a custom authentication scheme."""

    def __init__(self, access_key, secret_key):
        self.bearer_token = None
        self.expiry_time = None
        self.access_key = access_key
        self.secret_key = secret_key
        base_url = (
            os.environ.get('MATRICE_BASE_URL')
            or f"https://{os.environ.get('ENV', 'prod')}.backend.app.matrice.ai"
        )
        self.VALIDATE_ACCESS_KEY_URL = f"{base_url}/v1/accounting/validate_access_key"

    def is_expired(self, buffer_seconds: int = 300) -> bool:
        """Check if token is expired or will expire within buffer_seconds.

        Args:
            buffer_seconds: Number of seconds before actual expiry to consider token expired.
                          Default is 300 (5 minutes) to allow proactive refresh.

        Returns:
            True if token is None, has no expiry, or will expire within buffer_seconds.
        """
        if self.bearer_token is None or self.expiry_time is None:
            return True
        buffer = timedelta(seconds=buffer_seconds)
        now = datetime.now(timezone.utc)
        expiry = self.expiry_time if self.expiry_time.tzinfo else self.expiry_time.replace(tzinfo=timezone.utc)
        return now >= expiry - buffer

    def __call__(self, r):
        """Attach an API token to a custom auth header."""
        self.set_bearer_token()
        if self.bearer_token is None:
            raise ValueError(
                "Failed to obtain refresh token. Cannot authenticate request. "
                "Please check your access_key and secret_key credentials."
            )
        r.headers["Authorization"] = self.bearer_token
        return r

    def set_bearer_token(self):
        """Obtain a bearer token using the provided access key and secret key."""
        payload_dict = {
            "accessKey": self.access_key,
            "secretKey": self.secret_key,
        }
        payload = json.dumps(payload_dict)
        headers = {"Content-Type": "text/plain"}
        response = None
        try:
            response = requests.request(
                "GET",
                self.VALIDATE_ACCESS_KEY_URL,
                headers=headers,
                data=payload,
                timeout=120,
            )
        except Exception as e:
            from .utils import process_error_log
            process_error_log(
                error=e,
                service_name="matrice_common",
                default_return=None,
                raise_exception=False,
                log_error=True
            )
            return

        if not response or response.status_code != 200:
            error_msg = f"Error response from the auth server in RefreshToken (status: {getattr(response, 'status_code', 'unknown')}): {getattr(response, 'text', 'No response text')}"
            from .utils import process_error_log
            process_error_log(
                error=Exception(error_msg),
                service_name="matrice_common",
                default_return=None,
                raise_exception=False,
                log_error=True
            )
            return

        try:
            res_dict = response.json()
        except Exception as e:
            from .utils import process_error_log
            process_error_log(
                error=Exception(f"Invalid JSON in RefreshToken response: {str(e)}"),
                service_name="matrice_common",
                default_return=None,
                raise_exception=False,
                log_error=True
            )
            return

        if res_dict.get("success") and res_dict.get("data", {}).get("refreshToken"):
            logging.debug(f"res_dict: {res_dict}")
            self.bearer_token = "Bearer " + res_dict["data"]["refreshToken"]
            # Track expiry time - use server-provided value or default to 23 hours
            if res_dict.get("data", {}).get("expiresAt"):
                self.expiry_time = parse(res_dict["data"]["expiresAt"])
            else:
                # Conservative default: 23 hours (most refresh tokens last 24h+)
                self.expiry_time = datetime.now(timezone.utc) + timedelta(hours=23)
            logging.debug(f"RefreshToken expiry set to: {self.expiry_time}")
        else:
            error_msg = f"The provided credentials are incorrect in RefreshToken. Response: {res_dict}"
            logging.error(error_msg)
            from .utils import process_error_log
            process_error_log(
                error=Exception(error_msg),
                service_name="matrice_common",
                default_return=None,
                raise_exception=False,
                log_error=True
            )


class AuthToken(AuthBase):
    """Implements a custom authentication scheme."""

    def __init__(
        self,
        access_key,
        secret_key,
        refresh_token,
    ):
        self.bearer_token = None
        self.access_key = access_key
        self.secret_key = secret_key
        self.refresh_token = refresh_token
        self.expiry_time = datetime.now(timezone.utc)
        base_url = (
            os.environ.get('MATRICE_BASE_URL')
            or f"https://{os.environ.get('ENV', 'prod')}.backend.app.matrice.ai"
        )
        self.REFRESH_TOKEN_URL = f"{base_url}/v1/accounting/refresh"

    def is_expired(self, buffer_seconds: int = 300) -> bool:
        """Check if token is expired or will expire within buffer_seconds.

        Args:
            buffer_seconds: Number of seconds before actual expiry to consider token expired.
                          Default is 300 (5 minutes) to allow proactive refresh.

        Returns:
            True if token is None, has no expiry, or will expire within buffer_seconds.
        """
        if self.bearer_token is None or self.expiry_time is None:
            return True
        buffer = timedelta(seconds=buffer_seconds)
        now = datetime.now(timezone.utc)
        expiry = self.expiry_time if self.expiry_time.tzinfo else self.expiry_time.replace(tzinfo=timezone.utc)
        return now >= expiry - buffer

    def __call__(self, r):
        """Attach an API token to a custom auth header."""
        self.set_bearer_token()
        if self.bearer_token is None:
            raise ValueError(
                "Failed to obtain authentication token. Cannot authenticate request. "
                "This may be due to invalid credentials or server issues."
            )
        r.headers["Authorization"] = self.bearer_token
        return r

    def set_bearer_token(self):
        """Obtain an authentication bearer token using the provided refresh token."""
        # Ensure refresh token is valid - check expiry, not just None
        if self.refresh_token.bearer_token is None or self.refresh_token.is_expired():
            try:
                logging.debug("RefreshToken is None or expired, refreshing...")
                self.refresh_token.set_bearer_token()
            except Exception as e:
                error_msg = f"Failed to obtain refresh token before getting auth token: {e}"
                logging.error(error_msg)
                # Don't raise - return and let caller handle None bearer_token
                return

        # Use the refresh token bearer_token as an authorization header
        headers = {
            "Content-Type": "application/json",
            "Authorization": self.refresh_token.bearer_token
        }
        response = None
        try:
            response = requests.request(
                "POST",
                self.REFRESH_TOKEN_URL,
                headers=headers,
                timeout=120,
            )
        except Exception as e:
            from .utils import process_error_log
            process_error_log(
                error=e,
                service_name="matrice_common",
                default_return=None,
                raise_exception=False,
                log_error=True
            )
            return

        if not response or response.status_code != 200:
            error_msg = f"Error response from the auth server in AuthToken (status: {getattr(response, 'status_code', 'unknown')}): {getattr(response, 'text', 'No response text')}"
            from .utils import process_error_log
            process_error_log(
                error=Exception(error_msg),
                service_name="matrice_common",
                default_return=None,
                raise_exception=False,
                log_error=True
            )
            return

        try:
            res_dict = response.json()
        except Exception as e:
            from .utils import process_error_log
            process_error_log(
                error=Exception(f"Invalid JSON in AuthToken response: {str(e)}"),
                service_name="matrice_common",
                default_return=None,
                raise_exception=False,
                log_error=True
            )
            return

        if res_dict.get("success") and res_dict.get("data", {}).get("token"):
            self.bearer_token = "Bearer " + res_dict["data"]["token"]
            self.expiry_time = parse(res_dict["data"]["expiresAt"])
        else:
            error_msg = f"The provided credentials are incorrect in AuthToken. Response: {res_dict}"
            logging.error(error_msg)
            from .utils import process_error_log
            process_error_log(
                error=Exception(error_msg),
                service_name="matrice_common",
                default_return=None,
                raise_exception=False,
                log_error=True
            )
