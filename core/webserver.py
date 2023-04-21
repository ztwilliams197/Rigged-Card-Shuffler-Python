from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import List, Callable, Optional

_IP, _PORT = '128.46.96.236', 80

with open("form.html", 'r') as _f:
    _form_html = _f.readlines()


class _HTTPHandler(BaseHTTPRequestHandler):
    config_handler: Optional[Callable[[List[str]], None]] = None

    def write_body(self, line: str) -> None:
        self.wfile.write(bytes(line, "utf-8"))

    def do_GET(self):
        if '?' not in self.path:
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.write_body("<html><head><title>\"Rigged\" Card Shuffler -- WebServer Configurator</title></head>")
            self.write_body("<body>")
            for line in _form_html:
                self.write_body(line)
            self.write_body("</body></html>")
        else:
            self.send_response(200)
            self.end_headers()

            # site header
            self.write_body(f"Client: {self.client_address[0]}:{self.client_address[1]}\n")
            self.write_body(f"User-agent: {self.headers['user-agent']}\n")
            self.write_body(f"Path: {self.path}\n")
            self.write_body("\n")

            # compute configs
            configs = [conf.split('=') for conf in self.path.split('?')[1].split('&')]
            config_list = [f"{key}:{value}" for key, value in configs]

            # echo selected settings
            self.write_body("Form data:\n")
            for cfg in config_list:
                self.write_body(f"{cfg}\n")
            self.write_body("\n")

            # echo additional info & start shuffle
            self.write_body("Starting shuffle....\n")

            if _HTTPHandler.config_handler is not None:
                _HTTPHandler.config_handler(config_list)


def start_webserver(config_handler: Callable[[List[str]], None], *, verbose: bool = False) -> None:
    _HTTPHandler.config_handler = config_handler
    if verbose:
        print(f"Starting webserver running @ http://{_IP}:{_PORT}")
    HTTPServer((_IP, _PORT), _HTTPHandler).serve_forever()


if __name__ == '__main__':
    start_webserver(print, verbose=True)
