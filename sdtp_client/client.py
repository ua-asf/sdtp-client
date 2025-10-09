import requests
from typing import Optional, Dict, Any, Tuple, Union


class SDTPClient:
    def __init__(
        self,
        server: str,
        version: str = "v1",
        cert: Union[str, Tuple[str, str]] = ("client.crt", "client.key"),
    ):
        """
        A simple implementation of the SDTP Client based on the openapi spec
        https://gitlab.modaps.eosdis.nasa.gov/infrastructure/transfers/sdtp/-/blob/f45b60a32b0c9f7bae6c1ed724a03960fcce82b5/doc/openapi.yaml
        Does not have any admin endpoints defined,
        and the impersonating the user is not supported in this code.

        :param server: Hostname of the SDTP server (e.g., 'sdtp.example.com')
        :param version: API version (default 'v1')
        :param cert: Path to client certificate and key, either a tuple (cert, key) or a single .pem file
        """
        self.base_url = f"https://{server}/sdtp/{version}"
        self.cert = cert

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

    def get_file(self, fileid: int) -> bytes:
        response = requests.get(
            f"{self.base_url}/files/{fileid}",
            cert=self.cert,
            stream=True,
            verify=False,
        )
        response.raise_for_status()
        return response.content

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
