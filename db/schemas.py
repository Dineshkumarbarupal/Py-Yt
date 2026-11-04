from pydantic import AnyHttpUrl, BaseModel, ConfigDict, EmailStr, Field

class RegisterRequest(BaseModel):
    email: EmailStr
    display_name: str = Field(min_length=2, max_length=80)
    password: str = Field(min_length=12, max_length=128)

class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)

class ProfileUpdate(BaseModel):
    display_name: str = Field(min_length=2, max_length=80)
    bio: str = Field(default="", max_length=500)
    avatar_url: AnyHttpUrl | None = None

class PasswordChangeRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=12, max_length=128)

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    email: EmailStr
    display_name: str
    bio: str
    avatar_url: str | None
    role: str
