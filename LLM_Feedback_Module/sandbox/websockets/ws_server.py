import asyncio
import socketserver
import threading
from http.server import SimpleHTTPRequestHandler

import websockets


# WebSocket server
async def websocket_handler(websocket, path):
    try:
        async for message in websocket:
            print(f"Received: {message}")
            await websocket.send(f"Echo: {message}")
    except websockets.exceptions.ConnectionClosed:
        print("WebSocket connection closed")


# HTTP server for static files
class HttpHandler(SimpleHTTPRequestHandler):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory="static", **kwargs)


def run_http_server():
    with socketserver.TCPServer(("", 8000), HttpHandler) as httpd:
        print("Serving HTTP on port 8000")
        httpd.serve_forever()


# Main function to run both servers
async def main():
    # Start HTTP server in a separate thread
    http_thread = threading.Thread(target=run_http_server)
    http_thread.start()

    # Start WebSocket server
    async with websockets.serve(websocket_handler, "localhost", 8765):
        print("WebSocket server started on ws://localhost:8765")
        await asyncio.Future()  # Run forever


if __name__ == "__main__":
    asyncio.run(main())
