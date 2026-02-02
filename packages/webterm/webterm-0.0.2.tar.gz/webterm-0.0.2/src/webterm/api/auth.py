"""Authentication for webterm."""

import secrets
from typing import Optional

from fastapi import Cookie, HTTPException, Query, Request, status

from webterm.core.config import settings

# Cookie name for storing the auth token
AUTH_COOKIE_NAME = "webterm_auth"


def is_auth_enabled() -> bool:
    """Check if authentication is enabled."""
    return settings.token is not None and len(settings.token) > 0


def verify_token(token: str) -> bool:
    """Verify if the provided token is valid.

    Args:
        token: Token to verify

    Returns:
        True if valid, False otherwise
    """
    if not is_auth_enabled():
        return True
    return secrets.compare_digest(token, settings.token)


async def check_auth(request: Request) -> bool:
    """Check if the request is authenticated.

    Args:
        request: The incoming request

    Returns:
        True if authenticated, False otherwise
    """
    if not is_auth_enabled():
        return True

    # Check cookie first
    token = request.cookies.get(AUTH_COOKIE_NAME)
    if token and verify_token(token):
        return True

    # Check Authorization header (Bearer token)
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:]
        if verify_token(token):
            return True

    return False


async def require_auth(request: Request) -> None:
    """Dependency that requires authentication.

    Args:
        request: The incoming request

    Raises:
        HTTPException: If not authenticated
    """
    if not await check_auth(request):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )


def check_ws_auth(
    token: Optional[str] = Query(None),
    cookie_token: Optional[str] = Cookie(None, alias=AUTH_COOKIE_NAME),
) -> bool:
    """Check WebSocket authentication via query param or cookie.

    Args:
        token: Token from query parameter
        cookie_token: Token from cookie

    Returns:
        True if authenticated

    Raises:
        HTTPException: If not authenticated
    """
    if not is_auth_enabled():
        return True

    # Check query parameter
    if token and verify_token(token):
        return True

    # Check cookie
    if cookie_token and verify_token(cookie_token):
        return True

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required",
    )


def get_login_page() -> str:
    """Get the login page HTML."""
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WebTerm - Login</title>
    <style>
        :root {
            --ctp-base: #1e1e2e;
            --ctp-mantle: #181825;
            --ctp-surface0: #313244;
            --ctp-surface1: #45475a;
            --ctp-text: #cdd6f4;
            --ctp-subtext0: #a6adc8;
            --ctp-blue: #89b4fa;
            --ctp-red: #f38ba8;
        }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Menlo', 'Monaco', 'Consolas', monospace;
            background-color: var(--ctp-base);
            color: var(--ctp-text);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .login-container {
            background-color: var(--ctp-mantle);
            padding: 32px;
            border-radius: 8px;
            border: 1px solid var(--ctp-surface0);
            width: 100%;
            max-width: 360px;
        }
        h1 {
            font-size: 24px;
            margin-bottom: 8px;
            text-align: center;
        }
        .subtitle {
            color: var(--ctp-subtext0);
            font-size: 12px;
            text-align: center;
            margin-bottom: 24px;
        }
        .form-group {
            margin-bottom: 16px;
        }
        label {
            display: block;
            font-size: 12px;
            color: var(--ctp-subtext0);
            margin-bottom: 6px;
        }
        input[type="password"] {
            width: 100%;
            padding: 10px 12px;
            background-color: var(--ctp-surface0);
            border: 1px solid var(--ctp-surface1);
            border-radius: 4px;
            color: var(--ctp-text);
            font-family: inherit;
            font-size: 14px;
            outline: none;
        }
        input[type="password"]:focus {
            border-color: var(--ctp-blue);
        }
        button {
            width: 100%;
            padding: 10px;
            background-color: var(--ctp-blue);
            color: var(--ctp-base);
            border: none;
            border-radius: 4px;
            font-family: inherit;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: opacity 0.15s;
        }
        button:hover {
            opacity: 0.9;
        }
        .error {
            color: var(--ctp-red);
            font-size: 12px;
            margin-top: 12px;
            text-align: center;
            display: none;
        }
        .error.show {
            display: block;
        }
    </style>
</head>
<body>
    <div class="login-container">
        <h1>WebTerm</h1>
        <p class="subtitle">Enter token to continue</p>
        <form id="login-form">
            <div class="form-group">
                <label for="token">Token</label>
                <input type="password" id="token" name="token" placeholder="Enter your token" autofocus required>
            </div>
            <button type="submit">Login</button>
            <p id="error" class="error">Invalid token</p>
        </form>
    </div>
    <script>
        document.getElementById('login-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            const token = document.getElementById('token').value;
            const errorEl = document.getElementById('error');

            try {
                const response = await fetch('/auth/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ token })
                });

                if (response.ok) {
                    window.location.href = '/';
                } else {
                    errorEl.classList.add('show');
                }
            } catch (err) {
                errorEl.classList.add('show');
            }
        });
    </script>
</body>
</html>"""
