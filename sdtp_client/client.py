import requests
from typing import Optional, Dict, Any, Tuple, Union
import boto3
import os
import hashlib

class SDTPClient:
    def __init__(
        self,
        server: str,
        version: str = "v1",
        cert: Union[str, Tuple[str, str]] = ("client.crt", "client.key"),
        use_s3: bool = False,
    ):
        """
        A simple implementation of the SDTP Client based on the openapi spec
        https://gitlab.modaps.eosdis.nasa.gov/infrastructure/transfers/sdtp/-/blob/f45b60a32b0c9f7bae6c1ed724a03960fcce82b5/doc/openapi.yaml
        Does not have any admin endpoints defined,
        and the impersonating the user is not supported in this code.

        :param server: Hostname of the SDTP server (e.g., 'sdtp.example.com')
        :param version: API version (default 'v1')
        :param cert: Path to client certificate and key, either a tuple (cert, key) or a single .pem file
        :param use_s3: Boolean indicating to use S3 or just local. If Use s3 ..env needs to be set
        """
        self.base_url = f"https://{server}/sdtp/{version}"
        self.cert = cert
        self.use_s3 = use_s3
        if use_s3:
            required_env_vars = [
                "AWS_ACCESS_KEY_ID",
                "AWS_SECRET_ACCESS_KEY",
                "AWS_DEFAULT_REGION",
                "S3_BUCKET",
            ]
            missing_env_vars = [var for var in required_env_vars if not os.environ.get(var)]
            if missing_env_vars:
                raise EnvironmentError(f"Missing environment variables: {', '.join(missing_env_vars)}")
            self.s3 = boto3.client("s3")
            self.s3_bucket = os.environ.get("S3_BUCKET")

        else:
            self.local_path = os.environ.get("LOCAL_PATH")

    def get_files(
        self,
        maxfile: Optional[int] = None,
        startfileid: Optional[int] = None,
        tags: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        params = {}
        if maxfile is not None:
            params["maxfile"] = maxfile
        if startfileid is not None:
            params["startfileid"] = startfileid
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

    def get_file(self, file: dict):
        with requests.get(
            f"{self.base_url}/files/{file['fileid']}",
            cert=self.cert,
            stream=True,
            verify=False,
        ) as r:
            r.raise_for_status()
            if self.use_s3:
                self.s3.upload_fileobj(r.raw, self.s3_bucket, file["name"])
            else:
                with open(f"{file['name']}", "wb") as f:
                    md5 = hashlib.md5()
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            md5.update(chunk)
                            f.write(chunk)
                    if md5.hexdigest() != file["checksum"].split(":")[1]:
                        raise ValueError(f"File {file['name']} is corrupt")

    def delete_file(self, fileid: int) -> None:
        response = requests.delete(
            f"{self.base_url}/files/{fileid}",
            cert=self.cert,
        )
        response.raise_for_status()

    def delete_file_range(self, fileid1: int, fileid2: int) -> None:
        response = requests.delete(
            f"{self.base_url}/files/{fileid1}-{fileid2}",
            cert=self.cert,
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
