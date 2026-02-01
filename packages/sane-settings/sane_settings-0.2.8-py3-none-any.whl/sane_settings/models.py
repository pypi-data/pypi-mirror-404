from enum import StrEnum


class SecretStr:
    def __init__(self, value: str):
        self._value = value

    def get_secret_value(self) -> str:
        """Retrieve the actual secret value."""
        return self._value

    def __repr__(self) -> str:
        return "SecretStr('**********')"

    def __str__(self) -> str:
        return "**********"

    def __eq__(self, other) -> bool:
        if isinstance(other, SecretStr):
            return self._value == other._value
        return self._value == other


class Environments(StrEnum):
    DEV = "DEV"
    STAGING = "STAGING"
    PROD = "PROD"
