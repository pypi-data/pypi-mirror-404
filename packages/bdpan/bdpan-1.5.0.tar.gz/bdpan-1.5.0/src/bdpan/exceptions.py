class BaiduPanError(Exception):
    """Base exception for bdpan."""


class BaiduPanAuthError(BaiduPanError):
    """Authentication/cookie related errors."""


class BaiduPanHttpError(BaiduPanError):
    def __init__(self, message: str, *, status_code: int | None = None, url: str | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.url = url


class BaiduPanApiError(BaiduPanError):
    def __init__(self, message: str, *, payload: dict | None = None):
        super().__init__(message)
        self.payload = payload or {}
