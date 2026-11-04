import hmac
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

class CSRFMiddleware(BaseHTTPMiddleware):
    SAFE_METHODS = {"GET", "HEAD", "OPTIONS", "TRACE"}

    async def dispatch(self, request: Request, call_next):
        if request.method not in self.SAFE_METHODS and request.cookies.get("pyyt_session"):
            cookie_token = request.cookies.get("pyyt_csrf", "")
            header_token = request.headers.get("x-csrf-token", "")
            if not cookie_token or not header_token or not hmac.compare_digest(cookie_token, header_token):
                return JSONResponse({"detail": "CSRF validation failed."}, status_code=403)
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
        response.headers.setdefault("Content-Security-Policy", "default-src 'self'; img-src 'self' data: https:; style-src 'self' 'unsafe-inline'; script-src 'self'; frame-src https://www.youtube.com https://www.youtube-nocookie.com")
        return response
