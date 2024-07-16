import copy
import logging

from fastapi.testclient import TestClient
import pytest
from pytest_assert_utils import util as assert_util

from knotty.tests import TEST_USER, make_user, to_fuzzy_dict
from knotty.tests.test_package import make_package_model

logger = logging.getLogger(__name__)

TEST_NAMESPACE = {
    "name": "test-ns",
    "description": "Namespace description",
    "homepage": None,
}


def make_namespace_model(ns: dict = TEST_NAMESPACE, user: str = TEST_USER) -> dict:
    ns = copy.deepcopy(ns)

    ns["created_date"] = assert_util.Any(str)
    ns["users"] = [
        {
            "username": user,
            "role": "owner",
            "added_date": assert_util.Any(str),
            "added_by": user,
            "updated_date": assert_util.Any(str),
            "updated_by": user,
        },
    ]
    ns["roles"] = [
        {
            "name": "owner",
            "permissions": [
                "namespace-owner",
            ],
            "created_date": assert_util.Any(str),
            "created_by": user,
            "updated_date": assert_util.Any(str),
            "updated_by": user,
        },
    ]

    return ns


def test_create_namespace(auth_client: TestClient):
    r = auth_client.post("/namespace", json=TEST_NAMESPACE)
    assert r.status_code == 201

    r = auth_client.get(f"/namespace/{TEST_NAMESPACE['name']}")
    assert r.status_code == 200

    assert r.json() == make_namespace_model()


@pytest.fixture
def namespace(auth_client: TestClient) -> dict:
    r = auth_client.post("/namespace", json=TEST_NAMESPACE)
    assert r.status_code == 201

    return make_namespace_model()


def test_create_namespace_user(auth_client: TestClient, namespace: dict):
    make_user(
        auth_client,
        username="second-user",
        email="second@localhost.localdomain",
        password="hello world",
    )

    r = auth_client.post(
        f"/namespace/{namespace['name']}/user",
        json={
            "username": "second-user",
            "role": "owner",
        },
    )
    assert r.status_code == 201

    user_data = {
        "username": "second-user",
        "role": "owner",
        "added_date": assert_util.Any(str),
        "added_by": TEST_USER,
        "updated_date": assert_util.Any(str),
        "updated_by": TEST_USER,
    }

    r = auth_client.get(f"/namespace/{namespace['name']}/user/second-user")
    assert r.status_code == 200
    assert r.json() == user_data

    namespace["users"].append(user_data)
    r = auth_client.get(f"/namespace/{namespace['name']}")
    assert r.status_code == 200
    assert r.json() == to_fuzzy_dict(
        namespace,
        {
            ("users",): "unordered",
        },
    )


def test_create_namespace_role(auth_client: TestClient, namespace: dict):
    make_user(
        auth_client,
        username="second-user",
        email="second@localhost.localdomain",
        password="hello world",
    )

    r = auth_client.post(
        f"/namespace/{namespace['name']}/role",
        json={
            "name": "second-user-role",
            "permissions": [
                "package-create",
                "package-edit",
            ],
        },
    )
    assert r.status_code == 201

    role_data = {
        "name": "second-user-role",
        "permissions": [
            "package-create",
            "package-edit",
        ],
        "created_date": assert_util.Any(),
        "created_by": TEST_USER,
        "updated_date": assert_util.Any(),
        "updated_by": TEST_USER,
    }

    r = auth_client.get(f"/namespace/{namespace['name']}/role/{role_data['name']}")
    assert r.status_code == 200
    assert r.json() == to_fuzzy_dict(
        role_data,
        {
            ("permissions",): "unordered",
        },
    )

    namespace["roles"].append(role_data)

    r = auth_client.get(f"/namespace/{namespace['name']}")
    assert r.status_code == 200
    assert r.json() == to_fuzzy_dict(
        namespace,
        {
            ("roles",): "unordered",
            ("roles", None, "permissions"): "unordered",
        },
    )


def test_namespace_package(auth_client: TestClient, namespace: dict):
    second_user_token = make_user(
        auth_client,
        username="second-user",
        email="second@localhost.localdomain",
        password="hello world",
    )

    r = auth_client.post(
        f"/namespace/{namespace['name']}/role",
        json={
            "name": "second-user-role",
            "permissions": [
                "package-create",
                "package-edit",
            ],
        },
    )
    assert r.status_code == 201

    r = auth_client.post(
        f"/namespace/{namespace['name']}/user",
        json={
            "username": "second-user",
            "role": "second-user-role",
        },
    )
    assert r.status_code == 201

    prev_header = auth_client.headers["Authorization"]
    auth_client.headers["Authorization"] = f"Bearer {second_user_token}"
    package = {
        "name": "test-ns-package",
        "summary": "A package belonging to a namespace",
        "namespace": namespace["name"],
        "labels": ["test", "namespaces"],
        "versions": [
            {
                "version": "0.0.1",
                "description": "The initial version.",
                "repository": None,
                "tarball": None,
                "checksums": [],
                "dependencies": [],
            },
        ],
        "tags": [],
    }

    r = auth_client.post("/package", json=package)
    assert r.status_code == 201

    package = make_package_model(package, "second-user")
    r = auth_client.get(f"/package/{package['name']}")
    assert r.status_code == 200
    assert r.json() == to_fuzzy_dict(
        package,
        {
            ("labels",): "unordered",
        },
    )

    auth_client.headers["Authorization"] = prev_header
    r = auth_client.post(
        f"/package/{package['name']}/tag",
        json={
            "name": "test",
            "version": "0.0.1",
        },
    )
    assert r.status_code == 201

    r = auth_client.get(f"/package/{package['name']}/tag/test")
    assert r.status_code == 200
    assert r.json() == {
        "name": "test",
        "version": "0.0.1",
    }
