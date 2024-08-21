import concurrent.futures
import json
import logging
import socket
import sys
from typing import Callable

class SocketServer:

    def __init__(self, host='localhost', port=8765):
        self.host = host
        self.port = port
        self.server_socket = None
        self.clients = []
        self.handlers = {}
        self.executor = concurrent.futures.ThreadPoolExecutor()
        self.running = True

        logger = logging.getLogger(__file__)
        log_format = "%(levelname)s:%(name)s:%(asctime)s - %(message)s"
        logging.basicConfig(level=logging.DEBUG, format=log_format)

    def start(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        self.server_socket.settimeout(1.0)
        logging.info(f"Server listening on {self.host}:{self.port}")

        try:
            while self.running:
                try:
                    client_socket, addr = self.server_socket.accept()
                    logging.info(f"Accepted connection from {addr}")
                    self.executor.submit(self.handle_client, client_socket, addr)
                except socket.timeout:
                    continue
                except Exception as e:
                    logging.error(f"Error in server loop: {e}")
        finally:
            self.stop()

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
        try:
            client_socket.send(message.encode('utf-8'))
        except socket.error as e:
            logging.error(f"Error sending response to client: {e}")

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

    def stop(self):
        self.running = False
        if self.server_socket:
            self.server_socket.close()
        self.executor.shutdown(wait=True)
        logging.info("Server stopped")

if __name__ == "__main__":
    server = SocketServer()
    try:
        server.start()
    except KeyboardInterrupt:
        logging.info("Exiting due to keyboard interrupt")
        server.stop()
        sys.exit(0)
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        server.stop()
        sys.exit(1)
