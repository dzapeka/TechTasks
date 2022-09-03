import asyncio
import shelve
import uuid
from http.server import BaseHTTPRequestHandler, HTTPServer

CLIENTS_DB = "clients_db"


def register_client(client_id):
    with shelve.open(CLIENTS_DB) as clients_db:
        client_code = uuid.uuid1().hex
        clients_db[client_id] = client_code
        return client_code


def get_client_code(client_id):
    with shelve.open(CLIENTS_DB) as clients_db:
        return clients_db.get(client_id)


def is_client_registered(client_id):
    with shelve.open(CLIENTS_DB) as clients_db:
        return client_id in clients_db


def log_client_info(client_info):
    client_id, client_code = client_info
    with open("server.log", "a") as log_file:
        log_file.writelines(f"{client_id}:{client_code}\n")


class ClientRegistrationHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers["Content-Length"])
        if not content_length:
            self.send_error(400, "Client ID is not specified")
            return False

        post_data = self.rfile.read(content_length)
        client_id = post_data.decode("utf-8")

        if not (client_code := get_client_code(client_id)):
            client_code = register_client(client_id)

        self.send_response(200)
        self.send_header("Content-Type",
                         "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(client_code.encode("utf-8"))


class ClientValidationHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers["Content-Length"])
        if not content_length:
            self.send_error(
                400,
                "Request body is empty.")
            return False
        post_data = self.rfile.read(content_length)
        try:
            client_id, client_code = post_data.decode("utf-8").split(":")
        except ValueError:
            self.send_error(
                400,
                "Please specify request body in the following format: "
                "client_identifier:client_code")
            return False
        else:
            if not is_client_registered(client_id):
                self.send_error(
                    400,
                    f"Client identifier '{client_id}' is not registered")
                return False

            registered_client_code = get_client_code(client_id)
            if client_code != registered_client_code:
                self.send_error(
                    400,
                    f"Incorrect client code {client_code} for client identifier {client_id}")
                return False
            self.send_response(200)
            self.send_header("Content-Type",
                             "text/plain; charset=utf-8")
            self.end_headers()
            log_client_info((client_id, client_code))


def run_server(address, port, handler_class, server_name=""):
    server_address = (address, port)
    with HTTPServer(server_address, handler_class) as server:
        print(f"Run {server_name} server | {':'.join(map(str, server.server_address))}")
        server.serve_forever()


async def main():
    await asyncio.gather(
        asyncio.to_thread(run_server,
                          address="",
                          port=8000,
                          handler_class=ClientRegistrationHandler,
                          server_name="Client Registration"),
        asyncio.to_thread(run_server,
                          address="",
                          port=8001,
                          handler_class=ClientValidationHandler,
                          server_name="Client Validation")
    )

if __name__ == "__main__":
    asyncio.run(main())
