/** URL helpers. Pages keep their state in the URL, so every view can be shared. */

export interface Place {
  lat: number;
  lon: number;
  label: string | null;
}

export function addressPath(lat: number, lon: number, label?: string): string {
  const params = new URLSearchParams({ lat: lat.toFixed(6), lon: lon.toFixed(6) });
  if (label) params.set('a', label);
  return `/adresa?${params}`;
}

function parsePlace(params: URLSearchParams, prefix: string, labelKey: string): Place | null {
  const rawLat = params.get(`${prefix}lat`);
  const rawLon = params.get(`${prefix}lon`);
  if (!rawLat || !rawLon) return null;
  const lat = Number(rawLat);
  const lon = Number(rawLon);
  if (!Number.isFinite(lat) || !Number.isFinite(lon)) return null;
  if (Math.abs(lat) > 90 || Math.abs(lon) > 180) return null;
  return { lat, lon, label: params.get(labelKey) };
}

/** Parse ?lat=&lon=&a= from the address page URL; null if the coordinates are invalid. */
export function parseAddressParams(params: URLSearchParams): Place | null {
  return parsePlace(params, '', 'a');
}

/** /usporedba?a_lat=&a_lon=&a=&b_lat=&b_lon=&b= ; either side may be missing. */
export function comparePath(a: Place | null, b: Place | null): string {
  const params = new URLSearchParams();
  for (const [key, place] of [
    ['a', a],
    ['b', b],
  ] as const) {
    if (!place) continue;
    params.set(`${key}_lat`, place.lat.toFixed(6));
    params.set(`${key}_lon`, place.lon.toFixed(6));
    if (place.label) params.set(key, place.label);
  }
  const query = params.toString();
  return query ? `/usporedba?${query}` : '/usporedba';
}

export function parseCompareParams(params: URLSearchParams) {
  return { a: parsePlace(params, 'a_', 'a'), b: parsePlace(params, 'b_', 'b') };
}
