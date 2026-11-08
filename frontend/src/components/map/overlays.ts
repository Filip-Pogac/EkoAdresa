/** Map overlays: sources, styles and legend data. Colours of the WMS layers are the
 * publishers' own legends (GetLegendGraphic JSON, fetched 2026-11-05). */
import type { maplibregl } from './maplibre';
import { API_URL } from '../../api/client';

export type OverlayId =
  | 'flood'
  | 'noise'
  | 'parks'
  | 'bike_paths'
  | 'bike_stations'
  | 'air_stations'
  | 'recycling_yards'
  | 'green_islands'
  | 'stops';

export const OVERLAY_IDS: OverlayId[] = [
  'flood',
  'noise',
  'parks',
  'bike_paths',
  'bike_stations',
  'air_stations',
  'recycling_yards',
  'green_islands',
  'stops',
];

/** hv-poplave, scenario "mala vjerojatnost": fill colour per depth class. */
export const FLOOD_DEPTHS = [
  { label: '< 0,5 m', colour: '#BEE8FF' },
  { label: '0,5–1,5 m', colour: '#73DFFF' },
  { label: '1,5–2,5 m', colour: '#73B2FF' },
  { label: '> 2,5 m', colour: '#7A8EF5' },
];

/** zg-buka Lden bands. */
export const NOISE_BANDS = [
  { label: '50–54 dB', colour: '#B8D6D1' },
  { label: '55–59 dB', colour: '#E2F2BF' },
  { label: '60–64 dB', colour: '#F3C683' },
  { label: '65–69 dB', colour: '#CD463E' },
  { label: '70–74 dB', colour: '#75085C' },
  { label: '≥ 75 dB', colour: '#430A65' },
];

/** Bike paths (lines) and parks and forests (areas). Not the traffic-light colours. */
export const SHAPE_STYLE = {
  parks: { colour: '#5E9C55', opacity: 0.35 },
  bike_paths: { colour: '#2B5FA8', width: 2.5 },
} as const;

/** Point symbols. Not the traffic-light colours, which are reserved for layer status. */
export const POINT_STYLE: Record<
  Exclude<OverlayId, 'flood' | 'noise' | 'parks' | 'bike_paths'>,
  { colour: string; radius: number }
> = {
  air_stations: { colour: '#0E8C8C', radius: 8 },
  recycling_yards: { colour: '#1F7A4D', radius: 7 },
  green_islands: { colour: '#7B5EA7', radius: 4 },
  stops: { colour: '#14211A', radius: 4 },
  bike_stations: { colour: '#2B5FA8', radius: 6 }, // Bajs; same blue as the bike paths
};

const RASTER_OPACITY = 0.6;
/** [west, south, east, north], as backend/app/services/tiles.py */
const ZAGREB_BOUNDS: [number, number, number, number] = [15.77, 45.62, 16.23, 45.97];

/** Add the overlay's source and layer to the map (hidden until shown). Idempotent. */
export function addOverlay(map: maplibregl.Map, id: OverlayId, attribution: string): void {
  if (map.getSource(id)) return;
  if (id === 'flood' || id === 'noise') {
    map.addSource(id, {
      type: 'raster',
      tiles: [`${API_URL}/api/tiles/${id}/{z}/{x}/{y}.png`],
      tileSize: 256,
      minzoom: 10,
      maxzoom: 18,
      bounds: ZAGREB_BOUNDS, // the tile endpoint serves only the City of Zagreb
      attribution,
    });
    // below the radius circle so the circle stays visible
    map.addLayer(
      { id, type: 'raster', source: id, paint: { 'raster-opacity': RASTER_OPACITY } },
      'radius-fill',
    );
    return;
  }
  if (id === 'parks' || id === 'bike_paths') {
    map.addSource(id, { type: 'geojson', data: `${API_URL}/api/layers/${id}`, attribution });
    // below the radius circle and the points, like the raster layers
    if (id === 'parks')
      map.addLayer(
        {
          id,
          type: 'fill',
          source: id,
          paint: {
            'fill-color': SHAPE_STYLE.parks.colour,
            'fill-opacity': SHAPE_STYLE.parks.opacity,
          },
        },
        'radius-fill',
      );
    else
      map.addLayer(
        {
          id,
          type: 'line',
          source: id,
          paint: {
            'line-color': SHAPE_STYLE.bike_paths.colour,
            'line-width': SHAPE_STYLE.bike_paths.width,
          },
        },
        'radius-fill',
      );
    return;
  }
  const style = POINT_STYLE[id];
  map.addSource(id, { type: 'geojson', data: `${API_URL}/api/layers/${id}`, attribution });
  map.addLayer({
    id,
    type: 'circle',
    source: id,
    paint: {
      'circle-color': style.colour,
      'circle-radius': style.radius,
      'circle-stroke-color': '#FFFFFF',
      'circle-stroke-width': 1.5,
    },
  });
}
