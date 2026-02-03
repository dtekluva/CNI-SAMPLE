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

    # Only GEN and UTILITY devices
    cur.execute(
        f"""
        SELECT
            d.id AS device_pk,
            d.name AS device_name,
            d.device_id AS serial,
            d.branch_id,
            b.name AS branch_name,
            b.address AS branch_address,
            MIN(r.post_datetime AT TIME ZONE %s) AS min_local,
            MAX(r.post_datetime AT TIME ZONE %s) AS max_local,
            COUNT(*) AS samples
        FROM main_device d
        JOIN main_reading r ON r.device_id = d.id
        LEFT JOIN main_branch b ON b.id = d.branch_id
        WHERE d.client_id = %s
          AND (d.name ILIKE 'GEN%%' OR d.name ILIKE 'UTILITY')
        GROUP BY d.id, d.name, d.device_id, d.branch_id, b.name, b.address
        ORDER BY branch_name NULLS LAST, d.name, d.id;
        """,
        (tz, tz, client_id),
    )

    rows = cur.fetchall()
    if not rows:
        print("No GEN/UTILITY devices with readings found.")
        return

    print("\nGEN + UTILITY DEVICES (with period in Africa/Lagos):")
    for (
        device_pk,
        device_name,
        serial,
        branch_id,
        branch_name,
        branch_address,
        mn,
        mx,
        cnt,
    ) in rows:
        print(
            f"- device_id={device_pk} | {device_name} | serial={serial} | "
            f"branch_id={branch_id} ({branch_name}) | {mn} -> {mx} | samples={cnt}"
        )
        if branch_address:
            print(f"    address: {branch_address}")

    conn.close()


if __name__ == "__main__":
    main()

