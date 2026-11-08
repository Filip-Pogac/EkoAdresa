import type { Comparison, GeocodeResponse, Profile, ReverseResponse, Source } from './types';

export const API_URL =
  (import.meta.env.VITE_API_URL as string | undefined) ?? 'http://localhost:8000';

/** Version of the data snapshots in data/ (map layers, city heatmap). Bump it whenever those
 * files change: the URLs change with it, so browsers fetch the new data at once instead of
 * a cached copy. */
export const DATA_VERSION = '2026-11-08.2';

export interface LatLon {
  lat: number;
  lon: number;
}

/** Properties of one heatmap cell (scripts/build_heatmap.py): EkoSkor and sub-scores 0-100. */
export interface HeatmapCell {
  ekoskor: number;
  flood: number;
  noise: number;
  air: number;
  mobility: number;
  green: number;
}

export interface HeatmapCollection {
  type: 'FeatureCollection';
  features: {
    type: 'Feature';
    geometry: { type: 'Polygon'; coordinates: number[][][] };
    properties: HeatmapCell;
  }[];
}

export class ApiError extends Error {
  readonly status: number;
  readonly detail: string | null;

  constructor(status: number, detail: string | null) {
    super(`API ${status}: ${detail ?? 'error'}`);
    this.status = status;
    this.detail = detail;
  }
}

async function get<T>(
  path: string,
  params: Record<string, string | number | undefined> = {},
  signal?: AbortSignal,
): Promise<T> {
  const url = new URL(path, API_URL);
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined) url.searchParams.set(key, String(value));
  }
  const resp = await fetch(url, { signal });
  if (!resp.ok) {
    const body: unknown = await resp.json().catch(() => null);
    const detail =
      body && typeof body === 'object' && 'detail' in body && typeof body.detail === 'string'
        ? body.detail
        : null;
    throw new ApiError(resp.status, detail);
  }
  return (await resp.json()) as T;
}

export const api = {
  geocode: (q: string, signal?: AbortSignal) =>
    get<GeocodeResponse>('/api/geocode', { q, limit: 6 }, signal),
  reverse: (lat: number, lon: number, signal?: AbortSignal) =>
    get<ReverseResponse>('/api/reverse', { lat, lon }, signal),
  profile: (lat: number, lon: number, signal?: AbortSignal) =>
    get<Profile>('/api/profile', { lat, lon }, signal),
  sources: (signal?: AbortSignal) => get<Source[]>('/api/sources', {}, signal),
  compare: (a: LatLon, b: LatLon, signal?: AbortSignal) =>
    get<Comparison>(
      '/api/compare',
      { a_lat: a.lat, a_lon: a.lon, b_lat: b.lat, b_lon: b.lon },
      signal,
    ),
  heatmap: (signal?: AbortSignal) =>
    get<HeatmapCollection>('/api/heatmap', { v: DATA_VERSION }, signal),
};
