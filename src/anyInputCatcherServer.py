import http.server
import socketserver
import datetime
import argparse
import logging
import json
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

# Argument parser setup
parser = argparse.ArgumentParser(description='Start a simple HTTP server')
parser.add_argument('-p', '--port', type=int, help='The port to listen on')
args = parser.parse_args()

PORT = args.port if args.port else 7052

class MyHandler(http.server.BaseHTTPRequestHandler):
    UNAUTHORIZED_PATH = "/unauthorized"
    REDIRECT_PATH = "/redirect"
    REDIRECT_URL = "http://example.com"

    def do_GET(self):
        if not self.check_upgrade_header():
            self.send_426_response()
            return

        query_params = self.get_query_params()
        param1 = self.get_query_param(query_params, 'param1')
        if self.get_path() == self.UNAUTHORIZED_PATH:
            self.send_403_response()
        elif self.get_path() == self.REDIRECT_PATH:
            self.send_302_response(self.REDIRECT_URL, {"code": "123"})
        else:
            self.send_200_response({"message": "GET request received", "query": query_params, "param1": param1})

    def do_POST(self):
        if not self.check_upgrade_header():
            self.send_426_response()
            return

        query_params = self.get_query_params()
        param1 = self.get_query_param(query_params, 'param1')
        if self.get_path() == self.UNAUTHORIZED_PATH:
            self.send_403_response()
        elif self.get_path() == self.REDIRECT_PATH:
            self.send_302_response(self.REDIRECT_URL, {"code": "123"})
        else:
            self.send_200_response({"message": "POST request received", "query": query_params, "param1": param1})

    def do_PUT(self):
        if not self.check_upgrade_header():
            self.send_426_response()
            return

        query_params = self.get_query_params()
        param1 = self.get_query_param(query_params, 'param1')
        if self.get_path() == self.UNAUTHORIZED_PATH:
            self.send_403_response()
        elif self.get_path() == self.REDIRECT_PATH:
            self.send_302_response(self.REDIRECT_URL, {"code": "123"})
        else:
            self.send_200_response({"message": "PUT request received", "query": query_params, "param1": param1})

    def do_DELETE(self):
        if not self.check_upgrade_header():
            self.send_426_response()
            return

        query_params = self.get_query_params()
        param1 = self.get_query_param(query_params, 'param1')
        if self.get_path() == self.UNAUTHORIZED_PATH:
            self.send_403_response()
        elif self.get_path() == self.REDIRECT_PATH:
            self.send_302_response(self.REDIRECT_URL, {"code": "123"})
        else:
            self.send_200_response({"message": "DELETE request received", "query": query_params, "param1": param1})

    def do_HEAD(self):
        if not self.check_upgrade_header():
            self.send_426_response()
            return

        query_params = self.get_query_params()
        param1 = self.get_query_param(query_params, 'param1')
        if self.get_path() == self.UNAUTHORIZED_PATH:
            self.send_403_response()
        elif self.get_path() == self.REDIRECT_PATH:
            self.send_302_response(self.REDIRECT_URL, {"code": "123"}, send_body=False)
        else:
            self.send_200_response({"message": "HEAD request received", "query": query_params, "param1": param1}, send_body=False)

    def get_path(self):
        """Helper method to get the path without query parameters."""
        parsed_url = urlparse(self.path)
        return parsed_url.path

    def get_query_params(self):
        """Helper method to get the query parameters as a dictionary."""
        parsed_url = urlparse(self.path)
        return parse_qs(parsed_url.query)

    def get_query_param(self, query_params, param_name):
        """Helper method to get a specific query parameter."""
        return query_params.get(param_name, [None])[0]

    def check_upgrade_header(self):
        """Helper method to check for the 'Upgrade' header."""
        upgrade_header = self.headers.get('Upgrade')
        return upgrade_header == 'websocket'  # Example condition

    def send_403_response(self):
        self.log_request_details()
        self.send_response(403)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"error": "403 Forbidden: Access is denied"}).encode('utf-8'))

    def send_426_response(self):
        self.log_request_details()
        self.send_response(426)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Upgrade', 'websocket')  # Example upgrade required
        self.end_headers()
        self.wfile.write(json.dumps({"error": "426 Upgrade Required: Please upgrade your connection"}).encode('utf-8'))

    def send_302_response(self, location, query_params=None, send_body=True):
        self.log_request_details()
        # Parse the URL and append query parameters if provided
        parsed_url = urlparse(location)
        query = parse_qs(parsed_url.query)
        if query_params:
            query.update(query_params)
        new_query = urlencode(query, doseq=True)
        new_url = urlunparse(parsed_url._replace(query=new_query))
        self.send_response(302)
        self.send_header('Location', new_url)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        if send_body:
            self.wfile.write(json.dumps({"message": "Redirecting..."}).encode('utf-8'))

    def send_200_response(self, message, send_body=True):
        self.log_request_details()
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Custom-Header', 'CustomValue')
        self.end_headers()
        if send_body:
            self.wfile.write(json.dumps(message).encode('utf-8'))

    def log_request_details(self):
        try:
            request_time = datetime.datetime.now()
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length) if content_length > 0 else b''
            logger.info(f"---------------------------------------------------START---------------------------------------------------")
            logger.info(f"###################    Time: {request_time}")
            logger.info(f"###################  Method: {self.command}")
            logger.info(f"###################    Path: {self.path}")
            logger.info(f"################### Headers:\n{self.headers}")
            logger.info(f"###################    Body:\n{post_data.decode('utf-8')}")
            logger.info(f"---------------------------------------------------END---------------------------------------------------")
        except Exception as e:
            logger.error(f"Error logging request details: {e}")

# Use ThreadingTCPServer for handling requests concurrently
with socketserver.ThreadingTCPServer(("", PORT), MyHandler) as httpd:
    logger.info(f"Serving at port {PORT}")
    httpd.serve_forever()
