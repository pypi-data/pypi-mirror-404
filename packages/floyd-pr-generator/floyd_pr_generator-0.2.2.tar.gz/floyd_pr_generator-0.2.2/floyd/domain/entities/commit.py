from pydantic import BaseModel, Field, field_validator


class Commit(BaseModel):
    title: str = Field(..., min_length=1, max_length=256)
    body: str = Field(default="")

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Title cannot be empty")
        return v

    @field_validator("body")
    @classmethod
    def validate_body(cls, v: str) -> str:
        return v.strip()
