from http.server import BaseHTTPRequestHandler, HTTPServer
import cgi
from typing import List, Callable, Optional


class _HTTPHandler(BaseHTTPRequestHandler):
    config_handler: Optional[Callable[[List[str]], None]] = None

    def write_body(self, line: str) -> None:
        self.wfile.write(bytes(line, "utf-8"))

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        # TODO replace GET site with form
        # self.write_body("<html><head><title>https://pythonbasics.org</title></head>")
        # self.write_body(f"<p>Request: {self.path}</p>")
        # self.write_body("<body>")
        # self.write_body("<p>This is an example web server.</p>")
        # self.write_body("</body></html>")

    def do_POST(self):
        # Parse the form data posted
        form = cgi.FieldStorage(
            fp=self.rfile,
            headers={k: str(v) for k, v in self.headers.items()},
            environ={'REQUEST_METHOD': 'POST', 'CONTENT_TYPE': self.headers['Content-Type']}
        )

        # Begin the response
        self.send_response(200)
        self.end_headers()
        self.write_body(f"Client: {self.client_address}\n")
        self.write_body(f"User-agent: {self.headers['user-agent']}\n")
        self.write_body(f"Path: {self.path}\n")
        self.write_body("Form data:\n")

        # Echo back information about what was posted in the form
        for field in form.keys():
            field_item = form[field]
            if field_item.filename:
                # The field contains an uploaded file
                file_data = field_item.file.read()
                file_len = len(file_data)
                del file_data
                self.write_body(f"\tUploaded {field} as \"{field_item.filename}\" ({file_len} bytes)\n")
            else:
                # Regular form value
                self.write_body(f"\t{field}={field_item.value}\n")
        if _HTTPHandler.config_handler is not None:
            config = [f"{field}:{form[field].value}" for field in form.keys() if not form[field].filename]
            _HTTPHandler.config_handler(config)


def start_webserver(config_handler: Callable[[List[str]], None]) -> None:
    _HTTPHandler.config_handler = config_handler
    HTTPServer(('127.0.0.1', 8080), _HTTPHandler).serve_forever()
