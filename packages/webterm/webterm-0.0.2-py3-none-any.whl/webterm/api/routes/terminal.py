"""Terminal routes."""

from typing import Optional

from fastapi import APIRouter, Cookie, Query, Request, WebSocket, status

from webterm.api.app import templates
from webterm.api.auth import is_auth_enabled, verify_token
from webterm.api.websocket import ws_manager

router = APIRouter(tags=["terminal"])


@router.get("/")
async def index(request: Request):
    """Serve the terminal HTML page.

    Args:
        request: The HTTP request

    Returns:
        Rendered HTML template
    """
    return templates.TemplateResponse("index.html", {"request": request})


@router.websocket("/ws/terminal")
async def websocket_terminal(
    websocket: WebSocket,
    token: Optional[str] = Query(None),
    webterm_auth: Optional[str] = Cookie(None),
):
    """WebSocket endpoint for terminal communication.

    Args:
        websocket: The WebSocket connection
        token: Optional token from query parameter
        webterm_auth: Optional token from cookie
    """
    # Check authentication for WebSocket
    if is_auth_enabled():
        authenticated = False

        # Check query parameter token
        if token and verify_token(token):
            authenticated = True
        # Check cookie token
        elif webterm_auth and verify_token(webterm_auth):
            authenticated = True

        if not authenticated:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

    await ws_manager.handle_connection(websocket)
