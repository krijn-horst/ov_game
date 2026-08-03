import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import "./RoutePage.css";

import markerIcon2x from "leaflet/dist/images/marker-icon-2x.png";
import markerIcon from "leaflet/dist/images/marker-icon.png";
import markerShadow from "leaflet/dist/images/marker-shadow.png";

delete (L.Icon.Default.prototype as any)._getIconUrl;

L.Icon.Default.mergeOptions({
    iconRetinaUrl: markerIcon2x,
    iconUrl: markerIcon,
    shadowUrl: markerShadow,
});

const RoutePage = () => {

    // Utrecht Centraal
    const center: [number, number] = [52.0894, 5.1100];

    return (
        <div className="route-page">

            <h1>Route Planner</h1>

            <MapContainer
                center={center}
                zoom={13}
                scrollWheelZoom={true}
                className="map"
            >
                <TileLayer
                    attribution="&copy; OpenStreetMap contributors"
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                />

                <Marker position={center}>
                    <Popup>
                        Utrecht Centraal 🚆
                    </Popup>
                </Marker>

            </MapContainer>

        </div>
    );
};

export default RoutePage;