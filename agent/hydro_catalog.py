"""Verified source catalog and a deliberately restricted read-only SQL grammar."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
import re

from agent.tools_zetaris import SqlError, validate_uuid

SCHEMAS = {
    "flood_analysis.v_hydro_stations": [
        ("code_station", "string"), ("code_site", "string"),
        ("libelle_station", "string"), ("libelle_site", "string"),
        ("libelle_commune", "string"), ("libelle_departement", "string"),
        ("libelle_cours_eau", "string"), ("en_service", "boolean"),
        ("latitude_station", "double"), ("longitude_station", "double"),
        ("date_ouverture_station", "string"), ("date_fermeture_station", "string"),
        ("influence_locale_station", "bigint"),
        ("commentaire_influence_locale_station", "string"),
        ("commentaire_station", "string"),
    ],
    "flood_analysis.v_hydro_observations": [
        ("code_station", "string"), ("code_site", "string"), ("date_obs", "string"),
        ("grandeur_hydro", "string"), ("valeur_brute", "double"),
        ("valeur_normalisee", "double"), ("unite_normalisee", "string"),
        ("libelle_qualification_obs", "string"), ("libelle_statut", "string"),
    ],
    "flood_analysis.v_hydro_history": [
        ("code_station", "string"), ("code_site", "string"),
        ("date_obs_elab", "string"), ("grandeur_hydro_elab", "string"),
        ("valeur_brute", "double"), ("debit_m3_s", "double"),
        ("libelle_statut", "string"),
    ],
}
SCHEMAS["flood_hydro.meteo_precipitations_raw"] = [
    ("NUM_POSTE", "int"), ("NOM_USUEL", "string"), ("LAT", "double"),
    ("LON", "double"), ("AAAAMMJJ", "int"), ("RR", "double"), ("QRR", "int"),
]
CATALOG_VERSION = "loire-hydro-weather-discovery-2026-10-27-v5"
CATALOG = {
    "version": CATALOG_VERSION,
    "evidence": "docs/validation/reports/0015-hubeau-sql-discovery.md",
    "source": "Hub'Eau hydrometry and owner-supplied Meteo-France CSV exposed through Zetaris",
    "verifiedAt": "2026-10-27",
    "coverageIsHistoricalObservationNotLiveGuarantee": True,
    "views": [
        {"name": name, "columns": [{"name": col, "type": dtype} for col, dtype in schema]}
        for name, schema in SCHEMAS.items()
    ],
    "observedCoverage": {
        "stations": "103 distinct station rows, 68 sites, 75 en_service=true.",
        "observations": (
            "1000 exposed rows: H=381 in m, Q=619 in m3/s; "
            "2026-10-27T17:40:00Z to 18:00:00Z at inspection. "
            "Only 12 H and 10 Q station codes matched the reference. "
            "This may be a partial REST page; do not infer full basin coverage."),
        "history": (
            "1000 QmnJ rows, 3 station codes, bounds 2024-01-01 to 2024-12-31. "
            "No matching reference station code was found; code_site overlap is unverified. "
            "Bounds do not establish daily completeness."),
    },
    "precipitationCoverage": {
        "table": "flood_hydro.meteo_precipitations_raw",
        "department": "44, according to the owner-supplied file scope",
        "verifiedRows": 5490, "verifiedStationCount": 15,
        "firstDay": 20240101, "lastDay": 20241231, "nonnullRR": 5490,
        "provenance": "Owner-supplied meteo_precipitations_44_2024.csv; upstream download URL not recorded.",
        "availability": "Verified SELECT through Zetaris; static CSV, not a live weather API.",
        "limits": "Only 2024 is verified. Do not claim 1950-2024 coverage or per-station completeness.",
    },
    "semantics": {
        "observations": (
            "H uses valeur_normalisee and unite_normalisee=m; "
            "Q uses valeur_normalisee and unite_normalisee=m3/s. "
            "Preserve valeur_brute, timestamps, quality and status. "
            "A negative station height is not necessarily erroneous; its local datum "
            "is not known. A height alone is not a universal flood-risk threshold."),
        "history": "QmnJ discharge is debit_m3_s; retain date_obs_elab and libelle_statut.",
        "quality": "Unqualified/raw data is not validated. Influence code meanings are unverified.",
        "precipitation": "NUM_POSTE is the weather station code; AAAAMMJJ is an integer YYYYMMDD date. "
                         "RR is the raw precipitation value. Units and accumulation-window semantics "
                         "require source documentation confirmation; QRR is an uninterpreted source flag. "
                         "No Python weather analysis is provided. Do not infer geographic/temporal "
                         "compatibility with Givry or recent hydrometry without checking it.",
    },
    "knownStationContexts": [{
        "code_station": "K400001010", "code_site": "K4000010",
        "stationName": "La Loire at Cours-les-Barres - Givry",
        "commune": "COURS-LES-BARRES", "department": "CHER",
        "identifierNote": "Station and site codes are different. Filter code_station for K400001010.",
        "source": "Verified station-reference SQL; descriptive context, not current observations.",
    }],
    "exampleQueries": [
        "SELECT * FROM flood_analysis.v_hydro_observations WHERE code_station = 'K400001010' ORDER BY date_obs DESC LIMIT 50",
        "SELECT * FROM flood_analysis.v_hydro_stations WHERE code_station = 'K400001010' LIMIT 1",
        "SELECT * FROM flood_analysis.v_hydro_history LIMIT 5",
    ],
    "unavailable": ["Historical precipitation 1950-2023 is not present in the verified 2024 CSV."],
    "toolPolicy": (
        "run_sql accepts one restricted SELECT on one listed view. Use exact column names. "
        "Projection: *, columns, or COUNT/MIN/MAX/AVG with optional AS aliases; "
        "do not mix aggregate and ordinary columns. Optional WHERE comparisons or LIKE joined "
        "by AND or OR, ORDER BY columns, LIMIT 1..50, optional OFFSET 0..100000. "
        "If LIMIT is omitted, the backend appends LIMIT 50 after full grammar validation. "
        "No JOIN, GROUP BY, parenthesized predicates, CTE, subquery, or unlisted function, "
        "comments, semicolon, or modification. SQL at most 480 ASCII characters. "
        "Page limits and incomplete sources must be stated."),
    "responsibilities": (
        "The Analyzer supplies this authorized catalog on every inference request. "
        "Nemotron chooses useful reads; the application orchestrator validates and "
        "executes them. Python provides deterministic summaries, not fabricated forecasts. "
        "World Model stores operational references, not these measurement series. "
        "H-MEM is deferred; any future memory must not override current schemas or permissions."),
}

def catalog_digest() -> str:
    return hashlib.sha256(json.dumps(CATALOG, sort_keys=True).encode()).hexdigest()


@dataclass(frozen=True)
class Query:
    view: str
    columns: tuple[str, ...]
    types: tuple[str, ...]
    limit: int
    aggregate: bool


_IDENTIFIER = r"[a-z][a-z0-9_]*"
_ATOM = r"(?:'[A-Za-z0-9 %_:/+.,T-]{0,100}'|-?[0-9]+(?:\.[0-9]+)?|true|false)"
_QUERY = re.compile(
    r"SELECT (?P<select>.+?) FROM (?P<view>flood_analysis\.v_hydro_[a-z]+|flood_hydro\.meteo_precipitations_raw)"
    r"(?: WHERE (?P<where>.+?))?(?: ORDER BY (?P<order>.+?))?"
    r"(?: LIMIT (?P<limit>[0-9]+))?(?: OFFSET (?P<offset>[0-9]+))?", re.I)
_ITEM = re.compile(
    rf"(?:(?P<column>{_IDENTIFIER})|(?P<func>COUNT|MIN|MAX|AVG)"
    rf"\((?P<distinct>DISTINCT )?(?P<arg>\*|{_IDENTIFIER})\))"
    rf"(?: AS (?P<alias>{_IDENTIFIER}))?", re.I)
_PREDICATE = re.compile(
    rf"(?P<column>{_IDENTIFIER}) (?:(?:=|!=|<>|<=|>=|<|>|LIKE) {_ATOM}|IS (?:NOT )?NULL)",
    re.I)


class HydroQueryPolicy:
    """Fail closed on the complete grammar; not a general SQL security parser."""
    max_rows = 50

    @staticmethod
    def _layout(sql: str) -> str:
        if (not isinstance(sql, str) or len(sql.encode("utf-8")) > 480
                or not sql.isascii()
                or any(ord(c) < 32 and c not in "\t\r\n" for c in sql)):
            raise SqlError("SQL_NOT_ALLOWED")
        parts = re.split(r"('[^']*')", sql)
        for index in range(0, len(parts), 2):
            part = re.sub(r"\s+", " ", parts[index])
            parts[index] = re.sub(r"\s*(<=|>=|!=|<>|=|<|>)\s*", r" \1 ", part)
        return "".join(parts).strip()

    def parse(self, sql: str) -> Query:
        sql = self._layout(sql)
        match = _QUERY.fullmatch(sql)
        if match is None:
            raise SqlError("SQL_NOT_ALLOWED")
        view = match["view"].lower()
        if view not in SCHEMAS:
            raise SqlError("SQL_SOURCE_NOT_ALLOWED")
        schema = {column.lower(): dtype for column, dtype in SCHEMAS[view]}
        limit = int(match["limit"] or self.max_rows)
        if match["offset"] is not None and match["limit"] is None:
            raise SqlError("SQL_NOT_ALLOWED")
        if not 1 <= limit <= self.max_rows or int(match["offset"] or 0) > 100000:
            raise SqlError("SQL_ROW_LIMIT_NOT_ALLOWED")
        projection = match["select"]
        columns, types, modes = [], [], []
        if projection == "*":
            columns = [column for column, _ in SCHEMAS[view]]
            types = [dtype for _, dtype in SCHEMAS[view]]
            modes = [False]
        else:
            # Commas cannot occur inside the supported aggregate arguments.
            for part in projection.split(","):
                item = _ITEM.fullmatch(part.strip())
                if item is None:
                    raise SqlError("SQL_NOT_ALLOWED")
                col = (item["column"] or item["arg"]).lower()
                func = (item["func"] or "").upper()
                if col != "*" and col not in schema:
                    raise SqlError("SQL_COLUMN_NOT_ALLOWED")
                if (col == "*" and func != "COUNT") or (item["distinct"] and func != "COUNT"):
                    raise SqlError("SQL_NOT_ALLOWED")
                if func == "AVG" and schema.get(col) not in {"double", "bigint", "int"}:
                    raise SqlError("SQL_NOT_ALLOWED")
                # Preserve deterministic output column names independently of REST metadata.
                columns.append(item["alias"] or (item["column"] if not func else part.strip()))
                types.append("bigint" if func == "COUNT" else
                             "double" if func == "AVG" else schema[col])
                modes.append(bool(func))
        if len(columns) != len(set(columns)) or (any(modes) and not all(modes)):
            raise SqlError("SQL_NOT_ALLOWED")
        where = match["where"]
        if where is not None:
            # Match each whole predicate so quoted AND cannot escape validation.
            pos = 0
            while pos < len(where):
                predicate = _PREDICATE.match(where, pos)
                if predicate is None or predicate["column"].lower() not in schema:
                    raise SqlError("SQL_NOT_ALLOWED")
                pos = predicate.end()
                if pos == len(where):
                    break
                separator = re.match(r" (?:AND|OR) ", where[pos:], re.I)
                if separator is None:
                    raise SqlError("SQL_NOT_ALLOWED")
                pos += separator.end()
                if pos == len(where):
                    raise SqlError("SQL_NOT_ALLOWED")
        if match["order"] is not None:
            if any(modes):
                raise SqlError("SQL_NOT_ALLOWED")
            for part in match["order"].split(","):
                order = re.fullmatch(rf"({_IDENTIFIER})(?: (ASC|DESC))?", part.strip(), re.I)
                if order is None or order[1].lower() not in schema:
                    raise SqlError("SQL_NOT_ALLOWED")
        return Query(view, tuple(columns), tuple(types), limit, any(modes))

    def validate(self, sql: str) -> None:
        self.prepare(sql)

    def prepare(self, sql: str) -> str:
        sql = self._layout(sql)
        self.parse(sql)
        normalized = sql if _QUERY.fullmatch(sql)["limit"] is not None else sql + " LIMIT 50"
        if len(normalized.encode("utf-8")) > 480:
            raise SqlError("SQL_NOT_ALLOWED")
        return normalized

    def result(self, sql: str, rows, *, operation_id: str, source_kind: str) -> dict:
        import uuid
        query = self.parse(sql)
        validate_uuid(operation_id)
        if not isinstance(rows, list) or len(rows) > query.limit:
            raise SqlError("INVALID_ZETARIS_RESPONSE")
        normalized = []
        for row in rows:
            if not isinstance(row, (list, tuple)) or len(row) != len(query.columns):
                raise SqlError("INVALID_ZETARIS_RESPONSE")
            normalized.append([self._value(v, t) for v, t in zip(row, query.types)])
        return {"columns": list(query.columns), "rows": normalized,
                "rowCount": len(normalized),
                # Reaching LIMIT means completeness cannot be confirmed.
                "truncated": len(normalized) == query.limit,
                "sourceKind": source_kind, "operationId": operation_id,
                "evidenceId": str(uuid.uuid4())}

    @staticmethod
    def _value(value, dtype):
        if value is None:
            return None
        if dtype == "string":
            if not isinstance(value, str) or len(value.encode("utf-8")) > 2048:
                raise SqlError("INVALID_ZETARIS_RESPONSE")
            return value
        if dtype == "boolean":
            if type(value) is bool:
                return value
            if isinstance(value, str) and value.lower() in {"true", "false"}:
                return value.lower() == "true"
            raise SqlError("INVALID_ZETARIS_RESPONSE")
        if isinstance(value, bool) or not isinstance(value, (str, int, float)):
            raise SqlError("INVALID_ZETARIS_RESPONSE")
        try:
            number = float(value)
            if not math.isfinite(number) or (dtype in {"bigint", "int"} and not number.is_integer()):
                raise ValueError
        except (ValueError, OverflowError):
            raise SqlError("INVALID_ZETARIS_RESPONSE") from None
        return int(number) if dtype in {"bigint", "int"} else number

    def validate_result(self, result, *, sql: str, operation_id: str, source_kind: str):
        required = {"columns", "rows", "rowCount", "truncated", "sourceKind",
                    "operationId", "evidenceId"}
        if not isinstance(result, dict) or set(result) != required:
            raise SqlError("INVALID_SQL_RESULT")
        try:
            expected = self.result(sql, result["rows"], operation_id=operation_id,
                                   source_kind=source_kind)
            validate_uuid(result["evidenceId"])
            if (result["columns"] != expected["columns"]
                    or type(result["rowCount"]) is not int
                    or result["rowCount"] != expected["rowCount"]
                    or type(result["truncated"]) is not bool
                    or result["truncated"] != expected["truncated"]
                    or result["sourceKind"] != source_kind
                    or result["operationId"] != operation_id):
                raise ValueError
            # Enforce normalized types, not equality alone (True equals 1).
            for actual, normalized in zip(result["rows"], expected["rows"]):
                for left, right in zip(actual, normalized):
                    if type(left) is not type(right) or left != right:
                        raise ValueError
        except (SqlError, ValueError, TypeError):
            raise SqlError("INVALID_SQL_RESULT") from None

# History: 2026-10-27: Enforced a backend default row cap for admitted SELECTs and traced proposed versus executed SQL.

# History: 2026-10-27: Accepted validated SQL layout and simple OR predicates, retaining strict sources and bounded execution.

# History: 2026-10-27: Added verified station/site context and bounded textual source discovery for model-selected reads.

# History: 2026-10-27: Exposed the SQL-verified 2024 weather CSV as catalog data without adding Python weather analysis.
