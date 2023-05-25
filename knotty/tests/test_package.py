import copy
import logging
import pytest
from pytest_assert_utils import util as assert_util
from pytest_unordered import unordered
from fastapi.testclient import TestClient

from knotty.tests import TEST_USER, to_fuzzy_dict


logger = logging.getLogger(__name__)

TEST_PACKAGE = {
    "name": "test-package",
    "summary": "A short description of the package.",
    "namespace": None,
    "labels": ["label-1", "package", "hello"],
    "versions": [
        {
            "version": "0.0.1",
            "description": "The initial version.",
            "repository": None,
            "tarball": "https://example.com",
            "checksums": [
                {
                    "algorithm": "md5",
                    "value": "12345678901234567890123456789012",
                },
                {
                    "algorithm": "sha256",
                    "value": "12345678901234567890123456789012" * 2,
                },
            ],
            "dependencies": [],
        },
    ],
    "tags": [
        {
            "name": "latest",
            "version": "0.0.1",
        },
        {
            "name": "snapshot",
            "version": "0.0.1",
        },
    ],
}


def test_get_packages_empty(client: TestClient):
    r = client.get("/package")
    assert r.status_code == 200
    assert r.json() == []


def test_create_package(auth_client: TestClient):
    r = auth_client.post("/package", json=TEST_PACKAGE)
    assert r.status_code == 201

    r = auth_client.get("/package/test-package")
    assert r.status_code == 200
    assert r.json() == {
        "name": "test-package",
        "summary": "A short description of the package.",
        "namespace": None,
        "labels": unordered(["label-1", "package", "hello"]),
        "owners": unordered([TEST_USER]),
        "updated_date": assert_util.Any(str),
        "downloads": 0,
        "created_date": assert_util.Any(str),
        "created_by": TEST_USER,
        "updated_by": TEST_USER,
        "versions": unordered(
            [
                {
                    "version": "0.0.1",
                    "description": "The initial version.",
                    "repository": None,
                    "tarball": "https://example.com",
                    "checksums": unordered(
                        [
                            {
                                "algorithm": "md5",
                                "value": "12345678901234567890123456789012",
                            },
                            {
                                "algorithm": "sha256",
                                "value": "12345678901234567890123456789012" * 2,
                            },
                        ]
                    ),
                    "dependencies": [],
                    "downloads": 0,
                    "created_date": assert_util.Any(str),
                    "created_by": TEST_USER,
                },
            ]
        ),
        "tags": unordered(
            [
                {
                    "name": "latest",
                    "version": "0.0.1",
                },
                {
                    "name": "snapshot",
                    "version": "0.0.1",
                },
            ]
        ),
    }


def make_package_model(package: dict = TEST_PACKAGE, user: str = TEST_USER) -> dict:
    p = copy.deepcopy(package)

    p["created_by"] = user
    p["created_date"] = assert_util.Any(str)
    p["updated_by"] = user
    p["updated_date"] = assert_util.Any(str)
    p["downloads"] = 0
    p["owners"] = [user]

    for version in p["versions"]:
        version["created_by"] = user
        version["created_date"] = assert_util.Any(str)
        version["downloads"] = 0

    return p


@pytest.fixture
def package(auth_client: TestClient) -> dict:
    r = auth_client.post("/package", json=TEST_PACKAGE)
    assert r.status_code == 201

    return make_package_model()


def test_edit_package(auth_client: TestClient, package: dict):
    r = auth_client.post(
        f"/package/{package['name']}",
        json={
            "name": "another-name",
            "summary": "Hello world",
            "namespace": None,
            "labels": ["hello", "world"],
            "owners": [TEST_USER],
        },
    )
    assert r.status_code == 200

    package["name"] = "another-name"
    package["summary"] = "Hello world"
    package["labels"] = ["hello", "world"]

    r = auth_client.get(f"/package/{package['name']}")
    assert r.status_code == 200
    assert r.json() == to_fuzzy_dict(
        package,
        {
            ("labels",): "unordered",
            ("owners",): "unordered",
            ("versions",): "unordered",
            ("versions", None, "checksums"): "unordered",
            ("versions", None, "dependencies"): "unordered",
            ("tags",): "unordered",
        },
    )


def test_edit_no_owners(auth_client: TestClient, package: dict):
    r = auth_client.post(
        f"/package/{package['name']}",
        json={
            "name": package["name"],
            "summary": package["summary"],
            "namespace": None,
            "labels": package["labels"],
            "owners": [],
        },
    )
    assert r.status_code == 400
    assert "without owner" in r.json()["detail"]
