import { useEffect, useState } from "react";
import { MapContainer, TileLayer, GeoJSON, useMap } from "react-leaflet";
import MarkerClusterGroup from "react-leaflet-cluster";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import "leaflet.markercluster/dist/MarkerCluster.css";
import "leaflet.markercluster/dist/MarkerCluster.Default.css";
import "./RoutePage.css";
import "leaflet.markercluster";
import type { Feature, Geometry } from "geojson";
import type { LatLng, Layer } from "leaflet";


interface StopProperties {
  stop_id: string;
  stop_name: string;
  platform_code: string | null;
  zone_id: string | null;
}

const stopIcon = L.divIcon({
  className: "",
  html: '<div class="stop-dot"></div>',
  iconSize: [12, 12],
  iconAnchor: [6, 6],
});

const createClusterIcon = (cluster: L.MarkerCluster) => {
  const count = cluster.getChildCount();
  return L.divIcon({
    html: `<div>${count}</div>`,
    className: "marker-cluster-custom",
    iconSize: L.point(40, 40),
  });
};

// Dwingt Leaflet om zijn afmetingen opnieuw te berekenen
// zodra de container zijn definitieve grootte heeft.
const MapResizeFix = () => {
  const map = useMap();

  useEffect(() => {
    const invalidate = () => map.invalidateSize();

    // direct na mount (na de eerste render/layout pass)
    const timeout = setTimeout(invalidate, 0);

    // en bij elke resize van het venster
    window.addEventListener("resize", invalidate);

    // en bij resize van de container zelf (bv. sidebar toggle, layout shift)
    const container = map.getContainer();
    const resizeObserver = new ResizeObserver(invalidate);
    resizeObserver.observe(container);

    return () => {
      clearTimeout(timeout);
      window.removeEventListener("resize", invalidate);
      resizeObserver.disconnect();
    };
  }, [map]);

  return null;
};

const RoutePage = () => {
  const center: [number, number] = [52.0894, 5.11];
  const [geoData, setGeoData] = useState<GeoJSON.FeatureCollection | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch("/data/stops.geojson")
      .then((r) => {
        if (!r.ok) throw new Error(`Kon stops.geojson niet laden (${r.status})`);
        return r.json();
      })
      .then(setGeoData)
      .catch((e) => setError(e.message));
  }, []);

  return (
    <div className="route-page">
      <h1>Route Planner</h1>

      {error && <div className="map-error">{error}</div>}

      <MapContainer center={center} zoom={13} scrollWheelZoom={true} className="map">
        <MapResizeFix />

        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
          url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
          subdomains="abcd"
          maxZoom={20}
        />

        {geoData && (
          <MarkerClusterGroup
            chunkedLoading
            maxClusterRadius={50}
            disableClusteringAtZoom={15}
            iconCreateFunction={createClusterIcon}
          >
            <GeoJSON
                data={geoData}
                pointToLayer={(feature: Feature<Geometry, StopProperties>, latlng: LatLng): Layer =>
                    L.marker(latlng, { icon: stopIcon }).bindPopup(
                    popupHtml(feature.properties)
                    )
                }
                />
          </MarkerClusterGroup>
        )}
      </MapContainer>
    </div>
  );
};

function popupHtml(props: StopProperties) {
  return `
    <div class="stop-popup">
      <div class="name">${props.stop_name ?? "Onbekende halte"}</div>
      <div class="row"><span>Stop ID</span><span>${props.stop_id ?? "-"}</span></div>
      ${props.platform_code ? `<div class="row"><span>Perron</span><span>${props.platform_code}</span></div>` : ""}
      ${props.zone_id ? `<div class="row"><span>Zone</span><span>${props.zone_id}</span></div>` : ""}
    </div>
  `;
}

export default RoutePage;