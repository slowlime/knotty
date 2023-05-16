from .. import app, error, model, schema, storage
from ..db import SessionDep


def label_model_to_schema(label: model.Label) -> str:
    return label.name


def package_model_to_schema_brief(package: model.Package) -> schema.PackageBrief:
    if package.namespace is not None:
        namespace = package.namespace.namespace
    else:
        namespace = None

    return schema.PackageBrief(
        name=package.name,
        summary=package.summary,
        labels=[label_model_to_schema(label) for label in package.labels],
        namespace=namespace,
        owners=[owner.username for owner in package.owners],
        updated_date=package.updated_date,
        downloads=package.downloads,
    )


def package_checksum_model_to_schema(
    checksum: model.PackageVersionChecksum,
) -> schema.PackageChecksum:
    return schema.PackageChecksum(
        algorithm=checksum.algorithm,
        value=checksum.value.hex(),
    )


def package_dependency_model_to_schema(
    dep: model.PackageVersionDependency,
) -> schema.PackageDependency:
    return schema.PackageDependency.from_orm(dep)


def package_version_model_to_schema(
    version: model.PackageVersion,
) -> schema.PackageVersion:
    checksums = [
        package_checksum_model_to_schema(checksum) for checksum in version.checksums
    ]
    dependencies = [
        package_dependency_model_to_schema(dep) for dep in version.dependencies
    ]

    return schema.PackageVersion(
        version=version.version,
        downloads=version.downloads,
        created_date=version.created_date,
        created_by=version.created_by.username,
        description=version.description,
        repository=version.repository,
        tarball=version.tarball,
        checksums=checksums,
        dependencies=dependencies,
    )


def package_tag_model_to_schema(tag: model.PackageTag) -> schema.PackageTag:
    return schema.PackageTag.from_orm(tag)


def package_model_to_schema(package: model.Package) -> schema.Package:
    brief = package_model_to_schema_brief(package)

    versions = [
        package_version_model_to_schema(version) for version in package.versions
    ]
    tags = [package_tag_model_to_schema(tag) for tag in package.tags]

    return schema.Package(
        created_date=package.created_date,
        created_by=package.created_by.username,
        updated_by=package.updated_by.username,
        versions=versions,
        tags=tags,
        **brief.dict()
    )


@app.get("/package")
def get_packages(session: SessionDep) -> list[schema.PackageBrief]:
    packages = storage.get_packages(session)

    return [package_model_to_schema_brief(package) for package in packages]


@app.get("/package/{package}")
def get_package(session: SessionDep, package: str) -> schema.Package:
    p = storage.get_package(session, package)

    if p is None:
        raise error.not_found()

    return package_model_to_schema(p)
