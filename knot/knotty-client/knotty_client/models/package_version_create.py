from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.package_checksum import PackageChecksum
    from ..models.package_dependency import PackageDependency


T = TypeVar("T", bound="PackageVersionCreate")


@attr.s(auto_attribs=True)
class PackageVersionCreate:
    """
    Attributes:
        version (Any):
        description (str):
        checksums (List['PackageChecksum']):
        dependencies (List['PackageDependency']):
        repository (Union[Unset, str]):
        tarball (Union[Unset, str]):
    """

    version: Any
    description: str
    checksums: List["PackageChecksum"]
    dependencies: List["PackageDependency"]
    repository: Union[Unset, str] = UNSET
    tarball: Union[Unset, str] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        version = self.version
        description = self.description
        checksums = []
        for checksums_item_data in self.checksums:
            checksums_item = checksums_item_data.to_dict()

            checksums.append(checksums_item)

        dependencies = []
        for dependencies_item_data in self.dependencies:
            dependencies_item = dependencies_item_data.to_dict()

            dependencies.append(dependencies_item)

        repository = self.repository
        tarball = self.tarball

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "version": version,
                "description": description,
                "checksums": checksums,
                "dependencies": dependencies,
            }
        )
        if repository is not UNSET:
            field_dict["repository"] = repository
        if tarball is not UNSET:
            field_dict["tarball"] = tarball

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.package_checksum import PackageChecksum
        from ..models.package_dependency import PackageDependency

        d = src_dict.copy()
        version = d.pop("version")

        description = d.pop("description")

        checksums = []
        _checksums = d.pop("checksums")
        for checksums_item_data in _checksums:
            checksums_item = PackageChecksum.from_dict(checksums_item_data)

            checksums.append(checksums_item)

        dependencies = []
        _dependencies = d.pop("dependencies")
        for dependencies_item_data in _dependencies:
            dependencies_item = PackageDependency.from_dict(dependencies_item_data)

            dependencies.append(dependencies_item)

        repository = d.pop("repository", UNSET)

        tarball = d.pop("tarball", UNSET)

        package_version_create = cls(
            version=version,
            description=description,
            checksums=checksums,
            dependencies=dependencies,
            repository=repository,
            tarball=tarball,
        )

        package_version_create.additional_properties = d
        return package_version_create

    @property
    def additional_keys(self) -> List[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
