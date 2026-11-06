import { useEffect, useRef, useState } from 'react';
import { hr } from '../../i18n/hr';
import { ErrorState } from '../common/ErrorState';
import { Skeleton } from '../common/Skeleton';
import { LayerToggle } from './LayerToggle';
import { Legend } from './Legend';
import { maplibregl, STYLE_URL, ZAGREB_CENTER } from './maplibre';
import { addOverlay, type OverlayId } from './overlays';

type MapStatus = 'loading' | 'ready' | 'error';

const RADIUS_M = 500;
const M_PER_DEG_LAT = 111_320;

/** Circle of `radiusM` around [lon, lat] as a GeoJSON polygon (EPSG:4326, 64 vertices). */
function circle([lon, lat]: [number, number], radiusM: number) {
  const dLat = radiusM / M_PER_DEG_LAT;
  const dLon = radiusM / (M_PER_DEG_LAT * Math.cos((lat * Math.PI) / 180));
  const ring = Array.from({ length: 65 }, (_, i): [number, number] => {
    const a = (2 * Math.PI * i) / 64;
    return [lon + dLon * Math.sin(a), lat + dLat * Math.cos(a)];
  });
  return {
    type: 'Feature' as const,
    properties: {},
    geometry: { type: 'Polygon' as const, coordinates: [ring] },
  };
}

const OVERLAY_SOURCE_IDS = new Set<string>([
  'flood',
  'noise',
  'parks',
  'bike_paths',
  'air_stations',
  'recycling_yards',
  'green_islands',
  'stops',
]);

const POINT_LAYER_IDS: OverlayId[] = ['air_stations', 'recycling_yards', 'green_islands', 'stops'];

/** MapLibre turns array properties into JSON strings. */
function stringList(value: unknown): string[] {
  if (Array.isArray(value)) return value.map(String);
  if (typeof value !== 'string') return [];
  try {
    const parsed: unknown = JSON.parse(value);
    return Array.isArray(parsed) ? parsed.map(String) : [];
  } catch {
    return [];
  }
}

function popupText(id: OverlayId, p: Record<string, unknown>): string {
  const str = (v: unknown) => (typeof v === 'string' ? v : null);
  switch (id) {
    case 'air_stations':
      return hr.map.popup.station(str(p.name) ?? '', str(p.station_type));
    case 'recycling_yards':
      return hr.map.popup.yard(str(p.name) ?? '', p.kind === 'mobile', str(p.opening_hours));
    case 'stops':
      return hr.map.popup.stop(str(p.name), stringList(p.lines));
    default:
      return hr.map.popup.island;
  }
}

function showPopup(map: maplibregl.Map, id: OverlayId, e: maplibregl.MapLayerMouseEvent) {
  const feature = e.features?.[0];
  if (!feature) return;
  // setText, not setHTML: names come from data files
  new maplibregl.Popup({ closeButton: true, maxWidth: '260px' })
    .setLngLat(e.lngLat)
    .setText(popupText(id, feature.properties))
    .addTo(map);
}

interface AddressMapProps {
  /** Address to mark, EPSG:4326. Without it the map shows Zagreb. */
  point?: { lat: number; lon: number };
  /** Called with a clicked point (EPSG:4326), except when a map point with a popup is hit. */
  onPick?: (lat: number, lon: number) => void;
}

export function AddressMap({ point, onPick }: AddressMapProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  // The click handler is registered once per map; it reads the latest callback from here.
  const onPickRef = useRef(onPick);
  useEffect(() => {
    onPickRef.current = onPick;
  }, [onPick]);
  const [status, setStatus] = useState<MapStatus>('loading');
  const [attempt, setAttempt] = useState(0);
  const [active, setActive] = useState<Set<OverlayId>>(new Set());
  const [failed, setFailed] = useState<Set<OverlayId>>(new Set());

  useEffect(() => {
    if (!containerRef.current) return;
    const map = new maplibregl.Map({
      container: containerRef.current,
      style: STYLE_URL,
      center: ZAGREB_CENTER,
      zoom: 12,
      attributionControl: { compact: true },
    });
    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'top-right');
    map.once('load', () => {
      map.addSource('radius', {
        type: 'geojson',
        data: { type: 'FeatureCollection', features: [] },
      });
      map.addLayer({
        id: 'radius-fill',
        type: 'fill',
        source: 'radius',
        paint: { 'fill-color': '#0e8c8c', 'fill-opacity': 0.08 },
      });
      map.addLayer({
        id: 'radius-line',
        type: 'line',
        source: 'radius',
        paint: { 'line-color': '#0e8c8c', 'line-width': 2, 'line-dasharray': [2, 2] },
      });
      map.on('click', (e) => {
        // A click on a stop, yard, station or green island opens its popup instead
        const pointLayers = POINT_LAYER_IDS.filter((id) => map.getLayer(id));
        if (
          pointLayers.length &&
          map.queryRenderedFeatures(e.point, { layers: pointLayers }).length
        )
          return;
        onPickRef.current?.(e.lngLat.lat, e.lngLat.lng);
      });
      mapRef.current = map;
      setStatus('ready');
    });
    map.on('error', (e: maplibregl.ErrorEvent & { sourceId?: string }) => {
      // A failed initial style load is fatal. A failed overlay is reported under the map;
      // other tile errors (base map) are tolerated.
      if (e.sourceId && OVERLAY_SOURCE_IDS.has(e.sourceId)) {
        const id = e.sourceId as OverlayId;
        setFailed((prev) => (prev.has(id) ? prev : new Set(prev).add(id)));
      } else if (!map.isStyleLoaded()) setStatus('error');
    });
    return () => {
      mapRef.current = null;
      map.remove();
    };
  }, [attempt]);

  const lat = point?.lat;
  const lon = point?.lon;
  useEffect(() => {
    const map = mapRef.current;
    if (status !== 'ready' || !map || lat === undefined || lon === undefined) return;
    const lonLat: [number, number] = [lon, lat];
    const marker = new maplibregl.Marker({ color: '#1f7a4d' }).setLngLat(lonLat).addTo(map);
    (map.getSource('radius') as maplibregl.GeoJSONSource).setData(circle(lonLat, RADIUS_M));
    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    map.easeTo({ center: lonLat, zoom: 15, duration: reduceMotion ? 0 : 250 });
    return () => {
      marker.remove();
    };
  }, [status, lat, lon]);

  useEffect(() => {
    const map = mapRef.current;
    if (status !== 'ready' || !map) return;
    for (const id of active) {
      if (!map.getSource(id)) {
        addOverlay(map, id, hr.map.attribution[id]);
        // Popups only for points; a click on a park or bike path still picks that point
        if (POINT_LAYER_IDS.includes(id)) map.on('click', id, (e) => showPopup(map, id, e));
      }
    }
    for (const layer of OVERLAY_SOURCE_IDS) {
      if (map.getLayer(layer))
        map.setLayoutProperty(
          layer,
          'visibility',
          active.has(layer as OverlayId) ? 'visible' : 'none',
        );
    }
  }, [status, active]);

  const toggle = (id: OverlayId) => {
    setActive((prev) => {
      const next = new Set(prev);
      if (!next.delete(id)) next.add(id);
      return next;
    });
    setFailed((prev) => {
      const next = new Set(prev);
      next.delete(id); // retried when shown again
      return next;
    });
  };

  const retry = () => {
    setStatus('loading');
    setAttempt((n) => n + 1);
  };

  return (
    <div className="flex w-full flex-1 flex-col gap-3">
      <div className="relative h-80 w-full overflow-hidden rounded-lg border border-border lg:h-[60dvh]">
        {/* Outer div sizes the map: MapLibre's CSS forces `position: relative` on its own
            container. Its canvas is focusable and pans/zooms with arrow keys and +/-. */}
        <div
          role="region"
          aria-label={[hr.map.label, point && hr.map.radius, onPick && hr.map.clickHint]
            .filter(Boolean)
            .join('. ')}
          className="absolute inset-0"
        >
          <div ref={containerRef} className="h-full w-full" />
        </div>
        {status === 'loading' && (
          <Skeleton label={hr.map.loading} className="absolute inset-0 rounded-none" />
        )}
        {status === 'error' && (
          <div className="absolute inset-0">
            <ErrorState message={hr.map.error} retryLabel={hr.map.retry} onRetry={retry} />
          </div>
        )}
      </div>
      {status !== 'error' && (
        <>
          {onPick && <p className="text-sm text-ink-muted">{hr.map.clickHint}</p>}
          <LayerToggle active={active} failed={failed} onToggle={toggle} />
          <Legend active={active} />
        </>
      )}
    </div>
  );
}
