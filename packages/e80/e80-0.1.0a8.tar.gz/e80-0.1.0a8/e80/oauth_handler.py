import click
import webbrowser
import socket
import threading
import time
from e80.lib.context import E80ContextObject
import requests
import traceback
from e80.lib.user import (
    read_user_config,
    write_user_config,
    UserConfig,
    AuthInfo,
)
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlencode, parse_qs


class OAuthHandler(BaseHTTPRequestHandler):
    platform_host: str
    verbose: bool

    def log_message(self, format, *args):
        # Disable access logging by overriding with empty implementation
        pass

    def _400_response(self, message: str):
        # Send error response
        self.send_response(400)
        self.send_header("Content-type", "text/html")
        self.end_headers()

        response = f"<h1>Invalid Request</h1><p>{message}"
        self.wfile.write(response.encode())
        threading.Thread(target=self.server.shutdown).start()

    def _500_response(self, message: str):
        # Send error response
        self.send_response(500)
        self.send_header("Content-type", "text/html")
        self.end_headers()

        response = f"<h1>Unexpected Error</h1><p>{message}"
        self.wfile.write(response.encode())
        threading.Thread(target=self.server.shutdown).start()

    def _vecho(self, message: str, *args, **kwargs):
        if self.verbose:
            click.echo(message, *args, **kwargs)

    def do_GET(self):
        # Parse the authorization code from the URL
        if "?" not in self.path:
            self._400_response("No query parameters found.")
            return

        query = self.path.split("?")[1]
        params = parse_qs(query)

        if "code" not in params:
            self._400_response("No authorization code received.")
            return

        auth_code = params["code"][0]
        self._vecho(f"Authorization code received: {auth_code}")

        state = params["state"][0]
        response = requests.post(
            f"{self.platform_host}/accounts/login/oauth/token",
            data={
                "code": auth_code,
                "state": state,
                "grant_type": "authorization_code",
            },
        )
        if not response.status_code == 200:
            error_text = response.text
            self._500_response(
                "Error completing login. Please check your terminal and try again."
            )
            click.echo(f"Error fetching token: {error_text}")
            return

        self._vecho(f"Token response: {response.text}")
        self._vecho(f"Token response url: {response.url}")

        token = response.json()["access_token"]

        self._vecho(f"Access token: {token}")

        try:
            user_config = read_user_config()
            if user_config is None:
                user_config = UserConfig(auth_info={})
            user_config.auth_info[self.platform_host] = AuthInfo(auth_token=token)
            write_user_config(user_config)
        except Exception as e:
            self._500_response(
                "Error writing to config file. Please check your terminal"
            )
            click.echo("Got exception writing to config file.", err=True)
            self._vecho(e, err=True)
            self._vecho(traceback.format_exc())
            return

        # Send success response
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

        response = """
        <html>
        <head>
            <script>
                window.onload = function() {
                    setTimeout(function() {
                        window.close();
                    }, 3000);
                }
            </script>
        </head>
        <body style="text-align:center;background:#111214;color:white;font-family:monospace;padding:4rem">
            <p>Authorization Successful!</p>
            <small>(closing window now)</small>
        </body>
        </html>
        """
        self.wfile.write(response.encode())
        threading.Thread(target=self.server.shutdown).start()

        click.echo("Login successful.")


def find_free_port():
    """Find a free port on the system."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        s.listen(1)
        port = s.getsockname()[1]
    return port


def start_oauth_flow(ctx_obj: E80ContextObject):
    """Start the OAuth flow by opening browser and starting temporary web server."""
    # Find a free port
    port = find_free_port()
    redirect_uri = f"http://localhost:{port}"

    if ctx_obj.verbose:
        click.echo(f"Starting temporary web server on {redirect_uri}")

    oauth_url = f"{ctx_obj.platform_host}/accounts/login/oauth"
    params = {"redirect_uri": redirect_uri}
    full_url = f"{oauth_url}?{urlencode(params)}"

    # Start the web server in a separate thread
    # Set platform_host as a class attribute before creating server instance
    OAuthHandler.platform_host = ctx_obj.platform_host
    OAuthHandler.verbose = ctx_obj.verbose

    server = HTTPServer(("localhost", port), OAuthHandler)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()

    # Open the browser
    click.echo("Opening browser...")
    webbrowser.open(full_url)

    # Wait for the server to be shut down (when OAuth completes)
    try:
        while server_thread.is_alive():
            time.sleep(0.1)
    except KeyboardInterrupt:
        click.echo("\nOperation cancelled by user.")
        server.shutdown()
