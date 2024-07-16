import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union, cast

import attr
from dateutil.parser import isoparse

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.package_tag import PackageTag
    from ..models.package_version import PackageVersion


T = TypeVar("T", bound="Package")


@attr.s(auto_attribs=True)
class Package:
    """
    Attributes:
        name (str):
        summary (str):
        labels (List[str]):
        owners (List[str]):
        updated_date (datetime.datetime):
        downloads (int):
        created_date (datetime.datetime):
        created_by (str):
        updated_by (str):
        versions (List['PackageVersion']):
        tags (List['PackageTag']):
        namespace (Union[Unset, str]):
    """

    name: str
    summary: str
    labels: List[str]
    owners: List[str]
    updated_date: datetime.datetime
    downloads: int
    created_date: datetime.datetime
    created_by: str
    updated_by: str
    versions: List["PackageVersion"]
    tags: List["PackageTag"]
    namespace: Union[Unset, str] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        name = self.name
        summary = self.summary
        labels = self.labels

        owners = self.owners

        updated_date = self.updated_date.isoformat()

        downloads = self.downloads
        created_date = self.created_date.isoformat()

        created_by = self.created_by
        updated_by = self.updated_by
        versions = []
        for versions_item_data in self.versions:
            versions_item = versions_item_data.to_dict()

            versions.append(versions_item)

        tags = []
        for tags_item_data in self.tags:
            tags_item = tags_item_data.to_dict()

            tags.append(tags_item)

        namespace = self.namespace

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "summary": summary,
                "labels": labels,
                "owners": owners,
                "updated_date": updated_date,
                "downloads": downloads,
                "created_date": created_date,
                "created_by": created_by,
                "updated_by": updated_by,
                "versions": versions,
                "tags": tags,
            }
        )
        if namespace is not UNSET:
            field_dict["namespace"] = namespace

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.package_tag import PackageTag
        from ..models.package_version import PackageVersion

        d = src_dict.copy()
        name = d.pop("name")

        summary = d.pop("summary")

        labels = cast(List[str], d.pop("labels"))

        owners = cast(List[str], d.pop("owners"))

        updated_date = isoparse(d.pop("updated_date"))

        downloads = d.pop("downloads")

        created_date = isoparse(d.pop("created_date"))

        created_by = d.pop("created_by")

        updated_by = d.pop("updated_by")

        versions = []
        _versions = d.pop("versions")
        for versions_item_data in _versions:
            versions_item = PackageVersion.from_dict(versions_item_data)

            versions.append(versions_item)

        tags = []
        _tags = d.pop("tags")
        for tags_item_data in _tags:
            tags_item = PackageTag.from_dict(tags_item_data)

            tags.append(tags_item)

        namespace = d.pop("namespace", UNSET)

        package = cls(
            name=name,
            summary=summary,
            labels=labels,
            owners=owners,
            updated_date=updated_date,
            downloads=downloads,
            created_date=created_date,
            created_by=created_by,
            updated_by=updated_by,
            versions=versions,
            tags=tags,
            namespace=namespace,
        )

        package.additional_properties = d
        return package

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
