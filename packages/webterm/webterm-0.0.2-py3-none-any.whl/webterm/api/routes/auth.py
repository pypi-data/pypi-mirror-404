"""Authentication routes."""

from fastapi import APIRouter, Response
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from webterm.api.auth import AUTH_COOKIE_NAME, get_login_page, is_auth_enabled, verify_token

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    """Login request body."""

    token: str


@router.get("/login")
async def login_page():
    """Serve the login page.

    Returns:
        Login HTML page
    """
    if not is_auth_enabled():
        # Redirect to main page if auth is not enabled
        return Response(status_code=302, headers={"Location": "/"})

    return HTMLResponse(content=get_login_page())


@router.post("/login")
async def login(request: LoginRequest, response: Response):
    """Handle login request.

    Args:
        request: Login request with token
        response: Response object to set cookie

    Returns:
        Success or error response
    """
    if not is_auth_enabled():
        return {"success": True}

    if verify_token(request.token):
        # Set auth cookie (httponly for security, 30 days expiry)
        response.set_cookie(
            key=AUTH_COOKIE_NAME,
            value=request.token,
            httponly=True,
            samesite="strict",
            max_age=30 * 24 * 60 * 60,  # 30 days
        )
        return {"success": True}

    return Response(status_code=401, content='{"error": "Invalid token"}', media_type="application/json")


@router.post("/logout")
async def logout(response: Response):
    """Handle logout request.

    Args:
        response: Response object to clear cookie

    Returns:
        Success response
    """
    response.delete_cookie(key=AUTH_COOKIE_NAME)
    return {"success": True}
