from pydantic import BaseModel


class RegisterUsernameV0(BaseModel):
    username: str
    password: str
    admin_password: str


class LoginUsernameV0(BaseModel):
    username: str
    password: str


class RemoveAppForSelfV0(BaseModel):
    password: str


class ResetPasswordAndLoginUsingBackupCodeV0(BaseModel):
    backup_code: str
    username: str
    new_password: str
    logout_other_sessions: bool = False


class ResetPasswordAndLoginUsingResetEmailCodeV0(BaseModel):
    reset_email_code: str
    username: str
    new_password: str
    logout_other_sessions: bool = False


class UpdatePasswordV0(BaseModel):
    old_password: str
    new_password: str
    logout_other_sessions: bool = False
