import pandas as pd
import sqlite3
from pathlib import Path


GTFS_DIR = Path("/home/krijn/Desktop/ov_game/gtfs_static")
DATABASE = Path("/home/krijn/Desktop/ov_game/stops/database/ov.db")


TABLES = [
    "stops",
    "routes",
    "trips",
    "stop_times",
    "calendar",
    "calendar_dates",
    "agency"
]


def import_gtfs():

    DATABASE.parent.mkdir(
        exist_ok=True
    )

    conn = sqlite3.connect(DATABASE)

    for table in TABLES:

        file = GTFS_DIR / f"{table}.txt"

        if not file.exists():
            print(f"Niet gevonden: {file.name}")
            continue

        print(f"Laden: {file.name}")

        df = pd.read_csv(
            file,
            dtype=str,
            low_memory=False
        )

        print(f"{len(df):,} records")

        df.to_sql(
            table,
            conn,
            if_exists="replace",
            index=False
        )


    # Indexen maken na import
    print("Indexes maken...")

    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_stop_times_stop_id
        ON stop_times(stop_id)
    """)

    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_stop_times_trip_id
        ON stop_times(trip_id)
    """)

    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_stop_times_stop_departure
        ON stop_times(stop_id, departure_time)
    """)

    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_trips_route_id
        ON trips(route_id)
    """)

    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_trips_trip_id
        ON trips(trip_id)
    """)

    conn.commit()
    conn.close()

    print("GTFS import afgerond")


if __name__ == "__main__":
    import_gtfs()