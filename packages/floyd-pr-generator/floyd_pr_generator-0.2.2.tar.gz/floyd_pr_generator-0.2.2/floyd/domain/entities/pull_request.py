from pydantic import BaseModel, Field, field_validator


class PullRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=256)
    body: str = Field(default="")
    head_branch: str = Field(..., min_length=1)

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

    @field_validator("head_branch")
    @classmethod
    def validate_head_branch(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Head branch cannot be empty")
        return v
