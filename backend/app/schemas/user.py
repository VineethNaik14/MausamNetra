import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, ConfigDict

from app.models.user import UserRole


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    email: EmailStr
    role: UserRole
    is_active: bool
    created_at: datetime

    # NOTE: password_hash is intentionally never included in any response schema.


class UserCreateInternal(BaseModel):
    """
    Internal-only creation schema (used by scripts/create_admin.py and the
    seed script). This is NOT exposed via any public API route - there is
    no public registration endpoint in this prototype, and admin accounts
    in particular must only be created through controlled scripts.
    """

    name: str
    email: EmailStr
    password: str
    role: UserRole = UserRole.USER
