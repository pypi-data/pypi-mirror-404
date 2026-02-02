"""FastAPI application factory for webterm."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from webterm.api.auth import check_auth, is_auth_enabled
from webterm.core.session import session_manager
from webterm.logger import get_logger

logger = get_logger("api")

# Paths that don't require authentication
PUBLIC_PATHS = {"/auth/login", "/auth/logout", "/health"}

# Paths for static files and templates
BASE_DIR = Path(__file__).parent.parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

# Jinja2 templates
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager."""
    logger.info("Starting webterm...")
    await session_manager.start_cleanup_task()
    yield
    logger.info("Shutting down webterm...")
    await session_manager.shutdown()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application
    """
    app = FastAPI(
        title="WebTerm",
        description="Web-based terminal",
        version="0.0.1",
        lifespan=lifespan,
    )

    # Auth middleware
    @app.middleware("http")
    async def auth_middleware(request: Request, call_next):
        """Check authentication for protected routes."""
        path = request.url.path

        # Skip auth for public paths and static files
        if path in PUBLIC_PATHS or path.startswith("/static/") or path.startswith("/auth/"):
            return await call_next(request)

        # Check if auth is enabled and user is authenticated
        if is_auth_enabled() and not await check_auth(request):
            # Redirect to login page for browser requests
            if "text/html" in request.headers.get("accept", ""):
                return RedirectResponse(url="/auth/login", status_code=302)
            # Return 401 for API requests
            from fastapi.responses import JSONResponse

            return JSONResponse(status_code=401, content={"detail": "Authentication required"})

        return await call_next(request)

    # Mount static files
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    # Include routers
    from webterm.api.routes import auth, files, health, terminal

    app.include_router(auth.router)
    app.include_router(health.router)
    app.include_router(terminal.router)
    app.include_router(files.router)

    return app
