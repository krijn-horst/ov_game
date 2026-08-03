import sqlite3
import json
from pathlib import Path
from datetime import datetime
import requests
from google.transit import gtfs_realtime_pb2
from datetime import timedelta

DATABASE = Path("/home/krijn/Desktop/ov_game/stops/database/ov.db")

STOP_ID = "3923791"
OUTPUT_JSON = "departures.json"


MODALITIES = {
    "0": "tram",
    "1": "metro",
    "2": "trein",
    "3": "bus",
    "4": "veerboot",
    "5": "kabelbaan",
    "6": "gondel",
    "7": "funicular"
}

TRIP_UPDATES_URL = "http://gtfs.ovapi.nl/nl/tripUpdates.pb"


def gtfs_time_to_seconds(gtfs_time):

    h, m, s = map(int, gtfs_time.split(":"))

    return h * 3600 + m * 60 + s


def current_gtfs_seconds():

    now = datetime.now()

    return (
        now.hour * 3600
        + now.minute * 60
        + now.second
    )


def today_gtfs_info():

    now = datetime.now()

    weekday_map = {
        0: "monday",
        1: "tuesday",
        2: "wednesday",
        3: "thursday",
        4: "friday",
        5: "saturday",
        6: "sunday"
    }

    return (
        now.strftime("%Y%m%d"),
        weekday_map[now.weekday()]
    )


def get_active_services(conn):

    today = datetime.now().strftime("%Y%m%d")

    cursor = conn.cursor()

    active = set()


    cursor.execute(
        """
        SELECT service_id, exception_type
        FROM calendar_dates
        WHERE date = ?
        """,
        (today,)
    )


    for service_id, exception_type in cursor.fetchall():

        if exception_type == "1":
            active.add(service_id)

        elif exception_type == "2":
            active.discard(service_id)


    return active



def get_departures(stop_id, limit=25):

    conn = sqlite3.connect(DATABASE)

    conn.row_factory = sqlite3.Row


    active_services = get_active_services(
        conn
    )


    if not active_services:
        return []


    placeholders = ",".join(
        ["?"] * len(active_services)
    )


    query = f"""

    SELECT

        stops.stop_name,

        routes.route_short_name,
        routes.route_type,
        routes.route_id,

        trips.trip_id,
        trips.trip_headsign,

        stop_times.departure_time


    FROM stop_times


    JOIN trips
        ON stop_times.trip_id = trips.trip_id


    JOIN routes
        ON trips.route_id = routes.route_id


    JOIN stops
        ON stop_times.stop_id = stops.stop_id


    WHERE stop_times.stop_id = ?

    AND trips.service_id IN ({placeholders})


    ORDER BY stop_times.departure_time

    """


    params = [
        stop_id,
        *active_services
    ]


    cursor = conn.cursor()

    cursor.execute(
        query,
        params
    )


    now = current_gtfs_seconds()

    departures = []

    feed = fetch_trip_updates()
    delay_index = build_delay_index(feed)   # <-- toegevoegd

    seen = set()


    for row in cursor.fetchall():

        seconds = gtfs_time_to_seconds(
            row["departure_time"]
        )


        if seconds < now:
            continue


        # dubbele ritten voorkomen
        key = (
            row["route_short_name"],
            row["trip_headsign"],
            row["departure_time"]
        )


        if key in seen:
            continue


        seen.add(key)

        delay = get_delay(
            delay_index,      # <-- was: feed
            row["trip_id"],
            stop_id
        )
        
        expected_seconds = (
            gtfs_time_to_seconds(
                row["departure_time"]
            )
            +
            delay
        )


        hours = expected_seconds // 3600
        minutes = (expected_seconds % 3600) // 60
        seconds = expected_seconds % 60


        expected_time = (
            f"{hours:02d}:"
            f"{minutes:02d}:"
            f"{seconds:02d}"
        )

        departures.append(
            {
                "stop_id": stop_id,
                "stop_name": row["stop_name"],
                "line": row["route_short_name"],
                "route_id": row["route_id"],
                "trip_id": row["trip_id"],
                "destination": row["trip_headsign"],
                "mode": MODALITIES.get(
                    row["route_type"],
                    "unknown"
                ),
                "scheduled": row["departure_time"],
                "delay_seconds": delay,
                "expected": expected_time
            }
        )


        if len(departures) >= limit:
            break


    conn.close()

    return departures

def fetch_trip_updates():

    response = requests.get(
        TRIP_UPDATES_URL,
        timeout=10
    )

    response.raise_for_status()

    feed = gtfs_realtime_pb2.FeedMessage()

    feed.ParseFromString(
        response.content
    )

    return feed

def build_delay_index(feed):
    """Bouw eenmalig een index: trip_id -> {stop_id: delay_seconds}"""
    index = {}

    for entity in feed.entity:
        if not entity.HasField("trip_update"):
            continue

        tu = entity.trip_update
        trip_id = tu.trip.trip_id

        stop_delays = {}
        for stu in tu.stop_time_update:
            delay = None
            if stu.HasField("departure") and stu.departure.HasField("delay"):
                delay = stu.departure.delay
            elif stu.HasField("arrival") and stu.arrival.HasField("delay"):
                delay = stu.arrival.delay

            if delay is not None:
                stop_delays[stu.stop_id] = delay

        if stop_delays:
            index[trip_id] = stop_delays

    return index


def get_delay(delay_index, trip_id, stop_id):
    stop_delays = delay_index.get(trip_id)
    if not stop_delays:
        return 0

    if stop_id in stop_delays:
        return stop_delays[stop_id]

    # geen delay specifiek voor deze stop_id -> pak een fallback
    # (bv. laatst bekende delay in de update, als proxy)
    return next(iter(stop_delays.values()), 0)


def save_json(stop_id, departures):

    output = {
        "stop_id": stop_id,
        "updated": datetime.now().isoformat(
            timespec="seconds"
        ),
        "departures": departures
    }


    with open(
        OUTPUT_JSON,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            output,
            f,
            indent=2,
            ensure_ascii=False
        )



if __name__ == "__main__":

    departures = get_departures(
        STOP_ID
    )

    save_json(
        STOP_ID,
        departures
    )

    print(
        f"{len(departures)} vertrekken gevonden"
    )