import sys
import urllib.request
import uuid
from urllib.error import URLError

REGISTRATION_SERVER_URL = "http://localhost:8000"
VALIDATION_SERVER_URL = "http://localhost:8001"


def get_unique_client_id():
    return uuid.uuid1().hex


def register_client(client_id):
    reg = urllib.request.Request(
        url=REGISTRATION_SERVER_URL,
        data=client_id.encode("utf-8")
    )
    try:
        client_code = urllib.request.urlopen(reg).read().decode('utf-8')
        return client_code
    except URLError as ex:
        sys.exit(ex.reason)


def client_validation(client_id, client_code):
    reg = urllib.request.Request(
        url=VALIDATION_SERVER_URL,
        data=f"{client_id}:{client_code}".encode("utf-8")
    )
    try:
        urllib.request.urlopen(reg)
    except URLError as ex:
        sys.exit(ex.reason)


def main():
    client_id = get_unique_client_id()
    client_code = register_client(client_id)
    print(f"Client: {client_id}:{client_code}")
    client_validation(client_id, client_code)


if __name__ == "__main__":
    main()
