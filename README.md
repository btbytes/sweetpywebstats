# sweetpywebstats

A web stats gatherer in python written using <https://chat.openai.com>.

The purpose is to run this service (say running on 
<https://mystats.mydomain.com/> collect visitor web stats for websites you control.

You include a reference this server as a "CSS" like this in the pages you want
to track:

	<link href=https://mystats.mydomain.com/hello.css rel=stylesheet>

The request will be logged into a JSON file. Processing that JSON file as a 
separate process to collect user visit stats.

Note: The `hello.css` is just a subterfuge. All requests to the server return an empty CSS.


**The ChatGPT prompt that was used to generate this is:**


> write a python http server that responds to all requests with an empty css file with correct http headers, and saves the request info - time, ip, and user agent into a queue of size 1000, and when the queue gets full, it is written to a timestamped json file under a user specified location from config.toml; the http server should only log requests made to whitelisted  domains; the whitelisted domains are read from a config.toml file. the config.toml is accepted as a command line argument --config, with the default value being config.toml


**The ChatGPT Response in its entirety is below:**

Here's a Python HTTP server that meets your requirements. You'll need to install the 'toml' package to read the TOML configuration file.

Install the 'toml' package:

```bash
pip install toml
```

Create a 'config.toml' file with the following content:

```toml
[server]
port = 8000
request_log_directory = "logs"
whitelisted_domains = ["example.com", "example.org"]

[queue]
size = 1000
```


Create a Python file named 'http_server.py' and copy the following code into it:

```python
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
parser.add_argument('--config', default='config.toml', help='Path to the configuration file')
args = parser.parse_args()

# Read the configuration file
config = toml.load(args.config)

# Server configuration
port = config['server']['port']
request_log_directory = config['server']['request_log_directory']
whitelisted_domains = config['server']['whitelisted_domains']

# Queue configuration
queue_size = config['queue']['size']
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
                "user_agent": self.headers.get('User-Agent')
            }
            request_queue.append(request_info)

            # Check if the queue is full
            if len(request_queue) >= queue_size:
                self.dump_requests_to_file()

            # Respond with an empty CSS file
            self.send_response(200)
            self.send_header('Content-Type', 'text/css')
            self.end_headers()
            self.wfile.write(b'')
        else:
            self.send_error(403)

    def dump_requests_to_file(self):
        global request_queue
        timestamp = int(time.time())
        filename = f"{request_log_directory}/requests_{timestamp}.json"

        with open(filename, 'w') as f:
            json.dump(list(request_queue), f)

        # Clear the request queue
        request_queue.clear()

if __name__ == '__main__':
    handler = CustomHTTPRequestHandler
    httpd = socketserver.TCPServer(("", port), handler)
    print(f"Serving on port {port}")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
```


---

The only change I had to make to `config.toml` was to add `""` to 
`whitelisted_domains`  to go from  
`whitelisted_domains = ["localhost", "127.0.0.1"]` to 
`whitelisted_domains = ["localhost", "127.0.0.1", ""]`, 
so that I can test this locally.
