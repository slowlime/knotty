from pathlib import Path
from typing import Annotated, Literal
from pydantic import BaseModel, Field
import semver
import toml


class Version(semver.version.Version):
    @classmethod
    def _parse(cls, version):
        if isinstance(version, Version):
            return version

        if isinstance(version, semver.version.Version):
            # i'm sorry
            return cls._parse(str(version))

        return cls.parse(version)

    @classmethod
    def __get_validators__(cls):
        yield cls._parse

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(examples=["1.0.2", "2.15.3-alpha", "21.3.15-beta+12345"])


class PackageManifestV1(BaseModel):
    manifest_version: Literal[1] = 1
    version: Version
    description: str = ""
    repository: str | None = None
    tarball: str | None = None
    checksums: list["PackageChecksum"] = []
    dependencies: list["PackageDependency"] = []


class PackageChecksum(BaseModel):
    algorithm: str
    value: Annotated[str, Field(regex="^[0-9a-fA-F]+$")]


class PackageDependency(BaseModel):
    package: str
    spec: str


PackageManifest = PackageManifestV1


def read_manifest(path: Path) -> "PackageManifestV1":
    parsed = toml.load(path)

    return PackageManifest(**parsed)


PackageManifestV1.update_forward_refs()
