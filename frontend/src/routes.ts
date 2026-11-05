/** URL helpers. The address page keeps everything in the URL, so a card can be shared. */

export function addressPath(lat: number, lon: number, label?: string): string {
  const params = new URLSearchParams({ lat: lat.toFixed(6), lon: lon.toFixed(6) });
  if (label) params.set('a', label);
  return `/adresa?${params}`;
}

/** Parse ?lat=&lon=&a= from the address page URL; null if the coordinates are invalid. */
export function parseAddressParams(params: URLSearchParams) {
  const lat = Number(params.get('lat'));
  const lon = Number(params.get('lon'));
  if (!params.get('lat') || !params.get('lon') || !Number.isFinite(lat) || !Number.isFinite(lon))
    return null;
  if (Math.abs(lat) > 90 || Math.abs(lon) > 180) return null;
  return { lat, lon, label: params.get('a') };
}
