from sdtp_client.client import SDTPClient
from dotenv import load_dotenv

load_dotenv()

def main():
    server = "nsguap01.sgw.earthdata.nasa.gov"
    nsg_client = SDTPClient(server=server, version="v1", cert=("client.crt", "client.key"))

    res = nsg_client.get_files()
    for file in res["files"]:
        nsg_client.get_file(file)
    print("All files downloaded")


if __name__ == '__main__':
    main()
