from enum import Enum


class PermissionCode(str, Enum):
    NAMESPACE_ADMIN = "namespace-admin"
    NAMESPACE_EDIT = "namespace-edit"
    NAMESPACE_OWNER = "namespace-owner"
    PACKAGE_CREATE = "package-create"
    PACKAGE_EDIT = "package-edit"

    def __str__(self) -> str:
        return str(self.value)
