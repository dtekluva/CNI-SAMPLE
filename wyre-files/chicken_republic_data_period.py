import os
from dataclasses import dataclass
from typing import Dict, Iterable, Tuple

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

    client_id = 27  # Chicken Republic
    tz = "Africa/Lagos"

    cur.execute("SELECT id, name FROM account_client WHERE id=%s", (client_id,))
    print("CLIENT:", cur.fetchone())

    cur.execute(
        f"""
        SELECT
            MIN(r.post_datetime AT TIME ZONE %s) AS min_local,
            MAX(r.post_datetime AT TIME ZONE %s) AS max_local,
            COUNT(*) AS samples
        FROM main_device d
        JOIN main_reading r ON r.device_id = d.id
        WHERE d.client_id = %s;
        """,
        (tz, tz, client_id),
    )
    overall_min, overall_max, overall_cnt = cur.fetchone()

    print("OVERALL_PERIOD_LOCAL:", overall_min, "->", overall_max, "| samples=", overall_cnt)

    cur.execute(
        f"""
        SELECT
            d.id,
            d.name,
            MIN(r.post_datetime AT TIME ZONE %s) AS min_local,
            MAX(r.post_datetime AT TIME ZONE %s) AS max_local,
            COUNT(*) AS samples
        FROM main_device d
        JOIN main_reading r ON r.device_id = d.id
        WHERE d.client_id = %s
        GROUP BY d.id, d.name
        ORDER BY min_local;
        """,
        (tz, tz, client_id),
    )

    rows = cur.fetchall()
    print("\nPER_DEVICE_PERIOD_LOCAL:")
    for device_id, device_name, mn, mx, cnt in rows:
        print(f"- {device_id}: {device_name} | {mn} -> {mx} | samples={cnt}")

    conn.close()


if __name__ == "__main__":
    main()

