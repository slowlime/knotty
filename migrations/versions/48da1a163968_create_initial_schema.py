"""Create initial schema

Revision ID: 48da1a163968
Revises:
Create Date: 2023-05-23 19:18:11.914068

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "48da1a163968"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_collation(  # type: ignore
        "case_insensitive",
        provider="icu",
        locale="und-u-ks-level2",
        deterministic=False,
    )

    op.create_table(
        "labels",
        sa.Column("id", sa.Integer(), sa.Identity(always=True), nullable=False),
        sa.Column("name", sa.String(32), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_labels")),
        sa.UniqueConstraint("name", name=op.f("uq_labels_name")),
    )

    op.create_table(
        "namespace",
        sa.Column("id", sa.Integer(), sa.Identity(always=True), nullable=False),
        sa.Column(
            "namespace", sa.String(32, collation="case_insensitive"), nullable=False
        ),
        sa.Column("description", sa.String(131072), nullable=False),
        sa.Column("homepage", sa.String(2048), nullable=True),
        sa.Column("created_date", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_namespace")),
        sa.UniqueConstraint("namespace", name=op.f("uq_namespace_namespace")),
    )

    op.create_table(
        "permissions",
        sa.Column("id", sa.Integer(), sa.Identity(always=True), nullable=False),
        sa.Column(
            "code",
            sa.Enum(
                "namespace_owner",
                "namespace_admin",
                "namespace_edit",
                "package_create",
                "package_edit",
                name="permissioncode",
                native_enum=False,
                create_constraint=True,
            ),
            nullable=False,
        ),
        sa.Column("description", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_permissions")),
        sa.UniqueConstraint("code", name=op.f("uq_permissions_code")),
    )

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), sa.Identity(always=True), nullable=False),
        sa.Column(
            "username", sa.String(32, collation="case_insensitive"), nullable=False
        ),
        sa.Column("email", sa.String(64, collation="case_insensitive"), nullable=False),
        sa.Column("pwhash", sa.String(), nullable=False),
        sa.Column("registered", sa.DateTime(), nullable=False),
        sa.Column(
            "role",
            sa.Enum("regular", "admin", "banned", name="userrole", native_enum=False,
            create_constraint=True),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        sa.UniqueConstraint("email", name=op.f("uq_users_email")),
        sa.UniqueConstraint("username", name=op.f("uq_users_username")),
    )

    op.create_table(
        "namespace_roles",
        sa.Column("id", sa.Integer(), sa.Identity(always=True), nullable=False),
        sa.Column("namespace_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(32, collation="case_insensitive"), nullable=False),
        sa.Column("created_date", sa.DateTime(), nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), nullable=False),
        sa.Column("updated_date", sa.DateTime(), nullable=False),
        sa.Column("updated_by_user_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["created_by_user_id"],
            ["users.id"],
            name=op.f("fk_namespace_roles_created_by_user_id_users"),
        ),
        sa.ForeignKeyConstraint(
            ["namespace_id"],
            ["namespace.id"],
            name=op.f("fk_namespace_roles_namespace_id_namespace"),
            onupdate="CASCADE",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["updated_by_user_id"],
            ["users.id"],
            name=op.f("fk_namespace_roles_updated_by_user_id_users"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_namespace_roles")),
        sa.UniqueConstraint(
            "namespace_id",
            "name",
            name=op.f("uq_namespace_roles_namespace_id"),
        ),
    )

    op.create_table(
        "packages",
        sa.Column("id", sa.Integer(), sa.Identity(always=True), nullable=False),
        sa.Column(
            "name",
            sa.String(
                32,
            ),
            nullable=False,
        ),
        sa.Column("namespace_id", sa.Integer(), nullable=True),
        sa.Column("summary", sa.String(256), nullable=False),
        sa.Column("created_date", sa.DateTime(), nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), nullable=False),
        sa.Column("updated_date", sa.DateTime(), nullable=False),
        sa.Column("updated_by_user_id", sa.Integer(), nullable=False),
        sa.Column("downloads", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["created_by_user_id"],
            ["users.id"],
            name=op.f("fk_packages_created_by_user_id_users"),
        ),
        sa.ForeignKeyConstraint(
            ["namespace_id"],
            ["namespace.id"],
            name=op.f("fk_packages_namespace_id_namespace"),
            onupdate="SET NULL",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["updated_by_user_id"],
            ["users.id"],
            name=op.f("fk_packages_updated_by_user_id_users"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_packages")),
        sa.UniqueConstraint("name", name=op.f("uq_packages_name")),
    )

    op.create_table(
        "namespace_role_permissions",
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.Column("permission_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["permission_id"],
            ["permissions.id"],
            name=op.f("fk_namespace_role_permissions_permission_id_permissions"),
        ),
        sa.ForeignKeyConstraint(
            ["role_id"],
            ["namespace_roles.id"],
            name=op.f("fk_namespace_role_permissions_role_id_namespace_roles"),
            onupdate="CASCADE",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "role_id",
            "permission_id",
            name=op.f("pk_namespace_role_permissions"),
        ),
    )

    op.create_table(
        "namespace_users",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("namespace_id", sa.Integer(), nullable=False),
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.Column("added_date", sa.DateTime(), nullable=False),
        sa.Column("added_by_user_id", sa.Integer(), nullable=False),
        sa.Column("updated_date", sa.DateTime(), nullable=False),
        sa.Column("updated_by_user_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["added_by_user_id"],
            ["users.id"],
            name=op.f("fk_namespace_users_added_by_user_id_users"),
        ),
        sa.ForeignKeyConstraint(
            ["namespace_id"],
            ["namespace.id"],
            name=op.f("fk_namespace_users_namespace_id_namespace"),
            onupdate="CASCADE",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["role_id"],
            ["namespace_roles.id"],
            name=op.f("fk_namespace_users_role_id_namespace_roles"),
        ),
        sa.ForeignKeyConstraint(
            ["updated_by_user_id"],
            ["users.id"],
            name=op.f("fk_namespace_users_updated_by_user_id_users"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_namespace_users_user_id_users"),
        ),
        sa.PrimaryKeyConstraint(
            "user_id", "namespace_id", name=op.f("pk_namespace_users")
        ),
    )

    op.create_table(
        "package_labels",
        sa.Column("package_id", sa.Integer(), nullable=False),
        sa.Column("label_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["label_id"],
            ["labels.id"],
            name=op.f("fk_package_labels_label_id_labels"),
        ),
        sa.ForeignKeyConstraint(
            ["package_id"],
            ["packages.id"],
            name=op.f("fk_package_labels_package_id_packages"),
            onupdate="CASCADE",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "package_id", "label_id", name=op.f("pk_package_labels")
        ),
    )

    op.create_table(
        "package_owners",
        sa.Column("package_id", sa.Integer(), nullable=False),
        sa.Column("owner_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["owner_id"],
            ["users.id"],
            name=op.f("fk_package_owners_owner_id_users"),
        ),
        sa.ForeignKeyConstraint(
            ["package_id"],
            ["packages.id"],
            name=op.f("fk_package_owners_package_id_packages"),
            onupdate="CASCADE",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "package_id", "owner_id", name=op.f("pk_package_owners")
        ),
    )

    op.create_table(
        "package_versions",
        sa.Column("id", sa.Integer(), sa.Identity(always=True), nullable=False),
        sa.Column("package_id", sa.Integer(), nullable=False),
        sa.Column("version", sa.String(), nullable=False),
        sa.Column("downloads", sa.Integer(), nullable=False),
        sa.Column("created_date", sa.DateTime(), nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), nullable=False),
        sa.Column("description", sa.String(131072), nullable=False),
        sa.Column("repository", sa.String(2048), nullable=True),
        sa.Column("tarball", sa.String(2048), nullable=True),
        sa.ForeignKeyConstraint(
            ["created_by_user_id"],
            ["users.id"],
            name=op.f("fk_package_versions_created_by_user_id_users"),
        ),
        sa.ForeignKeyConstraint(
            ["package_id"],
            ["packages.id"],
            name=op.f("fk_package_versions_package_id_packages"),
            onupdate="CASCADE",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_package_versions")),
        sa.UniqueConstraint(
            "package_id",
            "version",
            name=op.f("uq_package_versions_package_id"),
        ),
    )

    op.create_table(
        "package_tags",
        sa.Column("package_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(32), nullable=False),
        sa.Column("version_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["package_id"],
            ["packages.id"],
            name=op.f("fk_package_tags_package_id_packages"),
            onupdate="CASCADE",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["version_id"],
            ["package_versions.id"],
            name=op.f("fk_package_tags_version_id_package_versions"),
        ),
        sa.PrimaryKeyConstraint("package_id", "name", name=op.f("pk_package_tags")),
    )

    op.create_table(
        "package_version_checksums",
        sa.Column("version_id", sa.Integer(), nullable=False),
        sa.Column(
            "algorithm",
            sa.Enum(
                "md5",
                "sha1",
                "sha256",
                "sha512",
                name="checksumalgorithm",
                native_enum=False,
                create_constraint=True,
            ),
            nullable=False,
        ),
        sa.Column("value", sa.LargeBinary(), nullable=False),
        sa.ForeignKeyConstraint(
            ["version_id"],
            ["package_versions.id"],
            name=op.f("fk_package_version_checksums_version_id_package_versions"),
            onupdate="CASCADE",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "version_id",
            "algorithm",
            name=op.f("pk_package_version_checksums"),
        ),
    )

    op.create_table(
        "package_version_dependencies",
        sa.Column("version_id", sa.Integer(), nullable=False),
        sa.Column("dep_package_id", sa.Integer(), nullable=False),
        sa.Column("spec", sa.String(40), nullable=False),
        sa.ForeignKeyConstraint(
            ["dep_package_id"],
            ["packages.id"],
            name=op.f("fk_package_version_dependencies_dep_package_id_packages"),
        ),
        sa.ForeignKeyConstraint(
            ["version_id"],
            ["package_versions.id"],
            name=op.f("fk_package_version_dependencies_version_id_package_versions"),
            onupdate="CASCADE",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "version_id",
            "dep_package_id",
            name=op.f("pk_package_version_dependencies"),
        ),
    )


def downgrade() -> None:
    op.drop_table("package_version_dependencies")
    op.drop_table("package_version_checksums")
    op.drop_table("package_tags")
    op.drop_table("package_versions")
    op.drop_table("package_owners")
    op.drop_table("package_labels")
    op.drop_table("namespace_users")
    op.drop_table("namespace_role_permissions")
    op.drop_table("packages")
    op.drop_table("namespace_roles")
    op.drop_table("users")
    op.drop_table("permissions")
    op.drop_table("namespace")
    op.drop_table("labels")
    op.drop_collation("case_insensitive")  # type: ignore
