import {
    MapContainer,
    TileLayer,
    GeoJSON,
    useMapEvents,
} from "react-leaflet";

import L from "leaflet";

import { useEffect, useState } from "react";

import "leaflet/dist/leaflet.css";
import "./RoutePage.css";


const STOP_ZOOM_LEVEL = 11;


interface StopLayerProps {
    stops: GeoJSON.GeoJsonObject;
}


const StopLayer = ({ stops }: StopLayerProps) => {

    const [showStops, setShowStops] = useState(false);


    useMapEvents({

        zoomend: (event) => {

            const zoom = event.target.getZoom();

            setShowStops(
                zoom >= STOP_ZOOM_LEVEL
            );

        },

    });


    return (

        <>
            {showStops && (

                <GeoJSON
                    data={stops}

                    pointToLayer={(_, latlng) => {

                        return L.circleMarker(
                            latlng,
                            {
                                radius: 5,
                                fillColor: "#2563eb",
                                color: "#ffffff",
                                weight: 1,
                                opacity: 1,
                                fillOpacity: 0.8,
                            }
                        );

                    }}

                    onEachFeature={(
                        feature,
                        layer
                    ) => {

                        const stopName =
                            feature.properties?.stop_name;


                        if (stopName) {

                            layer.bindPopup(
                                `<strong>${stopName}</strong>`
                            );

                        }

                    }}

                />

            )}
        </>

    );
};


const RoutePage = () => {

    const [
        stops,
        setStops
    ] = useState<GeoJSON.GeoJsonObject | null>(null);


    useEffect(() => {

        fetch("/data/stops.geojson")

            .then((response) => {

                if (!response.ok) {
                    throw new Error(
                        "Failed to load stops"
                    );
                }

                return response.json();

            })

            .then((data) => {

                setStops(data);

            })

            .catch((error) => {

                console.error(
                    "Error loading stops:",
                    error
                );

            });

    }, []);


    return (

        <div className="route-page">


            <div className="map-header">

                <h1>
                    Route Planner
                </h1>

                <p>
                    Explore public transport
                    stops and plan your journey.
                </p>

            </div>


            <div className="map-wrapper">

                <MapContainer
                    center={[
                        52.1326,
                        5.2913
                    ]}
                    zoom={8}
                    minZoom={7}
                    maxZoom={18}
                    scrollWheelZoom={true}
                    className="route-map"
                >

                    <TileLayer
                        attribution='&copy; OpenStreetMap contributors &copy; CARTO'
                        url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
                    />


                    {stops && (

                        <StopLayer
                            stops={stops}
                        />

                    )}

                </MapContainer>

            </div>

        </div>

    );
};


export default RoutePage;