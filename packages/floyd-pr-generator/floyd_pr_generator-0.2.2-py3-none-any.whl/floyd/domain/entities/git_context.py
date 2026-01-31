from pydantic import BaseModel, Field

from floyd.domain.value_objects.branch import Branch


class GitContext(BaseModel):
    current_branch: Branch
    target_branch: Branch
    commits: str = Field(default="")
    diff: str = Field(default="")
    diff_stat: str = Field(default="")

    def has_changes(self) -> bool:
        return bool(self.diff.strip())
