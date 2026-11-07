/** API response types. Mirror backend/app/models.py; keep both in sync. Coordinates EPSG:4326. */

export type Status = 'green' | 'yellow' | 'red' | 'unavailable';
export type LayerName = 'flood' | 'noise' | 'air' | 'waste' | 'mobility' | 'green';

export interface GeocodeResult {
  label: string;
  lat: number;
  lon: number;
  kind: 'address' | 'street' | 'place';
}

export interface GeocodeResponse {
  results: GeocodeResult[];
  source_id: string;
}

/** Nearest address to a map point within 150 m, else the named park or forest the point is
 * in (/api/reverse); null if neither. */
export interface ReverseResponse {
  result: {
    kind: 'address' | 'green_area';
    label: string;
    lat: number;
    lon: number;
    distance_m: number;
    source_id: string;
  } | null;
  source_id: string;
}

interface LayerBase {
  status: Exclude<Status, 'unavailable'>;
  score: number; // EkoSkor sub-score 0-100
  source_id: string;
}

interface RemoteLayer extends LayerBase {
  fetched_at: string; // ISO 8601, UTC
  stale: boolean; // service failed just now; last cached answer
}

export interface FloodLayer extends RemoteLayer {
  zone: 'high' | 'medium' | 'low' | 'none';
  depth_class: string | null;
}

export type NoiseSource = 'road' | 'tram' | 'rail' | 'industry';

export interface NoiseLayer extends RemoteLayer {
  lden_db_min: number | null; // null = no mapped band (max 49: below 50 dB)
  lden_db_max: number | null; // null = top band (≥ 75 dB)
  lnight_db_min: number | null;
  lnight_db_max: number | null;
  loudest_source: NoiseSource | null;
  facade_m: number | null; // band read this far from the point (inside a building)
}

export type Pollutant = 'no2' | 'o3' | 'pm10' | 'pm2_5';

export interface AirStation {
  id: string;
  name: string;
  station_type: string | null;
  lat: number;
  lon: number;
  distance_m: number;
  source_id: string;
}

export interface AirValue {
  pollutant: Pollutant;
  value_ug_m3: number;
  date: string; // YYYY-MM-DD
}

export interface LiveAirIndex {
  value: number;
  measured_at: string;
  distance_m: number;
  scale_verified: boolean;
  source_id: string;
}

export interface DhmzValue {
  pollutant: Pollutant;
  mean_24h_ug_m3: number;
  latest_ug_m3: number;
  latest_at_local: string; // 'YYYY-MM-DDTHH:00', local time in Croatia
  hours: number;
}

/** Last 24 h at the nearest DHMZ state station: raw, unvalidated, never scored. */
export interface DhmzReading {
  station: { name: string; lat: number; lon: number; distance_m: number };
  values: DhmzValue[];
  status: Status; // own status vs WHO 24 h guidelines, not the layer's; never scored
  validated: boolean;
  source_id: string;
}

export interface AirLayer extends LayerBase {
  station: AirStation;
  pm10_mean_ug_m3: number;
  period_from: string;
  period_to: string;
  latest: AirValue[];
  history: AirValue[];
  live_index: LiveAirIndex | null;
  dhmz: DhmzReading | null; // null if DHMZ did not answer in time
}

export interface Place {
  name: string | null;
  lat: number;
  lon: number;
  distance_m: number;
  source_id: string;
}

export interface RecyclingYard extends Place {
  address: string | null;
  opening_hours: string | null;
}

export interface GreenIsland extends Place {
  accepts: string[];
}

export interface WasteLayer extends LayerBase {
  yard: RecyclingYard;
  mobile_yard: RecyclingYard;
  island: GreenIsland;
  yard_distance_m: number;
  island_distance_m: number;
}

export interface Stop extends Place {
  type: 'bus' | 'tram';
  direction: string | null;
  lines: string[];
}

export interface BikePath extends Place {
  category: string | null; // kategorija_id as published
}

/** Public bike station (Grad Zagreb). */
export interface BikeStation extends Place {
  location: string | null;
  racks: number | null;
}

/** Park, forest, public garden or nature reserve ≥ 0.5 ha; distance 0 = address inside it. */
export interface GreenArea extends Place {
  kind: 'park' | 'forest';
  area_m2: number;
}

/** Score = 4/5 transit + 1/5 bike (docs/ekoskor.md). */
export interface MobilityLayer extends LayerBase {
  stops_300m: number;
  stops_500m: number;
  nearest_stop: Stop;
  nearest_bike_path: BikePath;
  nearest_bike_station: BikeStation; // the nearer of the two counts for the bike part
  transit_score: number;
  bike_score: number;
}

/** Zelenilo: nearest park or forest of at least 0.5 ha. */
export interface GreenLayer extends LayerBase {
  nearest: GreenArea;
}

export interface UnavailableLayer {
  status: 'unavailable';
  reason: 'timeout' | 'error';
  source_id: string;
}

export interface Layers {
  flood: FloodLayer | UnavailableLayer;
  noise: NoiseLayer | UnavailableLayer;
  air: AirLayer | UnavailableLayer;
  waste: WasteLayer | UnavailableLayer;
  mobility: MobilityLayer | UnavailableLayer;
  green: GreenLayer | UnavailableLayer;
}

export interface Profile {
  location: { lat: number; lon: number; address: string | null };
  ekoskor: number | null; // null if fewer than 3 layers are available
  layers: Layers;
  generated_at: string;
}

export interface LayerDiff {
  score_a: number | null;
  score_b: number | null;
  better: 'a' | 'b' | null;
}

export interface Comparison {
  a: Profile;
  b: Profile;
  ekoskor_diff: number | null;
  layers: Record<LayerName, LayerDiff>;
}

export interface Source {
  id: string;
  name: string;
  publisher: string;
  access: 'live' | 'snapshot';
  urls: string[];
  licence: string | null; // null = no licence stated
  data_as_of: string;
  used_for: string;
}
