import * as maplibregl from 'maplibre-gl';
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?url';
import { useEffect, useRef, useState } from 'react';
import { hr } from '../../i18n/hr';
import { ErrorState } from '../common/ErrorState';
import { Skeleton } from '../common/Skeleton';

// MapLibre resolves its worker relative to its own bundle, which breaks once Vite
// relocates the module (dev pre-bundling and production build). Point it at the file.
maplibregl.setWorkerUrl(workerUrl);

/** Trg bana Jelačića, EPSG:4326 [lon, lat]. */
const ZAGREB_CENTER: [number, number] = [15.9772, 45.8131];
const STYLE_URL = 'https://tiles.openfreemap.org/styles/liberty';

type MapStatus = 'loading' | 'ready' | 'error';

export function AddressMap() {
  const containerRef = useRef<HTMLDivElement>(null);
  const [status, setStatus] = useState<MapStatus>('loading');
  const [attempt, setAttempt] = useState(0);

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
    map.once('load', () => setStatus('ready'));
    map.on('error', () => {
      // Only a failed initial style load is fatal; later tile errors are tolerated.
      if (!map.isStyleLoaded()) setStatus('error');
    });
    return () => map.remove();
  }, [attempt]);

  const retry = () => {
    setStatus('loading');
    setAttempt((n) => n + 1);
  };

  return (
    <div className="relative min-h-80 w-full flex-1 overflow-hidden rounded-lg border border-border">
      {/* Outer div sizes the map: MapLibre's CSS forces `position: relative` on its own
          container. Its canvas is focusable and pans/zooms with arrow keys and +/-. */}
      <div role="region" aria-label={hr.map.label} className="absolute inset-0">
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
  );
}
