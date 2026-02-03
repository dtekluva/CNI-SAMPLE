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

    device_ids = (192, 195)

    # Inspect schema for hints
    cur.execute(
        """
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_schema='public' AND table_name='main_device'
        ORDER BY ordinal_position
        """
    )
    cols = cur.fetchall()
    hint_cols = [
        (name, typ)
        for name, typ in cols
        if any(k in name.lower() for k in ["branch", "site", "store", "location"])
    ]

    print(f"main_device has {len(cols)} columns")
    if hint_cols:
        print("Potential branch/site/location columns:")
        for name, typ in hint_cols:
            print(f"- {name} ({typ})")
    else:
        print("No obvious branch/site/location columns on main_device")

    # Fetch full rows for the two devices
    cur.execute(
        "SELECT * FROM main_device WHERE id IN %s ORDER BY id",
        (device_ids,),
    )
    rows = cur.fetchall()
    desc = [d.name for d in cur.description]

    print("\nDevices:")
    for r in rows:
        rec = dict(zip(desc, r))
        print(f"\nDEVICE {rec.get('id')} | name={rec.get('name')}")
        # Print most relevant identifiers
        for k in desc:
            lk = k.lower()
            if any(x in lk for x in ["client", "branch", "site", "store", "location", "name", "id"]):
                print(f"  {k}: {rec.get(k)}")

    conn.close()


if __name__ == "__main__":
    main()

