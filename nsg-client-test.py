from sdtp_client import client
from dotenv import load_dotenv

load_dotenv()

def main():
    server = "nsguap01.sgw.earthdata.nasa.gov"
    nsg_client = client.SDTPClient(server=server, version="v1", cert="client.pem")

    res = nsg_client.get_files()
    for file in res["files"]:
        nsg_client.get_file(file)
    print("All files downloaded")


if __name__ == '__main__':
    main()
