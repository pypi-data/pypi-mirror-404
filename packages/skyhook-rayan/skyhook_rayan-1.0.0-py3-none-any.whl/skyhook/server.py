"""FastAPI application for Skyhook file server."""

import mimetypes
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request

from skyhook.security import AuthManager, sanitize_path


def format_size(size: int) -> str:
    """Format file size in human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} PB"


class SkyhookServer:
    """Main Skyhook file server application."""
    
    def __init__(
        self,
        serve_path: Path,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ):
        self.serve_path = serve_path.resolve()
        self.auth_manager = AuthManager(username, password)
        self.app = FastAPI(
            title="Skyhook File Server",
            description="Secure file server with upload capabilities",
            version="1.0.0",
        )
        
        # Set up Jinja2 templates
        template_dir = Path(__file__).parent / "templates"
        self.templates = Jinja2Templates(directory=str(template_dir))
        
        # Register custom filters
        self.templates.env.filters['format_size'] = format_size
        
        # Register routes
        self._register_routes()
    
    def _register_routes(self):
        """Register all application routes."""
        
        @self.app.get("/", response_class=HTMLResponse)
        async def index(
            request: Request,
            path: str = "",
            authorized: bool = Depends(self.auth_manager.verify_credentials),
        ):
            """Serve the main file listing page."""
            return await self.list_directory(request, path)
        
        @self.app.get("/browse/{path:path}", response_class=HTMLResponse)
        async def browse(
            request: Request,
            path: str,
            authorized: bool = Depends(self.auth_manager.verify_credentials),
        ):
            """Browse a specific directory."""
            return await self.list_directory(request, path)
        
        @self.app.get("/download/{path:path}")
        async def download(
            path: str,
            authorized: bool = Depends(self.auth_manager.verify_credentials),
        ):
            """Download a specific file."""
            return await self.download_file(path)
        
        @self.app.post("/upload")
        async def upload(
            files: List[UploadFile] = File(...),
            path: str = "",
            authorized: bool = Depends(self.auth_manager.verify_credentials),
        ):
            """Upload one or more files."""
            return await self.upload_files(files, path)
        
        @self.app.get("/health")
        async def health():
            """Health check endpoint."""
            return {"status": "healthy", "version": "1.0.0"}
    
    async def list_directory(self, request: Request, path: str = "") -> HTMLResponse:
        """Generate HTML directory listing."""
        try:
            target_path = sanitize_path(self.serve_path, path)
        except HTTPException:
            raise
        
        if not target_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Directory not found"
            )
        
        if not target_path.is_dir():
            # If it's a file, redirect to download
            return await self.download_file(path)
        
        # Get directory contents
        items = []
        try:
            for item in sorted(target_path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
                try:
                    stat = item.stat()
                    items.append({
                        "name": item.name,
                        "is_dir": item.is_dir(),
                        "size": stat.st_size if item.is_file() else 0,
                        "modified": datetime.fromtimestamp(stat.st_mtime),
                        "path": str(item.relative_to(self.serve_path)),
                    })
                except (OSError, PermissionError):
                    # Skip items we can't access
                    continue
        except PermissionError:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied"
            )
        
        # Breadcrumb navigation
        breadcrumbs = []
        if path:
            parts = Path(path).parts
            for i, part in enumerate(parts):
                breadcrumbs.append({
                    "name": part,
                    "path": "/".join(parts[:i+1]),
                })
        
        return self.templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "items": items,
                "current_path": path,
                "breadcrumbs": breadcrumbs,
                "auth_enabled": self.auth_manager.enabled,
                "format_size": format_size
            }
        )
    
    async def download_file(self, path: str) -> FileResponse:
        """Serve a file for download."""
        try:
            file_path = sanitize_path(self.serve_path, path)
        except HTTPException:
            raise
        
        if not file_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        if not file_path.is_file():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Path is not a file"
            )
        
        # Determine MIME type
        mime_type, _ = mimetypes.guess_type(str(file_path))
        if mime_type is None:
            mime_type = "application/octet-stream"
        
        return FileResponse(
            path=file_path,
            media_type=mime_type,
            filename=file_path.name,
        )
    
    async def upload_files(
        self, files: List[UploadFile], path: str = ""
    ) -> dict:
        """Handle file uploads."""
        try:
            target_dir = sanitize_path(self.serve_path, path)
        except HTTPException:
            raise
        
        if not target_dir.exists() or not target_dir.is_dir():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid upload directory"
            )
        
        uploaded_files = []
        errors = []
        
        for file in files:
            try:
                # Sanitize filename
                safe_filename = Path(file.filename).name
                if not safe_filename or safe_filename.startswith('.'):
                    errors.append({
                        "filename": file.filename,
                        "error": "Invalid filename"
                    })
                    continue
                
                file_path = target_dir / safe_filename
                
                # Write file in chunks to handle large files
                with open(file_path, "wb") as f:
                    while chunk := await file.read(1024 * 1024):  # 1MB chunks
                        f.write(chunk)
                
                uploaded_files.append({
                    "filename": safe_filename,
                    "size": file_path.stat().st_size,
                })
            
            except Exception as e:
                errors.append({
                    "filename": file.filename,
                    "error": str(e)
                })
        
        return {
            "uploaded": uploaded_files,
            "errors": errors,
            "success": len(uploaded_files),
            "failed": len(errors),
        }


def create_app(
    serve_path: Path,
    username: Optional[str] = None,
    password: Optional[str] = None,
) -> FastAPI:
    """Create and configure the FastAPI application."""
    server = SkyhookServer(serve_path, username, password)
    return server.app