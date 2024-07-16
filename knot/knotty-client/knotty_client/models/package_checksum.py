from typing import Any, Dict, List, Type, TypeVar

import attr

from ..models.checksum_algorithm import ChecksumAlgorithm

T = TypeVar("T", bound="PackageChecksum")


@attr.s(auto_attribs=True)
class PackageChecksum:
    """
    Attributes:
        algorithm (ChecksumAlgorithm): An enumeration.
        value (str):
    """

    algorithm: ChecksumAlgorithm
    value: str
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        algorithm = self.algorithm.value

        value = self.value

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "algorithm": algorithm,
                "value": value,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        algorithm = ChecksumAlgorithm(d.pop("algorithm"))

        value = d.pop("value")

        package_checksum = cls(
            algorithm=algorithm,
            value=value,
        )

        package_checksum.additional_properties = d
        return package_checksum

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
