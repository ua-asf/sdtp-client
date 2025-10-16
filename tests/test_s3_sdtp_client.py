import boto3
import pytest
from moto import mock_aws

from sdtp_client.client import SDTPClient


@pytest.fixture
def mock_stream_response(test_file_metadata):
    _, content = test_file_metadata

    class FakeResponse:
        def iter_content(self, chunk_size=8192):
            for i in range(0, len(content), chunk_size):
                yield content[i : i + chunk_size]

        def raise_for_status(self):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    return FakeResponse()


@pytest.fixture
def setup_mock_s3(monkeypatch):
    """Set env vars and create the mock S3 bucket."""
    with mock_aws():
        bucket = "mybucket"
        region = "us-east-1"

        monkeypatch.setenv("AWS_ACCESS_KEY_ID", "test")
        monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "test")
        monkeypatch.setenv("AWS_DEFAULT_REGION", region)
        monkeypatch.setenv("S3_BUCKET", bucket)

        s3 = boto3.client("s3", region_name=region)
        s3.create_bucket(Bucket=bucket)

        yield s3, bucket


def test_s3_upload_success(test_file_metadata, mock_stream_response, setup_mock_s3):
    file_meta, content = test_file_metadata
    s3_client, s3_bucket = setup_mock_s3

    client = SDTPClient(server="mockserver", s3_client=s3_client, s3_bucket=s3_bucket)
    client._s3_multipart_upload_with_md5_check(mock_stream_response, file_meta)

    result = s3_client.get_object(Bucket=client.s3_bucket, Key=file_meta["name"])
    body = result["Body"].read()
    assert body == content


def test_s3_upload_checksum_mismatch(test_file_metadata, mock_stream_response, setup_mock_s3):
    file_meta, _ = test_file_metadata
    file_meta["checksum"] = "md5:00000000000000000000000000000000"  # incorrect
    s3_client, s3_bucket = setup_mock_s3
    client = SDTPClient(server="mockserver", s3_client=s3_client, s3_bucket=s3_bucket)

    with pytest.raises(ValueError, match="Checksum mismatch"):
        client._s3_multipart_upload_with_md5_check(mock_stream_response, file_meta)

    response = s3_client.list_objects_v2(Bucket=client.s3_bucket)
    assert "Contents" not in response or not response["Contents"]
