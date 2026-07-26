"""
Live vertrektijden van 1 halte opslaan -- voorbeeld: Arnhem Zuid.

Aanpak:
1. Zoek in de statische GTFS (stops.txt) de stop_id('s) die bij de halte horen.
2. Zoek in stop_times.txt welke ritten daar normaal langskomen (geplande tijd).
3. Poll de live feed (tripUpdates.pb) en bepaal per rit de actuele vertraging.
4. Log elke poll-ronde (geplande + voorspelde vertrektijd) naar een CSV-bestand.

Vereist een lokale kopie van de statische GTFS (zie gtfs_static.py) in ./gtfs_nl_static/
    stops.txt, stop_times.txt, trips.txt, routes.txt

Installeren:
    pip install requests pandas gtfs-realtime-bindings
"""

import csv
import time
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import requests
from google.transit import gtfs_realtime_pb2

GTFS_DIR = Path("gtfs_static")
TRIP_UPDATES_URL = "http://gtfs.ovapi.nl/nl/tripUpdates.pb"
STOP_NAME_QUERY = "Arnhem Zuid"          # pas aan voor een andere halte
OUTPUT_CSV = Path("arnhem_zuid_vertrektijden.csv")
POLL_INTERVAL_SECONDS = 60


def parse_gtfs_time(time_str: str, service_date: datetime) -> datetime:
    """Zet een GTFS-tijd ('25:03:00' kan voorkomen na middernacht) om naar een datetime."""
    h, m, s = (int(x) for x in time_str.split(":"))
    return service_date.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(
        hours=h, minutes=m, seconds=s
    )


def find_stop_ids(stops: pd.DataFrame, name_query: str) -> pd.DataFrame:
    """Vind alle stops waarvan de naam de zoekterm bevat (hoofdletterongevoelig)."""
    matches = stops[stops["stop_name"].str.contains(name_query, case=False, na=False)]
    print(f"Gevonden haltes voor '{name_query}':")
    for _, row in matches.iterrows():
        print(f"  stop_id={row['stop_id']}  stop_name={row['stop_name']}")
    return matches


def build_scheduled_lookup(stop_times: pd.DataFrame, trips: pd.DataFrame,
                            routes: pd.DataFrame, stop_ids: set[str]) -> pd.DataFrame:
    """Bouw een tabel met alle geplande stops op onze halte(n), incl. route-info."""
    relevant = stop_times[stop_times["stop_id"].isin(stop_ids)].copy()
    relevant = relevant.merge(trips[["trip_id", "route_id", "trip_headsign"]], on="trip_id", how="left")
    relevant = relevant.merge(routes[["route_id", "route_short_name"]], on="route_id", how="left")
    return relevant


def fetch_trip_updates(url: str = TRIP_UPDATES_URL) -> gtfs_realtime_pb2.FeedMessage:
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    feed = gtfs_realtime_pb2.FeedMessage()
    feed.ParseFromString(resp.content)
    return feed


def get_delay_for_stop(feed: gtfs_realtime_pb2.FeedMessage, trip_id: str, stop_id: str) -> int | None:
    """Zoek de vertraging (in seconden) voor een specifieke rit/halte in de live feed."""
    for entity in feed.entity:
        if not entity.HasField("trip_update"):
            continue
        tu = entity.trip_update
        if tu.trip.trip_id != trip_id:
            continue
        for stu in tu.stop_time_update:
            if stu.stop_id != stop_id:
                continue
            if stu.HasField("departure") and stu.departure.HasField("delay"):
                return stu.departure.delay
            if stu.HasField("arrival") and stu.arrival.HasField("delay"):
                return stu.arrival.delay
    return None


def ensure_csv_header(path: Path) -> None:
    if not path.exists():
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "poll_tijdstip", "stop_id", "stop_name", "trip_id", "route_short_name",
                "bestemming", "geplande_vertrektijd", "voorspelde_vertrektijd", "vertraging_sec",
            ])


def poll_and_log(scheduled: pd.DataFrame, stops: pd.DataFrame) -> None:
    ensure_csv_header(OUTPUT_CSV)
    stop_names = dict(zip(stops["stop_id"], stops["stop_name"]))
    print(f"{len(scheduled)} geplande stops gevonden op deze halte(s) in stop_times.txt")

    while True:
        today = datetime.now()  # elke ronde verversen, anders schuift het tijdvenster niet mee
        try:
            feed = fetch_trip_updates()
            rows_written = 0
            with open(OUTPUT_CSV, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                for _, row in scheduled.iterrows():
                    scheduled_dep = parse_gtfs_time(row["departure_time"], today)

                    # alleen ritten tonen die nog moeten vertrekken (binnen de komende 2 uur)
                    if not (today - timedelta(minutes=5) <= scheduled_dep <= today + timedelta(hours=2)):
                        continue

                    delay = get_delay_for_stop(feed, row["trip_id"], row["stop_id"])
                    predicted_dep = scheduled_dep + timedelta(seconds=delay or 0)

                    writer.writerow([
                        datetime.now().isoformat(timespec="seconds"),
                        row["stop_id"],
                        stop_names.get(row["stop_id"], "?"),
                        row["trip_id"],
                        row.get("route_short_name", "?"),
                        row.get("trip_headsign", "?"),
                        scheduled_dep.strftime("%H:%M:%S"),
                        predicted_dep.strftime("%H:%M:%S"),
                        delay or 0,
                    ])
                    rows_written += 1

            print(f"[{datetime.now():%H:%M:%S}] {rows_written} vertrektijden gelogd naar {OUTPUT_CSV}")
        except requests.RequestException as e:
            print(f"Fout bij ophalen live feed: {e}")

        time.sleep(POLL_INTERVAL_SECONDS)


def main() -> None:
    # dtype=str is cruciaal: stop_id/trip_id/route_id moeten als TEKST gelezen worden.
    # Anders leest pandas ze in het ene bestand als getal en in het andere als string
    # (vooral bij gemengde ID's zoals "stoparea:17883"), waardoor .isin()-matches
    # stilletjes mislukken en je 0 resultaten krijgt zonder foutmelding.
    id_dtypes = {"stop_id": str, "trip_id": str, "route_id": str, "service_id": str}
    stops = pd.read_csv(GTFS_DIR / "stops.txt", low_memory=False, dtype=id_dtypes)
    stop_times = pd.read_csv(GTFS_DIR / "stop_times.txt", low_memory=False, dtype=id_dtypes)
    trips = pd.read_csv(GTFS_DIR / "trips.txt", low_memory=False, dtype=id_dtypes)
    routes = pd.read_csv(GTFS_DIR / "routes.txt", low_memory=False, dtype=id_dtypes)

    matches = find_stop_ids(stops, STOP_NAME_QUERY)
    if matches.empty:
        print("Geen haltes gevonden -- pas STOP_NAME_QUERY aan.")
        return

    stop_ids = set(matches["stop_id"])
    scheduled = build_scheduled_lookup(stop_times, trips, routes, stop_ids)
    poll_and_log(scheduled, stops)


if __name__ == "__main__":
    main()
