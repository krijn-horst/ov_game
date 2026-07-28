-- schema.sql
-- Tabeldefinities voor de OV Game database.
-- Wordt uitgevoerd door 02_load_input_data.sh, vóór het inladen van data.
--
-- LET OP: dit script droppt en herbouwt de tabellen bij elke run
-- (dus alle data die erin staat gaat verloren -- dat hoort ook zo,
-- want 02_load_input_data.sh vult ze daarna opnieuw).

-- ============================================
-- Haltes
-- ============================================
DROP TABLE IF EXISTS gtfs_stops CASCADE;
CREATE TABLE gtfs_stops (
    stop_id              TEXT PRIMARY KEY,
    stop_code            TEXT,
    stop_name            TEXT,
    stop_lat             DOUBLE PRECISION,
    stop_lon             DOUBLE PRECISION,
    location_type        TEXT,
    parent_station       TEXT,
    stop_timezone        TEXT,
    wheelchair_boarding  TEXT,
    platform_code        TEXT,
    zone_id              TEXT,
    geom                 geometry(Point, 4326),
    -- gevuld in stap 5 van 02_load_input_data.sh na koppeling aan CBS-geografie
    wijkcode             TEXT,
    wijknaam             TEXT,
    buurtcode            TEXT,
    buurtnaam            TEXT,
    gemeentecode         TEXT,
    gemeentenaam         TEXT
);
CREATE INDEX idx_gtfs_stops_geom ON gtfs_stops USING GIST (geom);

-- ============================================
-- Routes
-- ============================================
DROP TABLE IF EXISTS gtfs_routes CASCADE;
CREATE TABLE gtfs_routes (
    route_id          TEXT PRIMARY KEY,
    agency_id         TEXT,
    route_short_name  TEXT,
    route_long_name   TEXT,
    route_desc        TEXT,
    route_type        INT,
    route_color       TEXT,
    route_text_color  TEXT,
    route_url         TEXT
);

-- ============================================
-- Ritten
-- ============================================
DROP TABLE IF EXISTS gtfs_trips CASCADE;
CREATE TABLE gtfs_trips (
    route_id               TEXT,
    service_id             TEXT,
    trip_id                TEXT PRIMARY KEY,
    realtime_trip_id       TEXT,
    trip_headsign          TEXT,
    trip_short_name        TEXT,
    trip_long_name         TEXT,
    direction_id           TEXT,
    block_id               TEXT,
    shape_id                TEXT,
    wheelchair_accessible  TEXT,
    bikes_allowed          TEXT
);

-- ============================================
-- Stop times
-- ============================================
DROP TABLE IF EXISTS gtfs_stop_times CASCADE;
CREATE TABLE gtfs_stop_times (
    trip_id              TEXT,
    stop_sequence        INT,
    stop_id              TEXT,
    stop_headsign        TEXT,
    arrival_time         TEXT,
    departure_time       TEXT,
    pickup_type          TEXT,
    drop_off_type        TEXT,
    timepoint            TEXT,
    shape_dist_traveled  DOUBLE PRECISION,
    fare_units_traveled  TEXT
);
CREATE INDEX idx_gtfs_stop_times_trip ON gtfs_stop_times (trip_id);
CREATE INDEX idx_gtfs_stop_times_stop ON gtfs_stop_times (stop_id);