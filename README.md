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
from sdtp_client import SDTPClient

client = SDTPClient(
    server="sdtp.example.com",
    cert=("client.crt", "client.key"),
    use_s3=False  # Set to True to use S3 uploads
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

To use S3 for file downloads, set `use_s3=True` in your client and define the following environment variables:

### Required S3 Environment Variables

```env
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret
AWS_DEFAULT_REGION=us-west-2
S3_BUCKET=your-bucket-name
```

You can set these manually, in your shell, or in a `.env` file (if using `python-dotenv`).

---

## Local Download Mode

In local mode (`use_s3=False`), files are saved to the current working directory.

> Optionally, you can set a `LOCAL_PATH` environment variable

---

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
S3_BUCKET=my-sdtp-bucket

# For local mode (optional)
LOCAL_PATH=/data/downloads
```

---

## Certificate Authentication

The client uses SSL client certificate authentication. Provide a tuple of:

```python
cert=("client.crt", "client.key")
```

> Note: SSL verification is **disabled** (`verify=False`) to support self-signed certs. For production, consider enabling verification or adding proper CA support.

---

## Development & Testing

To install in editable (dev) mode:

```bash
pip install -e ".[dev]"
```

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
