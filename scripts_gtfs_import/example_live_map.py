"""
Live kaart van OV-voertuigen in Nederland (GTFS-RT via NDOV/OVapi), gestreamd op Leaflet.

Dit is een kleine lokale webserver:
- haalt op de achtergrond elke X seconden de live voertuigposities op (protobuf)
- serveert ze als JSON op /api/vehicles
- serveert een Leaflet-kaart die dat elke paar seconden ophaalt en toont

Open daarna in je browser: http://localhost:5000
"""

import threading
import time

import requests
from flask import Flask, jsonify, render_template_string
from google.transit import gtfs_realtime_pb2

VEHICLE_POSITIONS_URL = "http://gtfs.ovapi.nl/nl/vehiclePositions.pb"
POLL_INTERVAL_SECONDS = 15

# Optioneel: filter op route_id's om het aantal markers te beperken (performance).
# Laat leeg (None) om alles te tonen.
ROUTE_ID_FILTER: set[str] | None = None

app = Flask(__name__)
_latest_vehicles: list[dict] = []
_lock = threading.Lock()


def fetch_vehicle_positions() -> list[dict]:
    resp = requests.get(VEHICLE_POSITIONS_URL, timeout=30)
    resp.raise_for_status()
    feed = gtfs_realtime_pb2.FeedMessage()
    feed.ParseFromString(resp.content)

    vehicles = []
    for entity in feed.entity:
        if not entity.HasField("vehicle"):
            continue
        v = entity.vehicle
        if not v.HasField("position"):
            continue

        route_id = v.trip.route_id if v.HasField("trip") else None
        if ROUTE_ID_FILTER and route_id not in ROUTE_ID_FILTER:
            continue

        vehicles.append({
            "id": entity.id,
            "trip_id": v.trip.trip_id if v.HasField("trip") else None,
            "route_id": route_id,
            "lat": v.position.latitude,
            "lon": v.position.longitude,
            "speed": v.position.speed if v.position.HasField("speed") else None,
        })
    return vehicles


def poll_loop() -> None:
    global _latest_vehicles
    while True:
        try:
            vehicles = fetch_vehicle_positions()
            with _lock:
                _latest_vehicles = vehicles
            print(f"{len(vehicles)} voertuigen opgehaald")
        except requests.RequestException as e:
            print(f"Fout bij ophalen live feed: {e}")
        time.sleep(POLL_INTERVAL_SECONDS)


@app.route("/api/vehicles")
def api_vehicles():
    with _lock:
        return jsonify(_latest_vehicles)


INDEX_HTML = """
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <title>Live OV-kaart Nederland</title>
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
  <style>
    html, body, #map { height: 100%; margin: 0; }
    #status {
      position: absolute; top: 10px; right: 10px; z-index: 1000;
      background: white; padding: 6px 10px; border-radius: 6px;
      font-family: sans-serif; font-size: 13px; box-shadow: 0 1px 4px rgba(0,0,0,0.3);
    }
  </style>
</head>
<body>
  <div id="status">Laden...</div>
  <div id="map"></div>
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
  <script>
    const map = L.map('map').setView([52.1, 5.3], 8);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '&copy; OpenStreetMap-bijdragers'
    }).addTo(map);

    let markers = {};

    async function refresh() {
      try {
        const res = await fetch('/api/vehicles');
        const vehicles = await res.json();
        document.getElementById('status').innerText = vehicles.length + ' voertuigen live';

        const seen = new Set();
        vehicles.forEach(v => {
          seen.add(v.id);
          const popup = `Route: ${v.route_id || '?'}<br>Rit: ${v.trip_id || '?'}<br>Snelheid: ${v.speed ?? '?'} m/s`;
          if (markers[v.id]) {
            markers[v.id].setLatLng([v.lat, v.lon]).setPopupContent(popup);
          } else {
            markers[v.id] = L.circleMarker([v.lat, v.lon], { radius: 5, color: '#0066cc', fillOpacity: 0.8 })
              .addTo(map)
              .bindPopup(popup);
          }
        });

        // verwijder voertuigen die niet meer in de feed zitten
        Object.keys(markers).forEach(id => {
          if (!seen.has(id)) {
            map.removeLayer(markers[id]);
            delete markers[id];
          }
        });
      } catch (e) {
        document.getElementById('status').innerText = 'Fout bij ophalen data';
        console.error(e);
      }
    }

    refresh();
    setInterval(refresh, 10000);
  </script>
</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(INDEX_HTML)


if __name__ == "__main__":
    threading.Thread(target=poll_loop, daemon=True).start()
    app.run(host="0.0.0.0", port=5000, debug=False)