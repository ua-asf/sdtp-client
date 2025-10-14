import os

import pytest
from sdtp_client.client import SDTPClient


@pytest.fixture
def mock_response(test_file_metadata):
    _, content = test_file_metadata

    class FakeResponse:
        def __init__(self, content):
            self.content = content

        def iter_content(self, chunk_size=8192):
            yield self.content

        def raise_for_status(self):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    return FakeResponse(content)


def test_get_files(monkeypatch):
    def mock_get(url, cert, params, verify):
        class MockResponse:
            def json(self):
                return {"files": []}

            def raise_for_status(self):
                pass

        return MockResponse()

    monkeypatch.setattr("requests.get", mock_get)

    client = SDTPClient(server="testserver", use_s3=False)
    result = client.get_files()
    assert isinstance(result, dict)
    assert "files" in result


def test_local_file_download_with_md5_check(
    tmp_path, test_file_metadata, mock_response
):
    file_meta, content = test_file_metadata
    os.chdir(tmp_path)

    client = SDTPClient(server="testserver", use_s3=False)
    client._local_file_download_with_md5_check(mock_response, file_meta)

    file_path = tmp_path / file_meta["name"]
    assert file_path.exists()
    assert file_path.read_bytes() == content
