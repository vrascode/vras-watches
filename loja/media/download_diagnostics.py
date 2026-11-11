"""Distinguish local transport restrictions from actual origin HTTP responses."""
import socket
from urllib.error import HTTPError, URLError


def describe_failure(error, stage="download"):
    cause = error.reason if isinstance(error, URLError) and isinstance(error.reason, BaseException) else error
    status = error.code if isinstance(error, HTTPError) else None
    winerror = getattr(cause, "winerror", None)
    errno = getattr(cause, "errno", None)
    if stage == "processing":
        code = "media_processing_failed"
    elif status is not None:
        code = {401: "source_authentication_required", 403: "source_access_denied",
                404: "source_not_found", 429: "source_rate_limited"}.get(status, "source_http_error")
    elif winerror == 10013 or isinstance(cause, PermissionError):
        code = "environment_network_denied"
    elif isinstance(cause, socket.gaierror):
        code = "dns_resolution_failed"
    elif isinstance(cause, TimeoutError):
        code = "network_timeout"
    else:
        code = "download_failed"
    return {"code": code, "stage": stage, "http_status": status,
            "errno": errno, "winerror": winerror,
            "retryable_without_access_change": code in {"network_timeout", "source_rate_limited"}}
