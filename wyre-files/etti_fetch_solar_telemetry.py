#!/usr/bin/env python3
"""Fetch solar/inverter telemetry for Mr Durosinmi Etti (client_id=4).

This script is intentionally schema-agnostic:
- Finds candidate tables by name (telemetry/inverter/solar/pv/battery/mppt)
- Filters rows to client_id=4 either directly (client_id column) or via
  JOIN to main_device/main_branch on device_id
- Prints: row count, period (min/max timestamp) and a few sample rows

Read-only: does not modify the database.
"""

from __future__ import annotations

import os
from typing import List, Optional, Sequence, Tuple

import psycopg2
from psycopg2 import sql


CLIENT_ID = 4
NAME_PATTERNS = ["telemetry", "inverter", "solar", "pv", "mppt", "battery"]
COL_PATTERNS = [
    # telemetry-like column-name fragments (used for discovery)
    "pv_",
    "solar",
    "inverter",
    "mppt",
    "battery",
    "soc",
    "grid_",
    "load_",
]
TS_CANDIDATES = [
    "post_datetime",
    "timestamp",
    "ts",
    "datetime",
    "created_at",
    "date_created",
]

SERIAL_COL_CANDIDATES = [
    "device_serial",
    "device_sn",
    "serial",
    "sn",
    "inverter_serial",
    "inverter_sn",
    "logger_serial",
    "logger_sn",
]


def read_credentials() -> dict:
    cred_path = os.path.join("wyre-files", ".credentials")
    creds = {}
    with open(cred_path) as f:
        for line in f:
            line = line.strip()
            if not line or "=" not in line:
                continue
            k, v = line.split("=", 1)
            creds[k.strip()] = v.strip()
    return creds


def pick_ts(cols: Sequence[str]) -> Optional[str]:
    for c in TS_CANDIDATES:
        if c in cols:
            return c
    return None


def get_columns(cur, schema: str, table: str) -> List[str]:
    cur.execute(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema=%s AND table_name=%s
        ORDER BY ordinal_position
        """,
        (schema, table),
    )
    return [r[0] for r in cur.fetchall()]


def table_has_any_rows(cur, schema: str, table: str) -> bool:
    try:
        q = sql.SQL("SELECT 1 FROM {}.{} LIMIT 1").format(sql.Identifier(schema), sql.Identifier(table))
        cur.execute(q)
        return cur.fetchone() is not None
    except Exception:
        return False


def pick_serial_col(cols: Sequence[str]) -> Optional[str]:
    for c in SERIAL_COL_CANDIDATES:
        if c in cols:
            return c
    return None


def pick_filter_mode(cur, schema: str, table: str, cols: Sequence[str]) -> Tuple[str, str]:
    """Pick a filtering strategy that yields at least one row for the client.

    Returns (mode, detail) where mode is one of:
    - client_id
    - branch_id
    - device_id
    - serial   (detail is the serial column name)
    - none
    """

    if "client_id" in cols:
        try:
            q = sql.SQL("SELECT 1 FROM {}.{} WHERE client_id=%s LIMIT 1").format(
                sql.Identifier(schema), sql.Identifier(table)
            )
            cur.execute(q, (CLIENT_ID,))
            if cur.fetchone() is not None:
                return "client_id", "client_id"
        except Exception:
            pass

    if "branch_id" in cols:
        try:
            q = sql.SQL(
                """
                SELECT 1
                FROM {schema}.{table} t
                JOIN main_branch b ON b.id=t.branch_id
                WHERE b.client_id=%s
                LIMIT 1
                """
            ).format(schema=sql.Identifier(schema), table=sql.Identifier(table))
            cur.execute(q, (CLIENT_ID,))
            if cur.fetchone() is not None:
                return "branch_id", "branch_id"
        except Exception:
            pass

    if "device_id" in cols:
        try:
            q = sql.SQL(
                """
                SELECT 1
                FROM {schema}.{table} t
                JOIN main_device d ON d.id=t.device_id
                LEFT JOIN main_branch b ON b.id=d.branch_id
                WHERE COALESCE(b.client_id, d.client_id)=%s
                LIMIT 1
                """
            ).format(schema=sql.Identifier(schema), table=sql.Identifier(table))
            cur.execute(q, (CLIENT_ID,))
            if cur.fetchone() is not None:
                return "device_id", "device_id"
        except Exception:
            pass

    serial_col = pick_serial_col(cols)
    if serial_col:
        try:
            q = sql.SQL(
                """
                SELECT 1
                FROM {schema}.{table} t
                JOIN main_device d ON d.device_id = t.{serial_col}
                LEFT JOIN main_branch b ON b.id=d.branch_id
                WHERE COALESCE(b.client_id, d.client_id)=%s
                LIMIT 1
                """
            ).format(
                schema=sql.Identifier(schema),
                table=sql.Identifier(table),
                serial_col=sql.Identifier(serial_col),
            )
            cur.execute(q, (CLIENT_ID,))
            if cur.fetchone() is not None:
                return "serial", serial_col
        except Exception:
            pass

    return "none", ""


def safe_period(
    cur,
    schema: str,
    table: str,
    cols: Sequence[str],
    mode: str,
    mode_detail: str,
) -> Optional[Tuple[object, object]]:
    ts = pick_ts(cols)
    if not ts:
        return None
    try:
        if mode == "client_id":
            q = sql.SQL("SELECT MIN({ts}), MAX({ts}) FROM {schema}.{table} WHERE client_id=%s").format(
                ts=sql.Identifier(ts), schema=sql.Identifier(schema), table=sql.Identifier(table)
            )
            cur.execute(q, (CLIENT_ID,))
        elif mode == "branch_id":
            q = sql.SQL(
                """
                SELECT MIN(t.{ts}), MAX(t.{ts})
                FROM {schema}.{table} t
                JOIN main_branch b ON b.id=t.branch_id
                WHERE b.client_id=%s
                """
            ).format(ts=sql.Identifier(ts), schema=sql.Identifier(schema), table=sql.Identifier(table))
            cur.execute(q, (CLIENT_ID,))
        elif mode == "device_id":
            q = sql.SQL(
                """
                SELECT MIN(t.{ts}), MAX(t.{ts})
                FROM {schema}.{table} t
                JOIN main_device d ON d.id = t.device_id
                LEFT JOIN main_branch b ON b.id = d.branch_id
                WHERE COALESCE(b.client_id, d.client_id) = %s
                """
            ).format(ts=sql.Identifier(ts), schema=sql.Identifier(schema), table=sql.Identifier(table))
            cur.execute(q, (CLIENT_ID,))
        elif mode == "serial":
            q = sql.SQL(
                """
                SELECT MIN(t.{ts}), MAX(t.{ts})
                FROM {schema}.{table} t
                JOIN main_device d ON d.device_id = t.{serial_col}
                LEFT JOIN main_branch b ON b.id = d.branch_id
                WHERE COALESCE(b.client_id, d.client_id) = %s
                """
            ).format(
                ts=sql.Identifier(ts),
                schema=sql.Identifier(schema),
                table=sql.Identifier(table),
                serial_col=sql.Identifier(mode_detail),
            )
            cur.execute(q, (CLIENT_ID,))
        else:
            return None
        return cur.fetchone()
    except Exception:
        return None


def sample(
    cur,
    schema: str,
    table: str,
    cols: Sequence[str],
    mode: str,
    mode_detail: str,
) -> Tuple[List[str], List[tuple]]:
    ts = pick_ts(cols)
    prefer = [
        "client_id",
        "device_id",
        "inverter_id",
        "serial",
        ts,
        "pv_power",
        "pv_kw",
        "pv_w",
        "ac_power",
        "load_power",
        "grid_power",
        "battery_soc",
        "soc",
        "battery_power",
        "battery_kw",
        "battery_kwh",
        "frequency",
        "voltage",
    ]
    picked: List[str] = []
    for c in prefer:
        if c and c in cols and c not in picked:
            picked.append(c)
        if len(picked) >= 10:
            break
    if not picked:
        picked = list(cols[:8])

    if mode == "client_id":
        q = sql.SQL("SELECT {fields} FROM {schema}.{table} WHERE client_id=%s {order} LIMIT 5").format(
            fields=sql.SQL(", ").join(sql.Identifier(c) for c in picked),
            schema=sql.Identifier(schema),
            table=sql.Identifier(table),
            order=sql.SQL("ORDER BY {} DESC NULLS LAST").format(sql.Identifier(ts)) if ts else sql.SQL(""),
        )
        cur.execute(q, (CLIENT_ID,))
        return picked, cur.fetchall()

    if mode == "branch_id":
        q = sql.SQL(
            """
            SELECT {fields}
            FROM {schema}.{table} t
            JOIN main_branch b ON b.id=t.branch_id
            WHERE b.client_id=%s
            {order}
            LIMIT 5
            """
        ).format(
            fields=sql.SQL(", ").join(sql.SQL("t.") + sql.Identifier(c) for c in picked),
            schema=sql.Identifier(schema),
            table=sql.Identifier(table),
            order=sql.SQL("ORDER BY t.{} DESC NULLS LAST").format(sql.Identifier(ts)) if ts else sql.SQL(""),
        )
        cur.execute(q, (CLIENT_ID,))
        return picked, cur.fetchall()

    if mode == "device_id":
        q = sql.SQL(
            """
            SELECT {fields}
            FROM {schema}.{table} t
            JOIN main_device d ON d.id=t.device_id
            LEFT JOIN main_branch b ON b.id = d.branch_id
            WHERE COALESCE(b.client_id, d.client_id) = %s
            {order}
            LIMIT 5
            """
        ).format(
            fields=sql.SQL(", ").join(sql.SQL("t.") + sql.Identifier(c) for c in picked),
            schema=sql.Identifier(schema),
            table=sql.Identifier(table),
            order=sql.SQL("ORDER BY t.{} DESC NULLS LAST").format(sql.Identifier(ts)) if ts else sql.SQL(""),
        )
        cur.execute(q, (CLIENT_ID,))
        return picked, cur.fetchall()

    if mode == "serial":
        q = sql.SQL(
            """
            SELECT {fields}
            FROM {schema}.{table} t
            JOIN main_device d ON d.device_id = t.{serial_col}
            LEFT JOIN main_branch b ON b.id = d.branch_id
            WHERE COALESCE(b.client_id, d.client_id) = %s
            {order}
            LIMIT 5
            """
        ).format(
            fields=sql.SQL(", ").join(sql.SQL("t.") + sql.Identifier(c) for c in picked),
            schema=sql.Identifier(schema),
            table=sql.Identifier(table),
            serial_col=sql.Identifier(mode_detail),
            order=sql.SQL("ORDER BY t.{} DESC NULLS LAST").format(sql.Identifier(ts)) if ts else sql.SQL(""),
        )
        cur.execute(q, (CLIENT_ID,))
        return picked, cur.fetchall()

    return picked, []


def main() -> None:
    creds = read_credentials()
    conn = psycopg2.connect(
        host=creds["host"],
        database="wyre_db",
        user=creds["user"],
        password=creds["password"],
        port=creds.get("port", "5432"),
    )
    cur = conn.cursor()

    # Helpful: show device candidates (inverter/solar/pv/battery) for this client
    try:
        cur.execute(
            """
            SELECT d.id, d.name, d.device_id, d.fuel_type, d.is_active
            FROM main_device d
            LEFT JOIN main_branch b ON b.id=d.branch_id
            WHERE COALESCE(b.client_id, d.client_id) = %s
            ORDER BY d.is_active DESC, d.id
            """,
            (CLIENT_ID,),
        )
        devs = cur.fetchall()
        print("Devices for client_id=4 matching inverter/solar/pv/battery:")
        for did, name, serial, fuel, active in devs:
            nm = (name or "").lower()
            if any(p in nm for p in ["inverter", "solar", "pv", "mppt", "battery"]):
                print(
                    f" - device_id={did} | active={active} | name={name} | serial/device_id={serial} | fuel={fuel}"
                )
        print("")
    except Exception:
        pass

    # candidate tables by name
    likes = [f"%{p}%" for p in NAME_PATTERNS]
    where = sql.SQL(" OR ").join([sql.SQL("lower(table_name) LIKE lower(%s)") for _ in likes])
    cur.execute(
        sql.SQL(
            """
            SELECT table_schema, table_name
            FROM information_schema.tables
            WHERE table_type='BASE TABLE'
              AND table_schema NOT IN ('pg_catalog','information_schema')
              AND ({where})
            ORDER BY table_schema, table_name
            """
        ).format(where=where),
        likes,
    )
    tables_by_name = cur.fetchall()

    # candidate tables by telemetry-like columns
    col_likes = [f"%{p}%" for p in COL_PATTERNS]
    col_where = sql.SQL(" OR ").join([sql.SQL("lower(column_name) LIKE lower(%s)") for _ in col_likes])
    cur.execute(
        sql.SQL(
            """
            SELECT DISTINCT table_schema, table_name
            FROM information_schema.columns
            WHERE table_schema NOT IN ('pg_catalog','information_schema')
              AND ({where})
            ORDER BY table_schema, table_name
            """
        ).format(where=col_where),
        col_likes,
    )
    tables_by_cols = cur.fetchall()

    tables = sorted(set(tables_by_name) | set(tables_by_cols))
    print(f"Found {len(tables)} candidate tables (name={len(tables_by_name)}, columns={len(tables_by_cols)})")

    matched = 0
    for schema, table in tables:
        if not table_has_any_rows(cur, schema, table):
            continue
        cols = get_columns(cur, schema, table)
        mode, detail = pick_filter_mode(cur, schema, table, cols)
        if mode == "none":
            continue
        matched += 1
        ts = pick_ts(cols)
        print(f"\n== {schema}.{table} ==")
        print(f"filter: {mode}{(':'+detail) if detail else ''} | ts: {ts or 'N/A'}")
        period = safe_period(cur, schema, table, cols, mode, detail)
        if period:
            print("period:", period[0], "->", period[1])
        picked, rows = sample(cur, schema, table, cols, mode, detail)
        print("columns(sample):", picked)
        for r in rows:
            print(" ", r)

    if matched == 0:
        print("\nNo candidate telemetry tables contained rows for client_id=4.")

    conn.close()


if __name__ == "__main__":
    main()
