"""
This script defines a server that handles concurrent client connections and
responds to queries for a string
"""

import logging
import mmap
import os
import openai
import socket
import ssl
import sys
import threading
from timeit import default_timer as timer
from typing import Literal

try:
    import config
except ImportError:
    sys.path.append(os.path.dirname(__file__))
    import config

FILE_PATH, PORT, REREAD_ON_QUERY, SSL, TEST = (
    config.FILE_PATH,
    config.PORT,
    config.REREAD_ON_QUERY,
    config.SSL,
    config.TEST,
)


logger = logging.getLogger("socket_server")
log_format = "%(levelname)s:%(name)s:%(asctime)s - %(message)s"
logging.basicConfig(level=logging.DEBUG, format=log_format)

cached_lines: set[str] = set()
total_run_time: float = 0
script_dir = os.path.dirname(os.path.realpath(__file__))
certfile = os.path.join(script_dir, "../ssl/ssl.pem")
keyfile = os.path.join(script_dir, "../ssl/private.key")
ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
ssl_context.load_cert_chain(certfile, keyfile)
AIML_API_KEY = os.getenv("AIML_API_KEY")
system_content = "You are a travel agent. Be descriptive and helpful."


def read_file() -> set[str] | list[str] | None:
    """Return all lines from a file with trailing whitespace stripped."""
    global cached_lines
    if (cached_lines) and (not REREAD_ON_QUERY):
        return cached_lines
    try:
        with open(FILE_PATH, "r+b") as f:
            with mmap.mmap(f.fileno(), length=0, access=mmap.ACCESS_READ) as mf:
                lines = mf.read().decode().splitlines()
    except FileNotFoundError:
        logger.exception("Target file missing")
        return None
    else:
        if not REREAD_ON_QUERY:
            cached_lines = set(lines)
            return cached_lines
        return lines


def converse(user_content):
    client = openai.OpenAI(
        api_key=AIML_API_KEY,
        base_url="https://api.aimlapi.com/v1",
    )
    chat_completion = client.chat.completions.create(
        model="meta-llama/Llama-2-70b-chat-hf",
        messages=[
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_content},
        ],
        temperature=0.7,
        max_tokens=512,
    )
    return chat_completion.choices[0].message.content
    # for chunk in stream:
    #     print(chunk.choices[0].text or "", end="", flush=True)
    # print()


def handle_client(socket: socket.socket, address: tuple[str, int]):
    """Respond to an accepted client connection."""
    global total_run_time
    client = f"{address[0]}:{address[1]}"
    start = timer()
    with socket as s:
        try:
            user_content = s.recv(1024).rstrip(b"\x00").decode()
            # lines = read_file()
            # if lines is None:
            #     s.sendall("SERVER ERROR\n".encode())
            # elif user_content in lines:
            #     s.sendall("STRING EXISTS\n".encode())
            # else:
            #     s.sendall("STRING NOT FOUND\n".encode())
            response = converse(user_content)
            if response is not None:
                with open("response.txt", "a") as f:
                    f.write("...\n")
                    f.write(response)
                s.sendall(response.encode())
            else:
                s.sendall("No response".encode())
        except IOError as ie:
            raise IOError("IOError!").with_traceback(ie.__traceback__)
        except Exception as e:
            logger.exception(f"Error when handling {client}: {e}")
    end = timer()
    run_time = end - start
    logger.debug(f'Client {client} (query: "{user_content}") took {run_time * 1000}ms')
    logger.info(f"Connection to {client} closed")
    total_run_time += run_time


def connect(s: socket.socket) -> list[threading.Thread]:
    """Establish connections with clients."""
    threads: list[threading.Thread] = []
    with s:
        while True:
            try:
                client_sock, client_addr = s.accept()
                client = f"{client_addr[0]}:{client_addr[1]}"
                logger.info(f"Accepted connection from {client}")
                thread = threading.Thread(
                    target=handle_client,
                    args=(client_sock, client_addr),
                )
                thread.start()
                threads.append(thread)
            except KeyboardInterrupt:
                logger.info("\nKeyboard interrupt! Disconnecting")
                break
            except Exception as e:
                if e:
                    logger.exception("Unhandled exception :(", e)
                else:
                    logger.exception("Unhandled exception :(")
                raise
            if TEST:
                break
    return threads


def connect_ssl(s: socket.socket, hostname: str) -> list[threading.Thread]:
    """Establish SSL secured connections with clients."""
    threads: list[threading.Thread] = []
    with ssl_context.wrap_socket(s, server_side=True) as ssock:
        while True:
            try:
                try:
                    client_sock, client_addr = ssock.accept()
                except ssl.SSLError as se:
                    logger.error(se)
                    if not TEST:
                        continue
                    raise
                client = f"{client_addr[0]}:{client_addr[1]}"
                logger.info(f"Accepted connection from {client}")
                thread = threading.Thread(
                    target=handle_client,
                    args=(client_sock, client_addr),
                )
                thread.start()
                threads.append(thread)
            except KeyboardInterrupt:
                print("\nKeyboard interrupt! Disconnecting")
                break
            except Exception as e:
                logger.exception(e)
            if TEST:
                break

    return threads


def connections_handler(s: socket.socket, hostname: str) -> int:
    """Call `connect_ssl` or `connect` depending on the value of `SSL`."""
    thread_count = 0
    if SSL:
        threads = connect_ssl(s, hostname)
    else:
        threads = connect(s)
    for thread in threads:
        thread.join()
        thread_count += 1
    return thread_count


def run_server() -> Literal[1, 0]:
    """Create and run a socket server."""
    hostname = "0.0.0.0"
    host = socket.gethostbyname(hostname)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.bind((hostname, PORT))
        except socket.error as se:
            logger.critical(f"Failed to start server: {se}")
            return 1
        logger.info("Server started")
        s.listen(0)
        logger.info(f"Listening on {host}:{PORT}")
        connections = connections_handler(s, hostname)
        logger.debug(f"Handled {connections} connection(s)")
        if connections:
            avg_time = (total_run_time / connections) * 1000
            logger.debug(f"AVG time per request: {avg_time}ms")
        logger.info("Shutting down server...")
        return 0


if __name__ == "__main__":
    code = run_server()
    exit(code)
