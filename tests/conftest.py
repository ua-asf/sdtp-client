import hashlib

import pytest


@pytest.fixture
def test_file_metadata():
    content = b"hello world" * 100_000
    checksum = hashlib.md5(content).hexdigest()
    return {
        "fileid": 1,
        "name": "testfile.txt",
        "checksum": f"md5:{checksum}",
    }, content
