from typing import List

from pydantic import BaseModel
from square_database_structure.square.authentication.enums import RecoveryMethodEnum


class DeleteUserV0(BaseModel):
    password: str


class LogoutAppsV0(BaseModel):
    app_names: List[str]


class ValidateEmailVerificationCodeV0(BaseModel):
    verification_code: str


class SendResetPasswordEmailV0(BaseModel):
    username: str


class UpdateUserRecoveryMethodsV0(BaseModel):
    recovery_methods_to_add: List[RecoveryMethodEnum] = None
    recovery_methods_to_remove: List[RecoveryMethodEnum] = None
