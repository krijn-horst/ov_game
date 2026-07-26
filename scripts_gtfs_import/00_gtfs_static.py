"""
Ophalen van de statische GTFS-dienstregeling (schedule) en het geonetwerk
(haltes + routegeometrie) van het Nederlandse OV, aangeboden via NDOV/OVapi.

Bron: http://gtfs.ovapi.nl/gtfs-nl.zip
Let op: dit bundelt ~44 vervoerders in NL, het bestand is groot
(zip ~200 MB, uitgepakt ~1.3 GB). De feed wordt dagelijks ververst.

Installeren:
    pip install requests pandas geopandas shapely
"""

import io
import zipfile
from pathlib import Path

import geopandas as gpd
import pandas as pd
import requests
from shapely.geometry import LineString, Point

GTFS_STATIC_URL = "http://gtfs.ovapi.nl/gtfs-nl.zip"
OUTPUT_DIR = Path("gtfs_static")


def download_gtfs(url: str = GTFS_STATIC_URL, out_dir: Path = OUTPUT_DIR) -> Path:
    """Download en pak de statische GTFS-feed uit."""
    out_dir.mkdir(exist_ok=True)
    print(f"Downloaden van {url} (kan even duren, bestand is groot) ...")
    resp = requests.get(url, timeout=300, stream=True)
    resp.raise_for_status()

    buffer = io.BytesIO()
    for chunk in resp.iter_content(chunk_size=1024 * 1024):
        buffer.write(chunk)
    buffer.seek(0)

    with zipfile.ZipFile(buffer) as z:
        z.extractall(out_dir)
    print(f"Uitgepakt naar {out_dir.resolve()}")
    return out_dir


def load_tables(gtfs_dir: Path = OUTPUT_DIR) -> dict[str, pd.DataFrame]:
    """Laad de belangrijkste GTFS-tabellen (dienstregeling) als DataFrames."""
    files = ["agency", "stops", "routes", "trips", "stop_times", "shapes", "calendar", "calendar_dates"]
    tables: dict[str, pd.DataFrame] = {}
    for f in files:
        path = gtfs_dir / f"{f}.txt"
        if path.exists():
            tables[f] = pd.read_csv(path, low_memory=False)
            print(f"{f}.txt: {len(tables[f])} rijen")
        else:
            print(f"{f}.txt niet gevonden, overgeslagen")
    return tables


def build_stops_geodataframe(stops: pd.DataFrame) -> gpd.GeoDataFrame:
    """Haltes/stations als puntenlaag (onderdeel van het geonetwerk)."""
    geometry = [Point(xy) for xy in zip(stops["stop_lon"], stops["stop_lat"])]
    return gpd.GeoDataFrame(stops, geometry=geometry, crs="EPSG:4326")


def build_shapes_geodataframe(shapes: pd.DataFrame) -> gpd.GeoDataFrame:
    """Routegeometrie (shapes.txt) als lijnenlaag: het feitelijke geonetwerk."""
    shapes_sorted = shapes.sort_values(["shape_id", "shape_pt_sequence"])
    lines, shape_ids = [], []
    for shape_id, group in shapes_sorted.groupby("shape_id"):
        coords = list(zip(group["shape_pt_lon"], group["shape_pt_lat"]))
        if len(coords) >= 2:
            lines.append(LineString(coords))
            shape_ids.append(shape_id)
    return gpd.GeoDataFrame({"shape_id": shape_ids}, geometry=lines, crs="EPSG:4326")


def main() -> None:
    gtfs_dir = download_gtfs()
    tables = load_tables(gtfs_dir)

    if "stops" in tables:
        stops_gdf = build_stops_geodataframe(tables["stops"])
        stops_gdf.to_file(gtfs_dir / "stops.geojson", driver="GeoJSON")
        print(f"Haltes weggeschreven: {gtfs_dir / 'stops.geojson'}")

    if "shapes" in tables:
        shapes_gdf = build_shapes_geodataframe(tables["shapes"])
        shapes_gdf.to_file(gtfs_dir / "shapes.geojson", driver="GeoJSON")
        print(f"Geonetwerk (routegeometrie) weggeschreven: {gtfs_dir / 'shapes.geojson'}")

    if "routes" in tables and "trips" in tables:
        routes_trips = tables["trips"].merge(tables["routes"], on="route_id", how="left")
        routes_trips.to_csv(gtfs_dir / "routes_trips.csv", index=False)
        print(f"Dienstregeling (routes/ritten) overzicht: {gtfs_dir / 'routes_trips.csv'}")


if __name__ == "__main__":
    main()
