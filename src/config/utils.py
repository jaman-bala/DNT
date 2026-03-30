import os
from typing import Any


def strtobool(value: str) -> bool:
    """Convert string representation of truth to boolean."""
    return value.lower() in ("yes", "true", "t", "1", "on")


def read_secret(secret_name: str, env_variable_name: str | None = None) -> str | None:
    """Read secret from Docker secrets or environment variable"""
    secret_name = secret_name.lower()
    secret_path = f"/run/secrets/{secret_name}"
    try:
        with open(secret_path) as f:
            return f.read().strip()
    except FileNotFoundError:
        # Handle the case where secrets are not available (e.g., in local development)
        if env_variable_name:
            return os.environ.get(env_variable_name)
        return os.environ.get(secret_name.upper())


class EnvHelper:
    def __call__(self, env_name: str, default: Any = None, is_bool: bool = False) -> str | bool | Any:
        """
        Get environment variable value with type conversion.

        Args:
            env_name: Name of environment variable
            default: Default value if environment variable is not set
            is_bool: Whether to convert value to boolean

        Returns:
            Environment variable value converted to appropriate type
        """
        value = os.environ.get(env_name.upper())
        if value is None:
            if default is None:
                return None
            if is_bool:
                return (
                    bool(default) if isinstance(default, bool) else strtobool(str(default))
                )
            return default

        if is_bool:
            return strtobool(value)
        return value

    def list(self, env_name: str, default: list | None = None) -> list:
        """Get environment variable as a list of strings."""
        value = os.environ.get(env_name.upper())
        if value is None:
            return default if default is not None else []
        return [x.strip() for x in value.split(",")]

env = EnvHelper()
