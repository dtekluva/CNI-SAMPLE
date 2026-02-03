#!/usr/bin/env python3
"""Lookup Ecobank ELF client/branch IDs in wyre_db (read-only).

Prints matching rows from:
- public.main_client (if present)
- public.main_branch (name/address matches)

Usage:
  python3 wyre-files/ecobank_elf_lookup.py
"""

from __future__ import annotations

import os
import psycopg2

PATTERNS = ["%ecobank%", "%elf%", "%eco bank%", "%e l f%"]


def read_credentials(path: str) -> dict:
    d: dict[str, str] = {}
    with open(path) as f:
        for raw in f:
            raw = raw.strip()
            if not raw or raw.startswith("#") or "=" not in raw:
                continue
            k, v = raw.split("=", 1)
            d[k.strip()] = v.strip()
    return d


def main() -> None:
    cred_path = os.path.join("wyre-files", ".credentials")
    creds = read_credentials(cred_path)

    conn = psycopg2.connect(
        host=creds.get("host"),
        port=creds.get("port", "5432"),
        database="wyre_db",
        user=creds.get("user"),
        password=creds.get("password"),
    )
    cur = conn.cursor()

    def table_exists(name: str) -> bool:
        cur.execute(
            """SELECT 1 FROM information_schema.tables
               WHERE table_schema='public' AND table_name=%s""",
            (name,),
        )
        return cur.fetchone() is not None

    # ---- Client table lookup ----
    candidate_tables = [
        "main_client",
        "account_client",
        "client",
        "clients",
        "main_customer",
        "main_customers",
    ]
    client_table = next((t for t in candidate_tables if table_exists(t)), None)
    print("client_table:", client_table)

    if client_table:
        cur.execute(
            """SELECT column_name FROM information_schema.columns
               WHERE table_schema='public' AND table_name=%s""",
            (client_table,),
        )
        cols = [r[0] for r in cur.fetchall()]
        name_col = (
            "name"
            if "name" in cols
            else ("company_name" if "company_name" in cols else ("client_name" if "client_name" in cols else None))
        )
        id_col = "id" if "id" in cols else None
        if id_col and name_col:
            cur.execute(
                f"""SELECT {id_col}, {name_col}
                    FROM public.{client_table}
                    WHERE lower({name_col}) LIKE ANY(%s)
                    ORDER BY {id_col}
                    LIMIT 50""",
                (PATTERNS,),
            )
            rows = cur.fetchall()
            print("\nMatches in client table:")
            for r in rows:
                print(" ", r)
            if not rows:
                print("  (none)")
        else:
            print("Could not infer id/name columns in", client_table, "cols:", cols)
    else:
        cur.execute(
            """SELECT table_name FROM information_schema.tables
               WHERE table_schema='public' AND lower(table_name) LIKE '%client%'
               ORDER BY table_name"""
        )
        print("tables_like_client:", [r[0] for r in cur.fetchall()])

    # ---- Branch lookup ----
    if table_exists("main_branch"):
        cur.execute(
            """SELECT column_name FROM information_schema.columns
               WHERE table_schema='public' AND table_name='main_branch'"""
        )
        bcols = [r[0] for r in cur.fetchall()]
        has_client = "client_id" in bcols
        cur.execute(
            """SELECT id, name, address, city, region_id, utility_tariff, is_active"""
            + (", client_id" if has_client else "")
            + """ FROM public.main_branch
                  WHERE lower(name) LIKE ANY(%s)
                     OR lower(coalesce(address,'')) LIKE ANY(%s)
                  ORDER BY id
                  LIMIT 50""",
            (PATTERNS, PATTERNS),
        )
        brows = cur.fetchall()
        print("\nMatches in branches (by name/address):")
        for r in brows:
            print(" ", r)
        if not brows:
            print("  (none)")

    conn.close()


if __name__ == "__main__":
    main()

