#!/usr/bin/env bash
set -euo pipefail

# ============================================
# 02_load_input_data.sh
# Laadt GTFS-statische data en de CBS wijk-en-buurtkaart (wijken + buurten +
# gemeenten, alle 3 als lagen in 1 GeoPackage) in de OV Game database, en
# koppelt elke halte aan zijn wijk, buurt en gemeente.
#
# Gebruik:
#   ./02_load_input_data.sh
#
# LET OP: de laagnamen in de GeoPackage (bv. 'wijken', 'buurten', 'gemeenten')
# en de kolomnamen daarbinnen (bv. 'buurtcode', 'wijkcode') kunnen per
# jaar/versie verschillen. Check dit vooraf met:
#   ogrinfo -so "$CBS_GPKG"
# en pas WIJKEN_LAYER / BUURTEN_LAYER / GEMEENTEN_LAYER en stap 5 hieronder aan.
# ============================================

# ============================================
# GDAL / PROJ configuratie
# Gebruik systeem GDAL i.p.v. Anaconda GDAL
# ============================================
export PROJ_LIB=/usr/share/proj

PGBIN="/usr/bin"
GDAL_BIN="/usr/bin"

PSQL="$PGBIN/psql"
OGR2OGR="$GDAL_BIN/ogr2ogr"
OGRINFO="$GDAL_BIN/ogrinfo"

if [[ ! -x "$PSQL" ]]; then
    echo "FOUT: psql niet gevonden op $PSQL"
    exit 1
fi

if [[ ! -x "$OGR2OGR" ]]; then
    echo "FOUT: ogr2ogr niet gevonden op $OGR2OGR"
    exit 1
fi

if [[ ! -x "$OGRINFO" ]]; then
    echo "FOUT: ogrinfo niet gevonden op $OGRINFO"
    exit 1
fi


# --- Pas deze paden aan naar jouw eigen situatie ---
GTFS_DIR="/home/krijn/Desktop/ov_game/gtfs_static"
CBS_GPKG="/home/krijn/Desktop/ov_game/data/WijkBuurtkaart_2026_v0.gpkg"

# --- Laagnamen zoals ze in de GeoPackage heten (check met ogrinfo -so "$CBS_GPKG") ---
WIJKEN_LAYER="wijken"
BUURTEN_LAYER="buurten"
GEMEENTEN_LAYER="gemeenten"

SCHEMA_SQL="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/02a_create_tables.sql"
SCRIPT_DIR="$(dirname "$SCHEMA_SQL")"
CONFIG_FILE="$SCRIPT_DIR/khorstmanshoff_user_config.ini"

if [[ ! -f "$CONFIG_FILE" ]]; then
    echo "FOUT: configuratiebestand niet gevonden: $CONFIG_FILE"
    exit 1
fi

set -o allexport
source "$CONFIG_FILE"
set +o allexport

export PGPASSWORD="$DB_PASSWORD"
PSQL="$PGBIN/psql"
OGR2OGR="$GDAL_BIN/ogr2ogr"
PG_CONN="PG:host=$DB_HOST port=$DB_PORT dbname=$DB_NAME user=$DB_USER password=$DB_PASSWORD"

echo "============================================"
echo "Stap 1: Tabellen aanmaken (schema.sql)"
echo "============================================"
if [[ ! -f "$SCHEMA_SQL" ]]; then
    echo "FOUT: schema.sql niet gevonden: $SCHEMA_SQL"
    exit 1
fi
"$PSQL" -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "$SCHEMA_SQL"

echo "============================================"
echo "Stap 2: GTFS-data inladen"
echo "============================================"
"$PSQL" -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "\copy gtfs_stops(stop_id,stop_code,stop_name,stop_lat,stop_lon,location_type,parent_station,stop_timezone,wheelchair_boarding,platform_code,zone_id) FROM '$GTFS_DIR/stops.txt' WITH (FORMAT csv, HEADER true, NULL '')"
"$PSQL" -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "\copy gtfs_routes(route_id,agency_id,route_short_name,route_long_name,route_desc,route_type,route_color,route_text_color,route_url) FROM '$GTFS_DIR/routes.txt' WITH (FORMAT csv, HEADER true, NULL '')"
"$PSQL" -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "\copy gtfs_trips(route_id,service_id,trip_id,realtime_trip_id,trip_headsign,trip_short_name,trip_long_name,direction_id,block_id,shape_id,wheelchair_accessible,bikes_allowed) FROM '$GTFS_DIR/trips.txt' WITH (FORMAT csv, HEADER true, NULL '')"
"$PSQL" -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "\copy gtfs_stop_times(trip_id,stop_sequence,stop_id,stop_headsign,arrival_time,departure_time,pickup_type,drop_off_type,timepoint,shape_dist_traveled,fare_units_traveled) FROM '$GTFS_DIR/stop_times.txt' WITH (FORMAT csv, HEADER true, NULL '')"

echo "============================================"
echo "Stap 3: Geometrie voor haltes opbouwen"
echo "============================================"
"$PSQL" -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "
UPDATE gtfs_stops SET geom = ST_SetSRID(ST_MakePoint(stop_lon, stop_lat), 4326) WHERE stop_lon IS NOT NULL AND stop_lat IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_gtfs_stops_geom ON gtfs_stops USING GIST (geom);
"

echo "============================================"
echo "Stap 4: CBS wijken, buurten en gemeenten inladen (via ogr2ogr)"
echo "============================================"

if [[ ! -f "$CBS_GPKG" ]]; then
    echo "FOUT: $CBS_GPKG niet gevonden."
    exit 1
fi

echo "-- laag '$WIJKEN_LAYER' -> tabel cbs_wijken"
"$OGR2OGR" -f PostgreSQL "$PG_CONN" "$CBS_GPKG" "$WIJKEN_LAYER" -nln cbs_wijken -overwrite -lco GEOMETRY_NAME=geom -t_srs EPSG:4326

echo "-- laag '$BUURTEN_LAYER' -> tabel cbs_buurten"
"$OGR2OGR" -f PostgreSQL "$PG_CONN" "$CBS_GPKG" "$BUURTEN_LAYER" -nln cbs_buurten -overwrite -lco GEOMETRY_NAME=geom -t_srs EPSG:4326

echo "-- laag '$GEMEENTEN_LAYER' -> tabel cbs_gemeenten"
"$OGR2OGR" -f PostgreSQL "$PG_CONN" "$CBS_GPKG" "$GEMEENTEN_LAYER" -nln cbs_gemeenten -overwrite -lco GEOMETRY_NAME=geom -t_srs EPSG:4326

echo "============================================"
echo "Stap 5: Haltes koppelen aan wijk, buurt en gemeente"
echo "(pas kolomnamen wijkcode/buurtcode/gemeentecode aan indien nodig, zie opmerking bovenaan)"
echo "============================================"
"$PSQL" -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "
UPDATE gtfs_stops s SET wijkcode = w.wijkcode, wijknaam = w.wijknaam
    FROM cbs_wijken w WHERE ST_Within(s.geom, w.geom);

UPDATE gtfs_stops s SET buurtcode = b.buurtcode, buurtnaam = b.buurtnaam
    FROM cbs_buurten b WHERE ST_Within(s.geom, b.geom);

UPDATE gtfs_stops s SET gemeentecode = g.gemeentecode, gemeentenaam = g.gemeentenaam
    FROM cbs_gemeenten g WHERE ST_Within(s.geom, g.geom);
"

echo "============================================"
echo "Klaar. Haltes, routes, ritten en CBS wijken/buurten/gemeenten staan in $DB_NAME."
echo "============================================"