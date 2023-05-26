from enum import Enum


class ChecksumAlgorithm(str, Enum):
    MD5 = "md5"
    SHA1 = "sha1"
    SHA256 = "sha256"
    SHA512 = "sha512"

    def __str__(self) -> str:
        return str(self.value)
