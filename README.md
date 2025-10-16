# SDTPClient

A Python client for interacting with NASA's SDTP API (Science Data Transfer Protocol), based on its [OpenAPI specification](https://gitlab.modaps.eosdis.nasa.gov/infrastructure/transfers/sdtp/-/blob/f45b60a32b0c9f7bae6c1ed724a03960fcce82b5/doc/openapi.yaml).

Supports listing, downloading, and deleting files — either to **local storage** or **Amazon S3** — with built-in checksum validation.

---

## Features

- Fetch and filter files from the SDTP API
- Download large files (1–10 GB+)
- Stream to disk **or** S3 using multipart upload
- Automatically verify file integrity with **MD5 checksums**
- Secure client authentication with cert/key
- Admin features and user impersonation not yet supported

---

## Quick Start

### 1. Instantiate the Client

```python
from boto3

from sdtp_client import SDTPClient

client = SDTPClient(
    server="sdtp.example.com",
    cert=("client.crt", "client.key"),
    s3_client = boto3.client("s3"),
    s3_bucket = "some_cool_bucket",
    local_path = "some_path/to_local",
)
```

### 2. Register with the Server

```python
client.register()
```

### 3. List Available Files

```python
files = client.get_files(maxfile=5)
```

### 4. Download a File

```python
file = files["files"][0]
client.get_file(file)
```

---

## S3 Mode (Optional)

To use S3 for file downloads, set `s3_client, and s3_bucket` as parameters to the SDTP Client

## Local Download Mode

Pass the local_path as a parameter to the SDTP Client. If s3_client is set this will be ignored

## File Integrity Check

All downloads are streamed and verified against the **MD5 checksum** provided by the server.

If the computed checksum does not match the expected one, the client will raise an error — and abort the S3 multipart upload if applicable.

---

## Example `.env`

```env
# For S3 mode
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
AWS_DEFAULT_REGION=us-west-2

```

---

## Certificate Authentication

The client uses SSL client certificate authentication. Provide a tuple of:

```python
cert=("client.crt", "client.key")
```

> Note: SSL verification is **disabled** (`verify=False`) to support self-signed certs. For production, consider enabling verification or adding proper CA support.

---


## File Deletion

```python
client.delete_file(fileid=12345)

# Or delete a range of files:
client.delete_file_range(fileid1=1000, fileid2=1050)
```

---

##  Notes

* Only `md5` checksums are supported
* The API version is defaulted to `v1`
* No support yet for SDTP admin or impersonation features
* Errors will raise standard Python exceptions (e.g., `requests.HTTPError`, `ValueError`)

---
