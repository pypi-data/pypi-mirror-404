"""CLI entrypoint for Skyhook file server."""

import sys
from pathlib import Path
from typing import Optional

import typer
import uvicorn

from skyhook.security import generate_self_signed_cert, parse_auth_string


app = typer.Typer(
    name="skyhook",
    help="🚀 Skyhook - Secure file server with upload capabilities",
    add_completion=False,
)


def format_size(size: int) -> str:
    """Format file size in human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} PB"


@app.command()
def serve(
    path: Path = typer.Argument(
        Path("."),
        help="Directory to serve",
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
    port: int = typer.Option(
        8000,
        "--port", "-p",
        help="Port to bind to",
        min=1,
        max=65535,
    ),
    host: str = typer.Option(
        "localhost",
        "--host", "-h",
        help="Host interface to bind to",
    ),
    auth: Optional[str] = typer.Option(
        None,
        "--auth", "-a",
        help="Enable authentication (format: username:password)",
    ),
    ssl: bool = typer.Option(
        False,
        "--ssl",
        help="Enable HTTPS with self-signed certificate",
    ),
    reload: bool = typer.Option(
        False,
        "--reload",
        help="Enable auto-reload for development",
    ),
):
    """
    Start the Skyhook file server.
    
    Examples:
    
        # Serve current directory on default port 8000
        $ skyhook
        
        # Serve specific directory with authentication
        $ skyhook /path/to/files --auth admin:password
        
        # Enable HTTPS with custom port
        $ skyhook --ssl --port 8443
        
        # Full configuration
        $ skyhook /data --port 8080 --auth user:pass --ssl
    """
    # Parse authentication if provided
    username = None
    password = None
    if auth:
        try:
            username, password = parse_auth_string(auth)
        except ValueError as e:
            typer.echo(f"❌ Error: {e}", err=True)
            raise typer.Exit(1)
    
    # Generate SSL certificate if requested
    ssl_certfile = None
    ssl_keyfile = None
    if ssl:
        typer.echo("🔐 Generating self-signed SSL certificate...")
        ssl_certfile, ssl_keyfile = generate_self_signed_cert()
        typer.echo("✅ SSL certificate generated")
    
    # Display startup information
    protocol = "https" if ssl else "http"
    typer.echo("")
    typer.echo("🚀 Starting Skyhook File Server")
    typer.echo("─" * 50)
    typer.echo(f"📁 Serving: {path.absolute()}")
    typer.echo(f"🌐 URL: {protocol}://{host}:{port}")
    if username:
        typer.echo(f"🔒 Auth: Enabled (user: {username})")
    else:
        typer.echo("🔓 Auth: Disabled (public access)")
    if ssl:
        typer.echo("🔐 SSL: Enabled (self-signed certificate)")
        typer.echo("⚠️  Warning: Your browser will show a security warning for self-signed certs")
    typer.echo("─" * 50)
    typer.echo("💡 Press Ctrl+C to stop the server")
    typer.echo("")
    
    # Create the server instance to set up Jinja2 filters
    from skyhook.server import SkyhookServer
    server_instance = SkyhookServer(path, username, password)
    server_instance.templates.env.filters['format_size'] = format_size
    
    # Use the app from the server instance
    fastapi_app = server_instance.app
    
    # Run server
    try:
        uvicorn.run(
            fastapi_app,
            host=host,
            port=port,
            ssl_certfile=ssl_certfile,
            ssl_keyfile=ssl_keyfile,
            reload=reload,
            log_level="info",
        )
    except KeyboardInterrupt:
        typer.echo("\n👋 Shutting down Skyhook...")
        raise typer.Exit(0)
    finally:
        # Clean up SSL files if they were created
        if ssl_certfile:
            Path(ssl_certfile).unlink(missing_ok=True)
        if ssl_keyfile:
            Path(ssl_keyfile).unlink(missing_ok=True)


@app.command()
def version():
    """Show Skyhook version."""
    typer.echo("Skyhook v1.0.0")


if __name__ == "__main__":
    app()