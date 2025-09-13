/* eslint-env browser */
/* global L */

class SightingsMap {
    constructor(config) {
        this.mapElement = config.mapElement || 'map';
        this.centerLat = config.centerLat || 54.5;
        this.centerLng = config.centerLng || -4.0;
        this.zoomLevel = config.zoomLevel || 6;
        this.sightings = config.sightings || [];

        this.map = null;
        this.markers = [];

        this.init();
    }

    init() {
        this.initializeMap();
        this.addMarkers();
    }

    initializeMap() {
        this.map = L.map(this.mapElement, { minZoom: 6 }).setView(
            [this.centerLat, this.centerLng],
            this.zoomLevel,
        );

        L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
            maxZoom: 18,
        }).addTo(this.map);
    }

    addMarkers() {
        this.sightings.forEach((location) => {
            const marker = L.marker([location.lat, location.lng]).addTo(this.map);

            if (location.popup_html) {
                marker.bindPopup(location.popup_html);
            }

            this.markers.push({ marker, location });
        });
    }
}

window.SightingsMap = SightingsMap;
