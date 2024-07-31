import concurrent.futures
import json
import logging
import socket
# import selectors
import threading
from typing import Callable


class SocketServer:

    def __init__(self, host='localhost', port=8765):
        self.host = host
        self.port = port
        self.server_socket = None
        self.clients = []
        self.handlers = {}
        # self.sel = selectors.DefaultSelector()

        logger = logging.getLogger(__file__)
        log_format = "%(levelname)s:%(name)s:%(asctime)s - %(message)s"
        logging.basicConfig(level=logging.DEBUG, format=log_format)

    def start(self):
        try:
            self.server_socket = socket.socket(socket.AF_INET,
                                               socket.SOCK_STREAM)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            logging.info(f"Server listening on {self.host}:{self.port}")

            with concurrent.futures.ThreadPoolExecutor() as executor:
                while True:
                    try:
                        client_socket, addr = self.server_socket.accept()
                        logging.info(f"Accepted connection from {addr}")
                        executor.submit(self.handle_client, client_socket, addr)
                    except KeyboardInterrupt:
                        logging.info("Server stopped by user")
                        break
                    except Exception as e:
                        logging.error(f"Error starting server: {e}")
        except Exception as e:
            logging.error(f"Error starting server: {e}")

    def handle_client(self, client_socket, addr):
        self.clients.append(client_socket)
        try:
            while True:
                data = client_socket.recv(1024).decode('utf-8')
                logging.debug(f"Received data from {addr}: {data}")
                if not data:
                    break
                self.process_message(client_socket, data)
        except socket.error as e:
            logging.error(f"Socket error: {e}")
        except Exception as e:
            logging.error(f"Error handling client: {e}")
        finally:
            self.disconnect_client(client_socket, addr)

    def process_message(self, client_socket, data):
        try:
            message = json.loads(data)
            action = message['action']
            content = message['content']

            if action in self.handlers:
                response = self.handlers[action](content)
                self.send_response(client_socket, action, response)
            else:
                self.send_response(client_socket, 'error', 'Invalid action')
        except json.JSONDecodeError:
            self.send_response(client_socket, 'error', 'Invalid JSON')

    def create_message(self, action, response):
        return json.dumps({'action': action, 'response': response})

    def send_response(self, client_socket, action, response):
        message = self.create_message(action, response)
        client_socket.send(message.encode('utf-8'))

    def register_handler(self, action: str, handler: Callable) -> None:
        if not isinstance(action, str):
            raise ValueError("Action must be a string")
        if not callable(handler):
            raise ValueError("Handler must be a callable")
        self.handlers[action] = handler

    def unregister_handler(self, action):
        if action in self.handlers:
            del self.handlers[action]

    def list_handlers(self):
        return list(self.handlers.keys())

    def broadcast(self, message, clients=None):
        if clients is None:
            clients = self.clients
        for client in clients:
            try:
                client.send(message.encode('utf-8'))
            except Exception as e:
                logging.error(f"Error broadcasting to client: {e}")
                self.clients.remove(client)

    def disconnect_client(self, client_socket, addr):
        self.clients.remove(client_socket)
        client_socket.close()
        logging.info(f"Client {addr} disconnected")


if __name__ == "__main__":
    server = SocketServer()
    try:
        server.start()
    except KeyboardInterrupt:
        print("Exiting...")
        exit(0)
