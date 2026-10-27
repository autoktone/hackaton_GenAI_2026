"""Controlled SELECT-one executors; all other SQL is rejected."""
from __future__ import annotations

import json
import math
import os
import uuid
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Callable, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

ALLOWED_SQL = "SELECT 1 AS one"
MAX_RESPONSE_BYTES = 65536


class SqlError(RuntimeError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def sql_http_error_code(status: int) -> str:
    if status in {401, 403}:
        return "ZETARIS_UNAUTHORIZED"
    if status in {408, 500, 502, 503, 504}:
        return "ZETARIS_TRANSIENT_HTTP_ERROR"
    return "ZETARIS_HTTP_ERROR"


class SqlExecutor(Protocol):
    kind: str
    timeout_seconds: float

    def execute(self, sql: str, *, operation_id: str) -> dict: ...


def validate_sql(sql: str) -> None:
    if not isinstance(sql, str) or sql != ALLOWED_SQL:
        raise SqlError("SQL_NOT_ALLOWED")


def validate_uuid(value: str) -> None:
    try:
        if not isinstance(value, str) or str(uuid.UUID(value)) != value:
            raise ValueError
    except (ValueError, AttributeError):
        raise SqlError("INVALID_OPERATION_ID") from None


def validate_result(result: dict, *, operation_id: str, source_kind: str) -> None:
    required = {"columns", "rows", "rowCount", "truncated", "sourceKind",
                "operationId", "evidenceId"}
    if not isinstance(result, dict) or set(result) != required:
        raise SqlError("INVALID_SQL_RESULT")
    if (result["columns"] != ["one"] or result["rows"] != [[1]]
            or type(result["rows"][0][0]) is not int
            or type(result["rowCount"]) is not int or result["rowCount"] != 1
            or result["truncated"] is not False
            or result["sourceKind"] != source_kind
            or result["operationId"] != operation_id):
        raise SqlError("INVALID_SQL_RESULT")
    try:
        validate_uuid(result["evidenceId"])
    except SqlError:
        raise SqlError("INVALID_SQL_RESULT") from None


def _result(operation_id: str, source_kind: str) -> dict:
    return {"columns": ["one"], "rows": [[1]], "rowCount": 1,
            "truncated": False, "sourceKind": source_kind,
            "operationId": operation_id, "evidenceId": str(uuid.uuid4())}


@dataclass(frozen=True)
class ZetarisSettings:
    base_url: str
    org_id: str
    api_key: str = field(repr=False)
    web_url: str | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        try:
            parsed = urlsplit(self.base_url)
            port = parsed.port
        except (TypeError, ValueError):
            raise SqlError("INVALID_ZETARIS_CONFIGURATION") from None
        loopback = parsed.hostname in {"localhost", "127.0.0.1", "::1"}
        if (parsed.scheme not in {"http", "https"} or not parsed.hostname
                or parsed.username is not None or parsed.password is not None
                or parsed.query or parsed.fragment or port == 8889
                or parsed.path.rstrip("/") != "/api/v1.0"
                or (parsed.scheme == "http" and not loopback)
                or not isinstance(self.org_id, str) or not self.org_id.isascii()
                or not self.org_id.isdigit()
                or not isinstance(self.api_key, str) or not self.api_key.strip()
                or any(ord(c) < 32 or ord(c) == 127 for c in self.api_key)):
            raise SqlError("INVALID_ZETARIS_CONFIGURATION")

    @classmethod
    def from_env_file(cls, path: str, *, environ: dict | None = None):
        file_path = Path(path)
        if file_path.name != ".env.local" or not file_path.is_absolute():
            raise SqlError("EXPLICIT_ENV_LOCAL_REQUIRED")
        names = ("ZETARIS_REST_URL", "ZETARIS_ORG_ID", "ZETARIS_API_KEY", "ZETARIS_BASE_URL")
        values = {}
        try:
            text = file_path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            raise SqlError("ZETARIS_CONFIGURATION_UNAVAILABLE") from None
        for line in text.splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            if key.strip() not in names:
                continue
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
                value = value[1:-1]
            values.setdefault(key.strip(), value)
        env = os.environ if environ is None else environ
        for name in names:
            if name in env:
                values[name] = env[name]
        if any(not values.get(name) for name in names[:3]):
            raise SqlError("MISSING_ZETARIS_CONFIGURATION")
        return cls(values[names[0]].rstrip("/"), values[names[1]], values[names[2]],
                   web_url=values.get("ZETARIS_BASE_URL"))


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class ZetarisHttpTransport:
    """Direct REST only, without proxy discovery, redirects or retries."""

    def __init__(self, settings: ZetarisSettings, timeout_seconds: float = 15,
                 *, sql_validator=validate_sql, query_limit: int = 1):
        if (not isinstance(timeout_seconds, (int, float))
                or isinstance(timeout_seconds, bool) or not math.isfinite(timeout_seconds)
                or not 0 < timeout_seconds <= 15):
            raise SqlError("INVALID_SQL_TIMEOUT")
        if type(query_limit) is not int or not 1 <= query_limit <= 50:
            raise SqlError("INVALID_SQL_ROW_LIMIT")
        self._settings = settings
        self._sql_validator = sql_validator
        self.query_limit = query_limit
        self.timeout_seconds = float(timeout_seconds)

    def post_query(self, sql: str, *, operation_id: str, query_id: str | None = None) -> dict:
        self._sql_validator(sql)
        validate_uuid(operation_id)
        query_id = operation_id if query_id is None else query_id
        validate_uuid(query_id)
        body = {"queryId": query_id, "sql": sql, "source": "SqlEditor", "limit": self.query_limit}
        request = Request(
            self._settings.base_url.rstrip("/") + "/sql-editor/sqls/run",
            data=json.dumps(body).encode("utf-8"), method="POST",
            headers={"Authorization": "Bearer " + self._settings.api_key,
                     "X-Org-ID": self._settings.org_id,
                     "X-Request-ID": str(uuid.uuid4()),
                     "Content-Type": "application/json"},
        )
        try:
            opener = build_opener(ProxyHandler({}), _NoRedirect())
            with opener.open(request, timeout=self.timeout_seconds) as response:
                if response.status != 200:
                    raise SqlError(sql_http_error_code(response.status))
                raw = response.read(MAX_RESPONSE_BYTES + 1)
        except HTTPError as error:
            code = sql_http_error_code(error.code)
            error.close()
            raise SqlError(code) from None
        except (URLError, OSError, TimeoutError):
            raise SqlError("ZETARIS_OUTCOME_UNKNOWN") from None
        if len(raw) > MAX_RESPONSE_BYTES:
            raise SqlError("ZETARIS_RESPONSE_TOO_LARGE")
        try:
            parsed = json.loads(raw)
        except (ValueError, UnicodeError):
            raise SqlError("INVALID_ZETARIS_RESPONSE") from None
        if not isinstance(parsed, dict):
            raise SqlError("INVALID_ZETARIS_RESPONSE")
        return parsed


class StubSqlExecutor:
    kind = "standalone_stub"
    timeout_seconds = 0.0

    def execute(self, sql: str, *, operation_id: str) -> dict:
        validate_sql(sql)
        validate_uuid(operation_id)
        return _result(operation_id, self.kind)


class ZetarisSqlExecutor:
    kind = "zetaris_rest"

    def __init__(self, transport):
        self._transport = transport
        self.timeout_seconds = transport.timeout_seconds

    def execute(self, sql: str, *, operation_id: str) -> dict:
        validate_sql(sql)
        validate_uuid(operation_id)
        response = self._transport.post_query(sql, operation_id=operation_id)
        if not isinstance(response, dict):
            raise SqlError("INVALID_ZETARIS_RESPONSE")
        rows = response.get("data")
        if (not isinstance(rows, list) or len(rows) != 1
                or not isinstance(rows[0], list) or len(rows[0]) != 1):
            raise SqlError("INVALID_ZETARIS_RESPONSE")
        value = rows[0][0]
        if isinstance(value, bool) or not isinstance(value, (str, int, float)):
            raise SqlError("INVALID_ZETARIS_RESPONSE")
        try:
            number = Decimal(str(value))
        except InvalidOperation:
            raise SqlError("INVALID_ZETARIS_RESPONSE") from None
        if not number.is_finite() or number != Decimal(1):
            raise SqlError("UNEXPECTED_SELECT_ONE_RESULT")
        return _result(operation_id, self.kind)


# History: 2026-10-27: Replaced the placeholder with shared SELECT-one executors and bounded direct REST handling.

# History: 2026-10-27: Retained an optional web endpoint in selected configuration without changing SQL execution.

# History: 2026-10-27: Added scoped catalog-aware hydro analysis while retaining the SELECT-one baseline and explicit dependency profiles.

# History: 2026-10-27: Added explicit workflow 1.3 read attempts, scoped human escalation and backend-linked generated results.
