import boto3
from dotenv import load_dotenv

from sdtp_client.client import SDTPClient

load_dotenv()


def main():
    server = "nsguap01.sgw.earthdata.nasa.gov"
    s3 = boto3.client("s3")

    nsg_client = SDTPClient(
        server=server,
        version="v1",
        cert=("client.crt", "client.key"),
        s3_bucket="test_bucket",
        s3_client=s3,
    )

    res = nsg_client.get_files()
    for file in res["files"]:
        nsg_client.get_file(file)
    print("All files downloaded")


if __name__ == "__main__":
    main()
