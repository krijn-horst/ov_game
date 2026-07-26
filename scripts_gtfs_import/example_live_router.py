"""
Vereenvoudigde OV-router met live vertragingen -- zelfde basisprincipe als 9292/NS-planner,
gebouwd met het Connection Scan Algorithm (CSA) bovenop de statische NL GTFS-feed en
live vertragingen uit GTFS-RT tripUpdates.

LET OP: dit is een leerzaam/werkend voorbeeld, GEEN productie-router. Ontbrekend
t.o.v. echte planners: voetpaden/overstaptijden, meerdere dagen, storingen/omleidingen,
prestatie op de volledige NL-dataset (zet ROUTE_TYPE_FILTER of AGENCY_FILTER om te
beperken als het te traag is). Voor productiegebruik: OpenTripPlanner of Motis.

Vereist een lokale kopie van de statische GTFS (zie gtfs_static.py) in ./gtfs_nl_static/
    stops.txt, stop_times.txt, trips.txt, routes.txt, calendar.txt, calendar_dates.txt

Installeren:
    pip install requests pandas gtfs-realtime-bindings
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import requests
from google.transit import gtfs_realtime_pb2

GTFS_DIR = Path("gtfs_static")
TRIP_UPDATES_URL = "http://gtfs.ovapi.nl/nl/tripUpdates.pb"

# Optioneel filteren om het dataset te beperken (performance). Laat leeg voor alles.
AGENCY_FILTER: set[str] | None = None          # bv. {"HTM", "GVB"}
LOOKAHEAD_HOURS = 4                             # alleen verbindingen binnen dit venster meenemen


@dataclass
class Connection:
    trip_id: str
    from_stop: str
    to_stop: str
    dep_time: datetime
    arr_time: datetime


def parse_gtfs_time(time_str: str, service_date: datetime) -> datetime:
    h, m, s = (int(x) for x in time_str.split(":"))
    return service_date.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(
        hours=h, minutes=m, seconds=s
    )


def get_active_service_ids(calendar: pd.DataFrame, calendar_dates: pd.DataFrame, date: datetime) -> set[str]:
    """Bepaal welke service_id's vandaag actief zijn (weekdag + uitzonderingen).

    Werkt ook als calendar.txt ontbreekt (sommige feeds publiceren alleen
    calendar_dates.txt met exacte data per service_id, zonder weekpatroon).
    """
    date_int = int(date.strftime("%Y%m%d"))

    if calendar is not None and not calendar.empty:
        weekday_col = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"][date.weekday()]
        active = set(calendar[
            (calendar[weekday_col] == 1) &
            (calendar["start_date"] <= date_int) &
            (calendar["end_date"] >= date_int)
        ]["service_id"])
    else:
        active = set()

    if calendar_dates is not None and not calendar_dates.empty:
        today_exceptions = calendar_dates[calendar_dates["date"] == date_int]
        added = set(today_exceptions[today_exceptions["exception_type"] == 1]["service_id"])
        removed = set(today_exceptions[today_exceptions["exception_type"] == 2]["service_id"])
        active = (active | added) - removed

    return active


def fetch_live_delays() -> dict[str, dict[int, int]]:
    """Haal live vertragingen op: {trip_id: {stop_sequence: delay_seconds}}."""
    try:
        resp = requests.get(TRIP_UPDATES_URL, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"Kon live feed niet ophalen, ga verder zonder live data: {e}")
        return {}

    feed = gtfs_realtime_pb2.FeedMessage()
    feed.ParseFromString(resp.content)

    delays: dict[str, dict[int, int]] = {}
    for entity in feed.entity:
        if not entity.HasField("trip_update"):
            continue
        tu = entity.trip_update
        seq_delays = {}
        for stu in tu.stop_time_update:
            delay = None
            if stu.HasField("departure") and stu.departure.HasField("delay"):
                delay = stu.departure.delay
            elif stu.HasField("arrival") and stu.arrival.HasField("delay"):
                delay = stu.arrival.delay
            if delay is not None:
                seq_delays[stu.stop_sequence] = delay
        if seq_delays:
            delays[tu.trip.trip_id] = seq_delays
    return delays


def build_connections(stop_times: pd.DataFrame, active_service_ids: set[str],
                       trips: pd.DataFrame, live_delays: dict[str, dict[int, int]],
                       now: datetime) -> list[Connection]:
    """Bouw de lijst van verbindingen (elke rit tussen 2 opeenvolgende haltes)."""
    active_trip_ids = set(trips[trips["service_id"].isin(active_service_ids)]["trip_id"])
    window_end = now + timedelta(hours=LOOKAHEAD_HOURS)

    relevant = stop_times[stop_times["trip_id"].isin(active_trip_ids)].sort_values(
        ["trip_id", "stop_sequence"]
    )

    connections: list[Connection] = []
    for trip_id, group in relevant.groupby("trip_id"):
        rows = group.to_dict("records")
        trip_delays = live_delays.get(trip_id, {})
        current_delay = 0

        for i in range(len(rows) - 1):
            a, b = rows[i], rows[i + 1]

            if a["stop_sequence"] in trip_delays:
                current_delay = trip_delays[a["stop_sequence"]]
            dep_time = parse_gtfs_time(a["departure_time"], now) + timedelta(seconds=current_delay)

            if b["stop_sequence"] in trip_delays:
                current_delay = trip_delays[b["stop_sequence"]]
            arr_time = parse_gtfs_time(b["arrival_time"], now) + timedelta(seconds=current_delay)

            if dep_time < now - timedelta(minutes=2) or dep_time > window_end:
                continue

            connections.append(Connection(trip_id, a["stop_id"], b["stop_id"], dep_time, arr_time))

    connections.sort(key=lambda c: c.dep_time)
    return connections


def find_route(connections: list[Connection], origin_stop: str, destination_stop: str,
                depart_after: datetime) -> list[Connection] | None:
    """Connection Scan Algorithm: vind de vroegst mogelijke aankomst."""
    earliest_arrival: dict[str, datetime] = {origin_stop: depart_after}
    predecessor: dict[str, Connection] = {}
    reachable_trips: set[str] = set()

    for c in connections:
        if c.dep_time < depart_after:
            continue
        if destination_stop in earliest_arrival and c.dep_time > earliest_arrival[destination_stop]:
            break  # geen latere verbinding kan de aankomst nog verbeteren

        can_board = c.trip_id in reachable_trips or (
            c.from_stop in earliest_arrival and earliest_arrival[c.from_stop] <= c.dep_time
        )
        if not can_board:
            continue

        reachable_trips.add(c.trip_id)
        if c.to_stop not in earliest_arrival or c.arr_time < earliest_arrival[c.to_stop]:
            earliest_arrival[c.to_stop] = c.arr_time
            predecessor[c.to_stop] = c

    if destination_stop not in earliest_arrival:
        return None

    # reconstrueer het pad terug naar de oorsprong
    path: list[Connection] = []
    current = destination_stop
    while current != origin_stop:
        conn = predecessor[current]
        path.append(conn)
        current = conn.from_stop
    path.reverse()
    return path


def print_itinerary(path: list[Connection], stop_names: dict[str, str], trips: pd.DataFrame,
                     routes: pd.DataFrame) -> None:
    """Groepeer opeenvolgende verbindingen met dezelfde rit tot 1 leg en print het resultaat."""
    trip_route = dict(zip(trips["trip_id"], trips["route_id"]))
    route_names = dict(zip(routes["route_id"], routes["route_short_name"]))

    legs = []
    current_leg = [path[0]]
    for conn in path[1:]:
        if conn.trip_id == current_leg[-1].trip_id:
            current_leg.append(conn)
        else:
            legs.append(current_leg)
            current_leg = [conn]
    legs.append(current_leg)

    print("\nGevonden route:")
    for leg in legs:
        first, last = leg[0], leg[-1]
        route_name = route_names.get(trip_route.get(first.trip_id), "?")
        print(
            f"  Lijn {route_name}: vertrek {stop_names.get(first.from_stop, first.from_stop)} "
            f"om {first.dep_time:%H:%M} -> aankomst {stop_names.get(last.to_stop, last.to_stop)} "
            f"om {last.arr_time:%H:%M}"
        )
    print(f"Totale aankomsttijd: {legs[-1][-1].arr_time:%H:%M}")


def main(origin_name: str, destination_name: str, depart_after: datetime | None = None) -> None:
    depart_after = depart_after or datetime.now()

    # dtype=str voorkomt dat stop_id/trip_id/route_id/service_id in het ene bestand
    # als getal en in het andere als string worden ingelezen (zie ook live_departures_stop.py) --
    # zonder dit gaan .isin()-matches en merges stilletjes mis.
    id_dtypes = {"stop_id": str, "trip_id": str, "route_id": str, "service_id": str}
    stops = pd.read_csv(GTFS_DIR / "stops.txt", low_memory=False, dtype=id_dtypes)
    stop_times = pd.read_csv(GTFS_DIR / "stop_times.txt", low_memory=False, dtype=id_dtypes)
    trips = pd.read_csv(GTFS_DIR / "trips.txt", low_memory=False, dtype=id_dtypes)
    routes = pd.read_csv(GTFS_DIR / "routes.txt", low_memory=False, dtype=id_dtypes)
    try:
        calendar = pd.read_csv(GTFS_DIR / "calendar.txt", low_memory=False, dtype=id_dtypes)
    except FileNotFoundError:
        calendar = pd.DataFrame()
    try:
        calendar_dates = pd.read_csv(GTFS_DIR / "calendar_dates.txt", low_memory=False, dtype=id_dtypes)
    except FileNotFoundError:
        calendar_dates = pd.DataFrame()

    if calendar.empty and calendar_dates.empty:
        print("Geen calendar.txt of calendar_dates.txt gevonden -- kan actieve diensten niet bepalen.")
        return

    if AGENCY_FILTER:
        routes = routes[routes["agency_id"].isin(AGENCY_FILTER)]
        trips = trips[trips["route_id"].isin(routes["route_id"])]

    origin_matches = stops[stops["stop_name"].str.contains(origin_name, case=False, na=False)]
    dest_matches = stops[stops["stop_name"].str.contains(destination_name, case=False, na=False)]
    if origin_matches.empty or dest_matches.empty:
        print("Halte(s) niet gevonden -- controleer de namen.")
        return

    origin_stop_id = origin_matches.iloc[0]["stop_id"]
    destination_stop_id = dest_matches.iloc[0]["stop_id"]
    print(f"Van: {origin_matches.iloc[0]['stop_name']} ({origin_stop_id})")
    print(f"Naar: {dest_matches.iloc[0]['stop_name']} ({destination_stop_id})")

    active_service_ids = get_active_service_ids(calendar, calendar_dates, depart_after)
    live_delays = fetch_live_delays()
    connections = build_connections(stop_times, active_service_ids, trips, live_delays, depart_after)
    print(f"{len(connections)} verbindingen binnen het tijdvenster van {LOOKAHEAD_HOURS} uur")

    path = find_route(connections, origin_stop_id, destination_stop_id, depart_after)
    if path is None:
        print("Geen route gevonden binnen het tijdvenster -- vergroot LOOKAHEAD_HOURS.")
        return

    stop_names = dict(zip(stops["stop_id"], stops["stop_name"]))
    print_itinerary(path, stop_names, trips, routes)


if __name__ == "__main__":
    main("Nijmegen, Fransestraat", "Groesbeek, Centrum")