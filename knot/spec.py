from dataclasses import dataclass

from knot.manifest import Version


Tag = str


@dataclass
class PackageSpec:
    package: str
    version: Tag | Version | None

    @staticmethod
    def from_str(spec: str) -> "PackageSpec":
        if len(unpacked := spec.rsplit(':', 1)) == 2:
            [package, version_str] = unpacked
            version = Version.parse(version_str)

            return PackageSpec(package, version)

        if len(unpacked := spec.rsplit('@', 1)) == 2:
            [package, tag] = unpacked
            return PackageSpec(package, tag)

        return PackageSpec(spec, None)
