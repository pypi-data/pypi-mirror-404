from floyd.domain.exceptions.domain_exception import DomainException


class BranchNotFoundException(DomainException):
    def __init__(self, branch_name: str) -> None:
        super().__init__(f"Branch '{branch_name}' not found")
        self.branch_name = branch_name
