"""Fetch and parse values from the softliQ HTTP endpoint."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import ipaddress
import logging
import re
from time import monotonic
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

_LOGGER = logging.getLogger(__name__)

POLL_INTERVAL = timedelta(minutes=1)
REQUEST_TIMEOUT = (10, 110)
DATA_MAX_AGE = timedelta(minutes=10)
REQUEST_DATA = "id=625&show=D_A_1_1|D_A_1_2|D_A_2_2|D_A_3_1|D_A_3_2|D_Y_1|D_A_1_3|D_A_2_3|D_Y_5~"

_REQUIRED_FIELDS = ("D_A_1_1", "D_A_1_2", "D_A_3_1", "D_A_3_2", "D_Y_1", "D_A_1_3", "D_Y_5")
_OPTIONAL_FIELDS = ("D_A_2_1", "D_A_2_2", "D_A_2_3")
_NUMBER_PATTERN = re.compile(r"[+-]?(?:\d+(?:[.,]\d*)?|[.,]\d+)")


class RequestFailed(Exception):
    """Raised when the device POST fails in the request worker."""


def _post_request(url: str) -> Any:
    """Perform the blocking POST using the known-working requests behavior."""
    import requests

    try:
        response = requests.post(url, data=REQUEST_DATA, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        return response
    except requests.exceptions.RequestException as err:
        raise RequestFailed(str(err)) from err


def _read_tag(content: str, tag: str) -> str | None:
    """Return the first value in a simple XML-like tag."""
    match = re.search(
        rf"<\s*{re.escape(tag)}\s*>\s*({_NUMBER_PATTERN.pattern})\s*</\s*{re.escape(tag)}\s*>",
        content,
        re.IGNORECASE,
    )
    return match.group(1).replace(",", ".") if match else None


def _parse_response(content: str) -> dict[str, Any]:
    """Parse required and optional numeric fields from a device response."""
    code_match = re.search(r"<\s*code\s*>\s*(\w+)\s*</\s*code\s*>", content, re.IGNORECASE)
    if code_match is None:
        preview = content[:160] + "..." if len(content) > 160 else content
        raise ValueError(
            f"Antwort enthält keinen <code>-Wert. Response Preview: {preview!r}"
        )

    values: dict[str, Any] = {"code": code_match.group(1)}
    missing = []
    for tag in _REQUIRED_FIELDS:
        value = _read_tag(content, tag)
        if value is None:
            missing.append(tag)
        else:
            values[tag] = float(value)

    if missing:
        raise ValueError(f"Antwort enthält nicht alle Pflichtwerte: {', '.join(missing)}")

    for tag in _OPTIONAL_FIELDS:
        value = _read_tag(content, tag)
        values[tag] = float(value) if value is not None else None

    values["D_Y_5"] = int(values["D_Y_5"])
    return values


class GruenbeckDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinate slow device requests and retain the last successful time."""

    def __init__(self, hass: HomeAssistant, host: str) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name="Gruenbeck softliQ",
            update_interval=POLL_INTERVAL,
        )
        address = ipaddress.ip_address(host)
        formatted_host = f"[{address.compressed}]" if address.version == 6 else address.compressed
        self.url = f"http://{formatted_host}/mux_http"
        self.host = address.compressed
        self.last_successful_update: datetime | None = None
        self.last_request_duration: float | None = None

    @property
    def has_fresh_data(self) -> bool:
        """Return whether cached values are still within the allowed stale period."""
        return (
            self.data is not None
            and self.last_successful_update is not None
            and datetime.now(timezone.utc) - self.last_successful_update < DATA_MAX_AGE
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Request device data without blocking Home Assistant's event loop."""
        started_at = monotonic()
        response = None
        http_status = None
        request_content_type = None
        response_content_type = None
        response_content_length = None
        response_text_length = None
        try:
            response = await self.hass.async_add_executor_job(_post_request, self.url)
            http_status = response.status_code
            request_content_type = response.request.headers.get("Content-Type")
            response_content_type = response.headers.get("Content-Type")
            response_content_length = response.headers.get("Content-Length")
            response.raise_for_status()
            content = response.text
            response_text_length = len(content)
            values = _parse_response(content)
        except (RequestFailed, TimeoutError, ValueError) as err:
            self.last_request_duration = monotonic() - started_at
            _LOGGER.warning(
                "POST-Abfrage von %s fehlgeschlagen nach %.2f s "
                "(HTTP %s, Request Content-Type %s, Response Content-Type %s, "
                "Content-Length %s, Textlänge %s): %s",
                self.host,
                self.last_request_duration,
                http_status,
                request_content_type,
                response_content_type,
                response_content_length,
                response_text_length,
                err,
            )
            raise UpdateFailed(f"Abruf von {self.host} fehlgeschlagen: {err}") from err
        finally:
            if response is not None:
                response.close()

        self.last_request_duration = monotonic() - started_at
        self.last_successful_update = datetime.now(timezone.utc)
        return values