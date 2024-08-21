import concurrent.futures
import os
import socket
import ssl
import sys

try:
    from config import PORT, SSL
except ImportError:
    sys.path.append(os.path.dirname(__file__))

    from config import PORT, SSL


script_dir = os.path.dirname(os.path.realpath(__file__))
if SSL:
    cafile = os.path.join(script_dir, "../ssl/ssl.pem")
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ssl_context.load_verify_locations(cafile)
HOST = "localhost"


def search_string_ssl(string: str) -> str:
    """Search for a specified string on the server -- with SSL authentication."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        with ssl_context.wrap_socket(sock, server_hostname=HOST) as ssock:
            try:
                ssock.connect((HOST, PORT))
            except socket.error as se:
                print("Connection error:", se)
                ssock.close()
                exit(1)
            except Exception as e:
                print("Error:", e)
                exit(1)
            else:
                ssock.sendall(string.encode())

            return ssock.recv(1024).decode()


def search_string() -> str:
    """Search for a specified string on the server."""
    while True:
        string = input(">>> ")
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                try:
                    s.connect((HOST, PORT))
                except socket.error as se:
                    print("Connection error:", se)
                    s.close()
                    exit(1)
                except Exception as e:
                    print("Error:", e)
                    s.close()
                    exit(1)
                else:
                    s.sendall(string.encode())

                stream = s.recv(10240).decode()
                print(f"... {stream}")
                # for chunk in stream:
                #     print(chunk, end="", flush=True)
        except KeyboardInterrupt:
            print("Exiting...")
            break


def main():
    """Initialise script execution."""
    if SSL:
        search_fn = search_string_ssl
    else:
        search_fn = search_string
    try:
        connections = int(sys.argv[1])
    except (IndexError, ValueError):
        connections = 1000
    strings = ["zelasstring" for _ in range(connections)]
    with concurrent.futures.ThreadPoolExecutor() as e:
        responses = e.map(search_fn, strings)
    print(list(responses))


if __name__ == "__main__":
    try:
        search_string()
    except KeyboardInterrupt:
        print("Exiting...")
        exit(0)
