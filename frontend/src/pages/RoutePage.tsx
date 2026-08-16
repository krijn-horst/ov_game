import {
    MapContainer,
    TileLayer,
} from "react-leaflet";

import "leaflet/dist/leaflet.css";

import "./RoutePage.css";


const RoutePage = () => {

    return (
        <div className="route-page">

            <div className="map-header">

                <h1>Route Planner</h1>

                <p>
                    Explore the Netherlands and plan your journey.
                </p>

            </div>


            <div className="map-wrapper">

                <MapContainer
                    center={[52.1326, 5.2913]}
                    zoom={8}
                    scrollWheelZoom={true}
                    className="route-map"
                >

                    <TileLayer
                        attribution='&copy; OpenStreetMap contributors &copy; CARTO'
                        url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
                    />

                </MapContainer>

            </div>

        </div>
    );
};


export default RoutePage;