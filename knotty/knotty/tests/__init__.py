from functools import cmp_to_key
from typing import Any, Literal, TypeVar
from typing_extensions import assert_never
from fastapi.testclient import TestClient

from pytest_assert_utils import util as assert_util
from pytest_unordered import unordered


TEST_USER = "tester"
TEST_EMAIL = "tester@localhost.localdomain"
TEST_PASSWD = "test"

SubstitutionMatcher = str | int | None
SubstitutionPath = tuple[SubstitutionMatcher, ...]
SubstitutionKind = Literal["any(str)"] | Literal["unordered"]
SubstitutionTable = dict[tuple[SubstitutionMatcher, ...], SubstitutionKind]


def is_accepted(
    k: str | int, path: SubstitutionPath, depth: int, partial: bool = True
) -> bool:
    if depth >= len(path):
        # the path matches a parent
        return False

    if depth + 1 < len(path) and not partial:
        # the path matches a child
        return False

    matcher = path[depth]

    if matcher is None:
        return True

    if isinstance(matcher, str):
        if isinstance(k, str):
            return k == matcher

        return False

    if isinstance(matcher, int):
        if isinstance(k, int):
            return k == matcher

        return False

    assert_never(matcher)


def get_matcher_range(
    k: str | int,
    paths: list[SubstitutionPath],
    start: int,
    end: int,
    depth: int,
) -> tuple[int, int]:
    for i in range(start, end):
        if is_accepted(k, paths[i], depth):
            break
    else:
        return (end, end)

    range_start = i

    for i in range(range_start, end):
        if not is_accepted(k, paths[i], depth):
            break
    else:
        return (range_start, end)

    range_end = i

    return (range_start, range_end)


def apply_substitution(v: Any, substitution: SubstitutionKind):
    match substitution:
        case "any(str)":
            return assert_util.Any()

        case "unordered":
            return unordered(v)

        case _:
            assert_never(substitution)


T = TypeVar("T")


def apply_substitutions(
    d: T,
    paths: list[SubstitutionPath],
    substitutions: SubstitutionTable,
    start: int,
    end: int,
    depth: int = 0,
) -> T:
    if not isinstance(d, list | dict):
        return d

    result = type(d)()

    if isinstance(d, dict):
        it = d.items()
    else:
        it = ((k, d[k]) for k in range(len(d)))

    for k, v in it:
        matcher_start, matcher_end = get_matcher_range(k, paths, start, end, depth)

        if isinstance(v, dict):
            v = apply_substitutions(
                v, paths, substitutions, matcher_start, matcher_end, depth + 1
            )
        elif isinstance(v, list):
            v = apply_substitutions(
                v, paths, substitutions, matcher_start, matcher_end, depth + 1
            )

        if isinstance(k, str | int):
            for i in range(matcher_start, matcher_end):
                if is_accepted(k, paths[i], depth, partial=False):
                    v = apply_substitution(v, substitutions[paths[i]])

        if isinstance(result, dict):
            result[k] = v
        elif isinstance(result, list):
            assert len(result) == k
            result.append(v)
        else:
            assert_never(result)

    return result


def to_fuzzy_dict(d: dict, substitutions: SubstitutionTable) -> dict:
    def key_comparator(
        lhs: SubstitutionPath, rhs: SubstitutionPath, field: int = 0
    ) -> int:
        # shorter paths go later
        if len(lhs) <= field and len(rhs) <= field:
            return 0
        elif len(lhs) <= field:
            return 1
        elif len(rhs) <= field:
            return -1

        l = lhs[field]  # noqa: E741
        r = rhs[field]

        # None path matcher follows non-None matchers
        if l is None and r is None:
            return key_comparator(lhs, rhs, field + 1)
        elif l is None:
            return 1
        elif r is None:
            return -1

        if isinstance(l, str) and isinstance(r, str):
            # str-str compare naturally
            if l < r:
                return -1
            elif l > r:
                return 1
            else:
                return key_comparator(lhs, rhs, field + 1)
        elif isinstance(l, int) and isinstance(r, int):
            # int-int compare naturally
            if l < r:
                return -1
            elif l > r:
                return 1
            else:
                return key_comparator(lhs, rhs, field + 1)
        elif isinstance(l, str) and isinstance(r, int):
            # str precede ints
            return -1
        elif isinstance(l, int) and isinstance(r, str):
            # int follows strs
            return 1

        raise TypeError(
            f"unsupported paths {lhs}, {rhs} (failed matching at index {field})"
        )

    ordered_keys = list(sorted(substitutions.keys(), key=cmp_to_key(key_comparator)))

    return apply_substitutions(d, ordered_keys, substitutions, 0, len(ordered_keys))


def make_user(
    client: TestClient,
    username: str = TEST_USER,
    email: str = TEST_EMAIL,
    password: str = TEST_PASSWD,
) -> str:
    r = client.post(
        "/user",
        json={
            "username": username,
            "email": email,
            "password": password,
        },
    )
    r.raise_for_status()

    r = client.post(
        "/login",
        data={
            "grant_type": "password",
            "username": username,
            "password": password,
        },
    )
    token: str = r.json()["access_token"]

    return token
