from __future__ import annotations

from typing import Any

from django.db import models
from django.db.backends.base.base import BaseDatabaseWrapper
from django.db.models.expressions import Expression

from saas.utils.secure import decrypt_data, encrypt_data


class EncryptedField(models.TextField):
    description = 'A field that stores bytes encrypted with JWE (X25519)'

    def get_prep_value(self, value: bytes | None) -> str | None:
        """Encrypt Python bytes into a JWE string for the database."""
        if value is None:
            return None

        if not isinstance(value, bytes):
            raise TypeError(f'EncryptedField must receive bytes, got {type(value)}')

        return encrypt_data(value)

    def get_db_prep_value(
        self,
        value: Any,
        connection: BaseDatabaseWrapper,  # noqa: ARG002
        prepared: bool = False,  # noqa: FBT001, FBT002
    ) -> Any:
        if not prepared:
            value = self.get_prep_value(value)
        return value

    def from_db_value(
        self,
        value: Any,
        expression: Expression,  # noqa: ARG002
        connection: BaseDatabaseWrapper,  # noqa: ARG002
    ) -> Any:
        return self.to_python(value)

    def to_python(self, value: str | None) -> bytes | None:
        """Decrypt a JWE string from the database back into Python bytes with Key Rotation support."""
        if value is None or not isinstance(value, str) or hasattr(self, '_already_decrypted'):
            return value
        return decrypt_data(value)

    def clean(self, value: Any, model_instance: models.Field) -> Any:
        """
        Create and assign a semaphore so that to_python method will not try
        to decrypt an already decrypted value during cleaning of a form
        """
        setattr(self, '_already_decrypted', True)
        ret = super().clean(value, model_instance)
        delattr(self, '_already_decrypted')
        return ret
