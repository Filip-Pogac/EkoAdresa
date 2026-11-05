import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router';
import type { HeatmapCell, HeatmapCollection } from '../../api/client';
import { hr } from '../../i18n/hr';
import { addressPath } from '../../routes';
import { ErrorState } from '../common/ErrorState';
import { Skeleton } from '../common/Skeleton';
import { maplibregl, STYLE_URL, ZAGREB_CENTER } from '../map/maplibre';
import { FILL_COLOUR } from './heatmapClasses';

function popupContent(cell: HeatmapCell, onOpen: () => void): HTMLElement {
  const root = document.createElement('div');
  const score = document.createElement('p');
  score.style.fontWeight = '700';
  score.textContent = hr.city.popup(cell.ekoskor);
  const layers = document.createElement('p');
  layers.textContent = hr.city.popupLayers(cell);
  const button = document.createElement('button');
  button.type = 'button';
  button.textContent = hr.city.openProfile;
  button.style.textDecoration = 'underline';
  button.style.fontWeight = '600';
  button.style.minHeight = '48px';
  button.addEventListener('click', onOpen);
  root.append(score, layers, button);
  return root;
}

export function HeatmapView({ data }: { data: HeatmapCollection }) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [status, setStatus] = useState<'loading' | 'ready' | 'error'>('loading');
  const [attempt, setAttempt] = useState(0);
  const navigate = useNavigate();

  useEffect(() => {
    if (!containerRef.current) return;
    const map = new maplibregl.Map({
      container: containerRef.current,
      style: STYLE_URL,
      center: ZAGREB_CENTER,
      zoom: 10,
      attributionControl: { compact: true },
    });
    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'top-right');
    map.once('load', () => {
      map.addSource('heatmap', {
        type: 'geojson',
        data: data as unknown as maplibregl.GeoJSONSourceSpecification['data'], // reason: same shape, local type
        attribution: 'EkoAdresa (docs/ekoskor.md)',
      });
      // under the base map's labels, so street names stay readable
      const firstSymbol = map.getStyle().layers.find((l) => l.type === 'symbol')?.id;
      map.addLayer(
        {
          id: 'heatmap',
          type: 'fill',
          source: 'heatmap',
          paint: { 'fill-color': FILL_COLOUR, 'fill-opacity': 0.7 },
        },
        firstSymbol,
      );
      map.on('click', 'heatmap', (e) => {
        const feature = e.features?.[0];
        if (!feature) return;
        const cell = feature.properties as HeatmapCell;
        const { lng, lat } = e.lngLat;
        const popup = new maplibregl.Popup({ maxWidth: '280px' }).setLngLat(e.lngLat);
        popup
          .setDOMContent(
            popupContent(cell, () => {
              popup.remove();
              navigate(addressPath(lat, lng));
            }),
          )
          .addTo(map);
      });
      map.on('mouseenter', 'heatmap', () => (map.getCanvas().style.cursor = 'pointer'));
      map.on('mouseleave', 'heatmap', () => (map.getCanvas().style.cursor = ''));
      setStatus('ready');
    });
    map.on('error', () => {
      if (!map.isStyleLoaded()) setStatus('error');
    });
    return () => map.remove();
  }, [attempt, data, navigate]);

  return (
    <div className="relative h-[70dvh] min-h-96 w-full overflow-hidden rounded-lg border border-border">
      <div role="region" aria-label={hr.city.title} className="absolute inset-0">
        <div ref={containerRef} className="h-full w-full" />
      </div>
      {status === 'loading' && (
        <Skeleton label={hr.city.loading} className="absolute inset-0 rounded-none" />
      )}
      {status === 'error' && (
        <div className="absolute inset-0">
          <ErrorState
            message={hr.city.error}
            retryLabel={hr.city.retry}
            onRetry={() => {
              setStatus('loading');
              setAttempt((n) => n + 1);
            }}
          />
        </div>
      )}
    </div>
  );
}
