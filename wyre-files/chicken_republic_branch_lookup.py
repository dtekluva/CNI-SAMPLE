import os
from typing import Dict, List, Tuple

import psycopg2


def read_credentials(path: str) -> Dict[str, str]:
    creds: Dict[str, str] = {}
    with open(path, "r") as f:
        for raw in f:
            line = raw.strip()
            if not line or "=" not in line:
                continue
            k, v = line.split("=", 1)
            creds[k.strip()] = v.strip()
    return creds


def table_columns(cur, table_name: str) -> List[str]:
    cur.execute(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema='public' AND table_name=%s
        ORDER BY ordinal_position
        """,
        (table_name,),
    )
    return [r[0] for r in cur.fetchall()]


def main() -> None:
    creds = read_credentials(os.path.join("wyre-files", ".credentials"))
    conn = psycopg2.connect(
        host=creds["host"],
        database="wyre_db",
        user=creds["user"],
        password=creds["password"],
        port=creds.get("port", "5432"),
    )
    cur = conn.cursor()

    branch_ids = (82, 83)

    # Find candidate tables
    cur.execute(
        """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema='public' AND table_name ILIKE '%branch%'
        ORDER BY table_name
        """
    )
    candidates = [r[0] for r in cur.fetchall()]
    print("Branch-like tables:", candidates)

    # Try to fetch branch info from each candidate
    for t in candidates:
        cols = table_columns(cur, t)
        if "id" not in cols:
            continue

        name_col = None
        for possible in ["name", "branch_name", "title"]:
            if possible in cols:
                name_col = possible
                break

        # Basic select list
        select_cols = ["id"]
        if name_col:
            select_cols.append(name_col)
        # add any useful columns if present
        for extra in ["client_id", "address", "city", "state", "code", "is_active"]:
            if extra in cols and extra not in select_cols:
                select_cols.append(extra)

        try:
            cur.execute(
                f"SELECT {', '.join(select_cols)} FROM {t} WHERE id IN %s ORDER BY id",
                (branch_ids,),
            )
            rows = cur.fetchall()
        except Exception as e:
            # not queryable or permissions etc
            conn.rollback()
            continue

        if rows:
            print(f"\nMatched branches in table: {t}")
            for r in rows:
                print(dict(zip(select_cols, r)))

    conn.close()


if __name__ == "__main__":
    main()

