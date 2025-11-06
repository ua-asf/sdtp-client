import hashlib
import os
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union

import boto3
import requests


class SDTPClient:
    def __init__(
        self,
        server: str,
        version: str = "v1",
        cert: Union[str, Tuple[str, str]] = ("client.crt", "client.key"),
        s3_client: Optional[boto3.Session] = None,
        s3_bucket: Optional[str] = None,
        local_path: Optional[str] = None,
    ):
        """
        A simple implementation of the SDTP Client based on the openapi spec
        https://gitlab.modaps.eosdis.nasa.gov/infrastructure/transfers/sdtp/-/blob/f45b60a32b0c9f7bae6c1ed724a03960fcce82b5/doc/openapi.yaml
        Does not have any admin endpoints defined,
        and the impersonating the user is not supported in this code.

        :param server: Hostname of the SDTP server (e.g., 'sdtp.example.com')
        :param version: API version (default 'v1')
        :param cert: Path to client certificate and key a tuple (cert, key)
        :param s3_client: Boto3 S3 Client
        :param s3_bucket: Bucket to place data in S3
        :param local_path: Local path to save data, ignored if s3_client is set
        """
        self.base_url = f"https://{server}/sdtp/{version}"
        self.cert = cert
        self.s3_client = s3_client
        self.s3_bucket = s3_bucket
        self.local_path = local_path

    def get_files(
        self,
        max_file: Optional[int] = None,
        start_file_id: Optional[int] = None,
        tags: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        params = {}
        if max_file is not None:
            params["maxfile"] = max_file
        if start_file_id is not None:
            params["startfileid"] = start_file_id
        if tags:
            for key, value in tags.items():
                params[f"tags[{key}]"] = value  # tag encoding

        response = requests.get(
            f"{self.base_url}/files",
            cert=self.cert,
            params=params,
            verify=False,
        )
        response.raise_for_status()
        return response.json()

    def get_file(self, file: dict) -> None:
        with requests.get(
            f"{self.base_url}/files/{file['file_id']}",
            cert=self.cert,
            stream=True,
            verify=False,
        ) as r:
            r.raise_for_status()
            if self._use_s3():
                self._s3_multipart_upload_with_md5_check(r, file)
            else:
                self._local_file_download_with_md5_check(r, file)

    def delete_file(self, file_id: int) -> None:
        response = requests.delete(
            f"{self.base_url}/files/{file_id}",
            cert=self.cert,
            verify=False,
        )
        response.raise_for_status()

    def delete_file_range(self, file_id1: int, file_id2: int) -> None:
        response = requests.delete(
            f"{self.base_url}/files/{file_id1}-{file_id2}",
            cert=self.cert,
            verify=False,
        )
        response.raise_for_status()

    def register(self) -> None:
        response = requests.put(
            f"{self.base_url}/register",
            cert=self.cert,
            verify=False,
        )
        print(response)
        response.raise_for_status()

    def _parse_checksum(self, checksum_string: str) -> str:
        try:
            checksum_type, checksum = checksum_string.split(":")
        except ValueError:
            raise RuntimeError(f"Invalid checksum string: {checksum_string}")
        if checksum_type != "md5":
            raise RuntimeError(f"Invalid checksum type: {checksum_type}")
        return checksum

    def _s3_multipart_upload_with_md5_check(self, response: requests.Response, file: dict) -> None:
        md5 = hashlib.md5()
        parsed_checksum = self._parse_checksum(file["checksum"])
        s3_response = self.s3_client.create_multipart_upload(Bucket=self.s3_bucket, Key=file["name"])
        upload_id = s3_response["UploadId"]
        parts = []
        part_number = 1
        buffer = b""
        chunk_size = 8 * 1024 * 1024

        try:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    buffer += chunk
                    md5.update(chunk)
                    if len(buffer) >= chunk_size:
                        part = self.s3_client.upload_part(
                            Body=buffer,
                            Bucket=self.s3_bucket,
                            Key=file["name"],
                            UploadId=upload_id,
                            PartNumber=part_number,
                        )
                        parts.append(
                            {
                                "PartNumber": part_number,
                                "ETag": part["ETag"],
                            },
                        )
                        print(f"Uploaded part {part_number}, size {len(buffer)}")
                        part_number += 1
                        buffer = b""
            if buffer:
                part = self.s3_client.upload_part(
                    Body=buffer,
                    Bucket=self.s3_bucket,
                    Key=file["name"],
                    UploadId=upload_id,
                    PartNumber=part_number,
                )
                parts.append(
                    {
                        "PartNumber": part_number,
                        "ETag": part["ETag"],
                    },
                )
                print(f"Uploaded Final part {part_number}, size {len(buffer)}")
            computed_checksum = md5.hexdigest()
            if computed_checksum != parsed_checksum:
                raise ValueError(f"Checksum mismatch: {computed_checksum} != {parsed_checksum}")
            print(f"Computed checksum: {computed_checksum} matches {parsed_checksum}")
            self.s3_client.complete_multipart_upload(
                Bucket=self.s3_bucket,
                Key=file["name"],
                UploadId=upload_id,
                MultipartUpload={"Parts": parts},
            )
            print("Multipart upload complete")
        except Exception as e:
            print(f"Error during upload: {e}")
            self.s3_client.abort_multipart_upload(Bucket=self.s3_bucket, Key=file["name"], UploadId=upload_id)
            raise

    def _local_file_download_with_md5_check(self, response: requests.Response, file: dict) -> None:
        local_path = os.environ.get("LOCAL_FILE_PATH")
        if local_path is not None:
            local_file = Path(local_path) / file["name"]
        else:
            local_file = file["name"]
        md5 = hashlib.md5()
        parsed_checksum = self._parse_checksum(file["checksum"])
        with open(local_file, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    md5.update(chunk)
                    f.write(chunk)
            computed_checksum = md5.hexdigest()
            if computed_checksum != parsed_checksum:
                raise ValueError(f"Checksum mismatch: {computed_checksum} != {parsed_checksum}")

    def _use_s3(self) -> bool:
        return self.s3_client is not None and self.s3_bucket is not None
