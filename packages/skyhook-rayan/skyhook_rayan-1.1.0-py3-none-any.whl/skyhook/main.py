"""
CLI entrypoint for Skyhook file server
"""

import os
from pathlib import Path
from typing import Optional
import socket

import typer
import uvicorn

from skyhook.security import generate_self_signed_cert, parse_auth_string
from skyhook.server import SkyhookServer

app = typer.Typer(
    name="skyhook",
    help="Skyhook - Secure file server with upload capabilities",
    add_completion=False,
)


# -------------------------
# Helpers
# -------------------------

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip


def format_size(size: int) -> str:
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} PB"


# -------------------------
# Main command
# -------------------------

@app.callback(invoke_without_command=True)
def main_command(
    path: Path = typer.Argument(None),
    host: str = typer.Option("127.0.0.1", "--host", "-h"),
    port: int = typer.Option(8000, "--port", "-p"),
    public: bool = typer.Option(True),
    auth: Optional[str] = typer.Option(None, "--auth", "-a"),
    ssl: bool = typer.Option(False, "--ssl"),
    no_upload: bool = typer.Option(False, "--no-upload"),
):
    if path is None:
        path = Path(os.getcwd())

    host = "0.0.0.0" if public else host

    username = None
    password = None

    if auth:
        username, password = parse_auth_string(auth)

    ssl_certfile = None
    ssl_keyfile = None

    if ssl:
        ssl_certfile, ssl_keyfile = generate_self_signed_cert()

    local_ip = get_local_ip()

    print()
    print("Skyhook - Secure zero-config file server")
    print()
    print(f"LOCAL   : http://127.0.0.1:{port}")
    print(f"NETWORK : http://{local_ip}:{port}")
    if ssl:
        print(f"HTTPS   : https://{local_ip}:{port}")
    print("Press CTRL+C to stop")
    print()

    server = SkyhookServer(path, username, password)
    server.templates.env.filters["format_size"] = format_size
    server.app.state.upload_enabled = not no_upload

    try:
        uvicorn.run(
            server.app,
            host=host,
            port=port,
            ssl_certfile=ssl_certfile,
            ssl_keyfile=ssl_keyfile,
            log_level="info",
        )
    finally:
        if ssl_certfile:
            Path(ssl_certfile).unlink(missing_ok=True)
        if ssl_keyfile:
            Path(ssl_keyfile).unlink(missing_ok=True)


# -------------------------
# Version command
# -------------------------

@app.command()
def version():
    typer.echo("Skyhook v1.1.0")


# -------------------------
# Entrypoint
# -------------------------

def main():
    app(prog_name="skyhook")


if __name__ == "__main__":
    main()
