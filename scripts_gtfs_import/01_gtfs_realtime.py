"""
Verbinden met de live GTFS-Realtime (GTFS-RT) feed van het Nederlandse OV,
aangeboden via NDOV/OVapi.

Feeds (protobuf, GTFS-RT standaard):
- TripUpdates:      http://gtfs.ovapi.nl/nl/tripUpdates.pb
- VehiclePositions: http://gtfs.ovapi.nl/nl/vehiclePositions.pb
- Alerts:           http://gtfs.ovapi.nl/nl/alerts.pb
- TrainUpdates:     http://gtfs.ovapi.nl/nl/trainUpdates.pb  (los feed voor treinen)

Installeren:
    pip install gtfs-realtime-bindings requests
"""

import time
import requests
from google.transit import gtfs_realtime_pb2

BASE_URL = "http://gtfs.ovapi.nl/nl"
TRIP_UPDATES_URL = f"{BASE_URL}/tripUpdates.pb"
VEHICLE_POSITIONS_URL = f"{BASE_URL}/vehiclePositions.pb"
ALERTS_URL = f"{BASE_URL}/alerts.pb"
TRAIN_UPDATES_URL = f"{BASE_URL}/trainUpdates.pb"


def fetch_feed(url: str) -> gtfs_realtime_pb2.FeedMessage:
    """Haal een GTFS-RT protobuf feed op en parse hem."""
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    feed = gtfs_realtime_pb2.FeedMessage()
    feed.ParseFromString(resp.content)
    return feed


def print_vehicle_positions(feed: gtfs_realtime_pb2.FeedMessage, limit: int = 20) -> None:
    count = 0
    for entity in feed.entity:
        if entity.HasField("vehicle"):
            v = entity.vehicle
            trip_id = v.trip.trip_id if v.HasField("trip") else "?"
            route_id = v.trip.route_id if v.HasField("trip") else "?"
            lat, lon = v.position.latitude, v.position.longitude
            speed = v.position.speed if v.position.HasField("speed") else None
            print(f"Voertuig {entity.id} | route {route_id} | rit {trip_id} "
                  f"| ({lat:.5f}, {lon:.5f}) | snelheid: {speed}")
            count += 1
            if count >= limit:
                break


def print_trip_updates(feed: gtfs_realtime_pb2.FeedMessage, limit: int = 20) -> None:
    count = 0
    for entity in feed.entity:
        if entity.HasField("trip_update"):
            tu = entity.trip_update
            trip_id = tu.trip.trip_id
            route_id = tu.trip.route_id
            for stu in tu.stop_time_update[:1]:  # alleen eerstvolgende halte
                delay = None
                if stu.HasField("arrival") and stu.arrival.HasField("delay"):
                    delay = stu.arrival.delay
                elif stu.HasField("departure") and stu.departure.HasField("delay"):
                    delay = stu.departure.delay
                print(f"Rit {trip_id} | route {route_id} | halte {stu.stop_id} "
                      f"| vertraging: {delay} sec")
            count += 1
            if count >= limit:
                break


def print_alerts(feed: gtfs_realtime_pb2.FeedMessage, limit: int = 10) -> None:
    count = 0
    for entity in feed.entity:
        if entity.HasField("alert"):
            alert = entity.alert
            header = alert.header_text.translation[0].text if alert.header_text.translation else "?"
            print(f"Melding {entity.id}: {header}")
            count += 1
            if count >= limit:
                break


def poll(interval_seconds: int = 30, include_alerts: bool = True) -> None:
    """Blijf de live feeds periodiek ophalen en tonen (Ctrl+C om te stoppen)."""
    while True:
        try:
            print("\n=== Voertuigposities ===")
            print_vehicle_positions(fetch_feed(VEHICLE_POSITIONS_URL))

            print("\n=== Ritupdates (vertragingen) ===")
            print_trip_updates(fetch_feed(TRIP_UPDATES_URL))

            if include_alerts:
                print("\n=== Meldingen/storingen ===")
                print_alerts(fetch_feed(ALERTS_URL))

        except requests.RequestException as e:
            print(f"Fout bij ophalen feed: {e}")

        time.sleep(interval_seconds)


if __name__ == "__main__":
    poll(interval_seconds=30)
