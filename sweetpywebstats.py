import http.server
import socketserver
import toml
import sys
import argparse
import os
import json
import time
from collections import deque
from urllib.parse import urlparse

# Read command line arguments
parser = argparse.ArgumentParser()
parser.add_argument(
    "--config", default="config.toml", help="Path to the configuration file"
)
args = parser.parse_args()

# Read the configuration file
config = toml.load(args.config)

# Server configuration
port = config["server"]["port"]
request_log_directory = config["server"]["request_log_directory"]
whitelisted_domains = config["server"]["whitelisted_domains"]

# Queue configuration
queue_size = config["queue"]["size"]
request_queue = deque(maxlen=queue_size)

# Make sure the log directory exists
os.makedirs(request_log_directory, exist_ok=True)


class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.respond_with_empty_css()

    def do_HEAD(self):
        self.respond_with_empty_css()

    def respond_with_empty_css(self):
        parsed_url = urlparse(self.path)
        domain = parsed_url.netloc
        if domain in whitelisted_domains:
            # Add request info to the queue
            request_info = {
                "time": time.time(),
                "ip": self.client_address[0],
                "user_agent": self.headers.get("User-Agent"),
            }
            request_queue.append(request_info)

            # Check if the queue is full
            if len(request_queue) >= queue_size:
                self.dump_requests_to_file()

            # Respond with an empty CSS file
            self.send_response(200)
            self.send_header("Content-Type", "text/css")
            self.end_headers()
            self.wfile.write(b"")
        else:
            self.send_error(403)

    def dump_requests_to_file(self):
        global request_queue
        timestamp = int(time.time())
        filename = f"{request_log_directory}/requests_{timestamp}.json"

        with open(filename, "w") as f:
            json.dump(list(request_queue), f)

        # Clear the request queue
        request_queue.clear()


if __name__ == "__main__":
    handler = CustomHTTPRequestHandler
    httpd = socketserver.TCPServer(("", port), handler)
    print(f"Serving on port {port}")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
