import {
    MapContainer,
    TileLayer,
    CircleMarker,
    Popup,
    useMap,
    useMapEvents,
} from "react-leaflet";

import { useEffect, useMemo, useState } from "react";

import Supercluster from "supercluster";

import "leaflet/dist/leaflet.css";
import "./RoutePage.css";


/*
 * Configuration
 */

const MIN_ZOOM = 7;
const MAX_ZOOM = 18;


/*
 * Types
 */

interface StopProperties {
    stop_id?: string;
    stop_code?: string | null;
    stop_name?: string;
    stop_lat?: number;
    stop_lon?: number;
    location_type?: number;
    parent_station?: string | null;
    stop_timezone?: string | null;
    wheelchair_boarding?: number | null;
    platform_code?: string | null;
    zone_id?: string | null;
}


interface StopFeature {
    type: "Feature";

    properties: StopProperties;

    geometry: {
        type: "Point";

        coordinates: [
            number,
            number
        ];
    };
}


interface StopsGeoJSON {
    type: "FeatureCollection";

    features: StopFeature[];
}


/*
 * Properties stored inside Supercluster.
 */

interface StopClusterProperties {
    cluster?: boolean;

    cluster_id?: number;

    point_count?: number;

    point_count_abbreviated?: number | string;

    stop_id?: string;

    stop_name?: string;

    platform_code?: string | null;
}


/*
 * Supercluster feature type.
 */

type StopPoint =
    GeoJSON.Feature<
        GeoJSON.Point,
        StopClusterProperties
    >;


/*
 * Load the GeoJSON and convert it into
 * the format Supercluster expects.
 */

const createPoints = (
    data: StopsGeoJSON
): StopPoint[] => {

    return data.features.map(
        (stop) => {

            return {
                type: "Feature",

                properties: {
                    stop_id:
                        stop.properties.stop_id,

                    stop_name:
                        stop.properties.stop_name,

                    platform_code:
                        stop.properties.platform_code,

                    cluster: false,
                },

                geometry: {
                    type: "Point",

                    coordinates:
                        stop.geometry.coordinates,
                },
            };

        }
    );

};


/*
 * Component responsible for rendering
 * clusters and individual stops.
 */

interface StopLayerProps {
    points: StopPoint[];
}


const StopLayer = ({
    points
}: StopLayerProps) => {

    const map = useMap();


    /*
     * Current map state.
     */

    const [
        bounds,
        setBounds
    ] = useState(
        map.getBounds()
    );


    const [
        zoom,
        setZoom
    ] = useState(
        map.getZoom()
    );


    /*
     * Create the Supercluster index.
     *
     * This happens once when the dataset
     * changes, NOT every time the map moves.
     */

    const index = useMemo(() => {

        const cluster =
            new Supercluster<
                StopClusterProperties,
                StopClusterProperties
            >({

                radius: 60,

                maxZoom: 17,

                minZoom: 0,

                nodeSize: 64,

            });


        cluster.load(points);


        return cluster;

    }, [points]);


    /*
     * Update the map state when the user
     * zooms or pans.
     */

    useMapEvents({

        moveend: () => {

            setBounds(
                map.getBounds()
            );

        },

        zoomend: () => {

            setZoom(
                map.getZoom()
            );

            setBounds(
                map.getBounds()
            );

        },

    });


    /*
     * Convert Leaflet bounds into
     * Supercluster bounds.
     *
     * [west, south, east, north]
     */

    const clusters = useMemo(() => {

        if (!bounds) {
            return [];
        }


        let west =
            bounds.getWest();

        let east =
            bounds.getEast();

        const south =
            bounds.getSouth();

        const north =
            bounds.getNorth();


        /*
         * Handle the map crossing
         * the international date line.
         */

        if (west > east) {
            [west, east] =
                [east, west];
        }


        /*
         * Add a little padding around
         * the visible map.
         *
         * This prevents markers appearing
         * only at the exact edge.
         */

        const padding = 0.2;


        west -= padding;
        east += padding;


        const safeBounds: [
            number,
            number,
            number,
            number
        ] = [
            west,
            south,
            east,
            north
        ];


        return index.getClusters(
            safeBounds,
            Math.round(zoom)
        );

    }, [
        index,
        bounds,
        zoom
    ]);


    /*
     * Nothing is rendered outside
     * the relevant map area.
     */

    return (

        <>

            {clusters.map(
                (item) => {

                    const [
                        longitude,
                        latitude
                    ] =
                        item.geometry.coordinates;


                    const properties =
                        item.properties;


                    /*
                     * This is a cluster.
                     */

                    if (
                        properties.cluster
                    ) {

                        return (

                            <CircleMarker

                                key={
                                    `cluster-${
                                        properties.cluster_id
                                    }`
                                }

                                center={[
                                    latitude,
                                    longitude
                                ]}

                                radius={
                                    getClusterRadius(
                                        properties.point_count ?? 1
                                    )
                                }

                                pathOptions={{

                                    color:
                                        "white",

                                    weight:
                                        2,

                                    fillColor:
                                        "#f59e0b",

                                    fillOpacity:
                                        0.9,

                                }}

                                eventHandlers={{

                                    click: () => {

                                        if (
                                            properties.cluster_id
                                            ===
                                            undefined
                                        ) {
                                            return;
                                        }


                                        const expansionZoom =
                                            Math.min(
                                                index.getClusterExpansionZoom(
                                                    properties.cluster_id
                                                ),

                                                MAX_ZOOM
                                            );


                                        map.flyTo(
                                            [
                                                latitude,
                                                longitude
                                            ],

                                            expansionZoom,

                                            {
                                                duration:
                                                    0.5
                                            }
                                        );

                                    },

                                }}

                            >

                                <Popup>

                                    <div className="cluster-popup">

                                        <strong>

                                            {
                                                properties
                                                    .point_count
                                            }
                                            {" "}
                                            stops

                                        </strong>


                                        <p>

                                            Click to zoom
                                            into this area.

                                        </p>

                                    </div>

                                </Popup>

                            </CircleMarker>

                        );

                    }


                    /*
                     * This is an individual stop.
                     */

                    return (

                        <CircleMarker

                            key={
                                properties.stop_id ??
                                `${latitude}-${longitude}`
                            }

                            center={[
                                latitude,
                                longitude
                            ]}

                            radius={5}

                            pathOptions={{

                                color:
                                    "white",

                                weight:
                                    1,

                                fillColor:
                                    "#2563eb",

                                fillOpacity:
                                    0.85,

                            }}

                        >

                            <Popup>

                                <div className="stop-popup">

                                    <h3>

                                        {
                                            properties
                                                .stop_name ??
                                            "Unknown stop"
                                        }

                                    </h3>


                                    {
                                        properties
                                            .platform_code && (

                                            <p>

                                                Platform:{" "}
                                                {
                                                    properties
                                                        .platform_code
                                                }

                                            </p>

                                        )
                                    }


                                    {
                                        properties
                                            .stop_id && (

                                            <p className="stop-id">

                                                Stop ID:{" "}
                                                {
                                                    properties
                                                        .stop_id
                                                }

                                            </p>

                                        )
                                    }

                                </div>

                            </Popup>

                        </CircleMarker>

                    );

                }
            )}

        </>

    );

};


/*
 * Make larger clusters slightly larger.
 */

const getClusterRadius = (
    count: number
): number => {

    if (count >= 1000) {
        return 18;
    }

    if (count >= 500) {
        return 16;
    }

    if (count >= 100) {
        return 14;
    }

    if (count >= 20) {
        return 12;
    }

    return 10;
};


/*
 * Main Route Page.
 */

const RoutePage = () => {

    const [
        stops,
        setStops
    ] =
        useState<StopPoint[]>([]);


    const [
        loading,
        setLoading
    ] =
        useState(true);


    const [
        error,
        setError
    ] =
        useState<string | null>(
            null
        );


    /*
     * Load stops.
     */

    useEffect(() => {

        fetch(
            "/data/stops.geojson"
        )

            .then(
                (response) => {

                    if (!response.ok) {

                        throw new Error(
                            "Failed to load stops.geojson"
                        );

                    }

                    return response.json();

                }
            )

            .then(
                (data: StopsGeoJSON) => {

                    const points =
                        createPoints(data);


                    setStops(
                        points
                    );


                    setLoading(
                        false
                    );

                }
            )

            .catch(
                (err) => {

                    console.error(
                        err
                    );


                    setError(
                        "Could not load public transport stops."
                    );


                    setLoading(
                        false
                    );

                }
            );

    }, []);


    return (

        <div className="route-page">


            <div className="map-header">

                <div>

                    <h1>
                        Route Planner
                    </h1>

                    <p>
                        Explore public transport
                        stops and plan your journey.
                    </p>

                </div>


                {loading && (

                    <div className="map-status">

                        Loading stops...

                    </div>

                )}


                {error && (

                    <div className="map-error">

                        {error}

                    </div>

                )}

            </div>


            <div className="map-wrapper">

                <MapContainer

                    center={[
                        52.1326,
                        5.2913
                    ]}

                    zoom={8}

                    minZoom={MIN_ZOOM}

                    maxZoom={MAX_ZOOM}

                    scrollWheelZoom={true}

                    className="route-map"

                >

                    <TileLayer

                        attribution=
                            '&copy; OpenStreetMap contributors &copy; CARTO'

                        url=
                            "https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"

                    />


                    {stops.length > 0 && (

                        <StopLayer
                            points={
                                stops
                            }
                        />

                    )}

                </MapContainer>

            </div>

        </div>

    );

};


export default RoutePage;