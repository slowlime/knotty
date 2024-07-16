from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union, cast

import attr

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.package_tag import PackageTag
    from ..models.package_version_create import PackageVersionCreate


T = TypeVar("T", bound="PackageCreate")


@attr.s(auto_attribs=True)
class PackageCreate:
    """
    Attributes:
        name (str):
        summary (str):
        versions (List['PackageVersionCreate']):
        tags (List['PackageTag']):
        namespace (Union[Unset, str]):
        labels (Union[Unset, List[str]]):
        owners (Union[Unset, List[str]]):
    """

    name: str
    summary: str
    versions: List["PackageVersionCreate"]
    tags: List["PackageTag"]
    namespace: Union[Unset, str] = UNSET
    labels: Union[Unset, List[str]] = UNSET
    owners: Union[Unset, List[str]] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        name = self.name
        summary = self.summary
        versions = []
        for versions_item_data in self.versions:
            versions_item = versions_item_data.to_dict()

            versions.append(versions_item)

        tags = []
        for tags_item_data in self.tags:
            tags_item = tags_item_data.to_dict()

            tags.append(tags_item)

        namespace = self.namespace
        labels: Union[Unset, List[str]] = UNSET
        if not isinstance(self.labels, Unset):
            labels = self.labels

        owners: Union[Unset, List[str]] = UNSET
        if not isinstance(self.owners, Unset):
            owners = self.owners

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "summary": summary,
                "versions": versions,
                "tags": tags,
            }
        )
        if namespace is not UNSET:
            field_dict["namespace"] = namespace
        if labels is not UNSET:
            field_dict["labels"] = labels
        if owners is not UNSET:
            field_dict["owners"] = owners

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.package_tag import PackageTag
        from ..models.package_version_create import PackageVersionCreate

        d = src_dict.copy()
        name = d.pop("name")

        summary = d.pop("summary")

        versions = []
        _versions = d.pop("versions")
        for versions_item_data in _versions:
            versions_item = PackageVersionCreate.from_dict(versions_item_data)

            versions.append(versions_item)

        tags = []
        _tags = d.pop("tags")
        for tags_item_data in _tags:
            tags_item = PackageTag.from_dict(tags_item_data)

            tags.append(tags_item)

        namespace = d.pop("namespace", UNSET)

        labels = cast(List[str], d.pop("labels", UNSET))

        owners = cast(List[str], d.pop("owners", UNSET))

        package_create = cls(
            name=name,
            summary=summary,
            versions=versions,
            tags=tags,
            namespace=namespace,
            labels=labels,
            owners=owners,
        )

        package_create.additional_properties = d
        return package_create

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
