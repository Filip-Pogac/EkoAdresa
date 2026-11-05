import * as maplibregl from 'maplibre-gl';
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?url';

// MapLibre resolves its worker relative to its own bundle, which breaks once Vite
// relocates the module (dev pre-bundling and production build). Point it at the file.
maplibregl.setWorkerUrl(workerUrl);

export { maplibregl };

/** Trg bana Jelačića, EPSG:4326 [lon, lat]. */
export const ZAGREB_CENTER: [number, number] = [15.9772, 45.8131];
export const STYLE_URL = 'https://tiles.openfreemap.org/styles/liberty';
