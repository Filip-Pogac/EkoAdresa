/** All UI strings (Croatian). Never inline strings in components. */
import type {
  AirLayer,
  FloodLayer,
  MobilityLayer,
  NoiseLayer,
  NoiseSource,
  Status,
  UnavailableLayer,
  WasteLayer,
} from '../api/types';
import { formatDate, formatDistance, formatNumber } from '../format';

const NOISE_SOURCE: Record<NoiseSource, string> = {
  road: 'cestovni promet',
  tram: 'tramvaj',
  rail: 'željeznica',
  industry: 'industrija',
};

/** Noise band as text: (null, 49) -> 'ispod 50', (75, null) -> '75 ili više', else '65–69'. */
function band(min: number | null, max: number | null): string {
  if (min === null) return `ispod ${(max ?? 49) + 1}`;
  if (max === null) return `${min} ili više`;
  return `${min}–${max}`;
}

const stopsWord = (n: number) => (n % 10 === 1 && n % 100 !== 11 ? 'stajalište' : 'stajališta');

export const hr = {
  app: {
    name: 'EkoAdresa',
    tagline: 'Kako je živjeti na ovoj adresi?',
    home: 'EkoAdresa – početna',
    pilot: 'Pilot područje: Grad Zagreb',
  },
  map: {
    label: 'Karta Zagreba',
    loading: 'Učitavanje karte…',
    error: 'Karta se trenutno ne može učitati. Ostali podaci i dalje rade.',
    retry: 'Pokušaj ponovno',
    radius: 'Krug od 500 m oko adrese',
    layersTitle: 'Slojevi na karti',
    overlays: {
      flood: 'Poplave',
      noise: 'Buka',
      air_stations: 'Mjerne postaje zraka',
      recycling_yards: 'Reciklažna dvorišta',
      green_islands: 'Zeleni otoci',
      stops: 'Stajališta ZET-a',
    },
    attribution: {
      flood: 'Hrvatske vode',
      noise: 'Grad Zagreb',
      air_stations: 'Grad Zagreb',
      recycling_yards: 'Grad Zagreb',
      green_islands: '© OpenStreetMap contributors',
      stops: 'Grad Zagreb, ZET',
    },
    legend: {
      flood: 'Poplave, scenarij male vjerojatnosti (najveći obuhvat). Boja je dubina vode:',
      noise:
        'Buka Lden, svi izvori. Gdje se izvori preklapaju, karta crta jedan od njih; kartica adrese uzima najglasniji.',
    },
    overlayError: (name: string) => `${name}: dio sloja trenutno se ne može učitati.`,
    popup: {
      station: (name: string, type: string | null) =>
        type ? `${name} (${type.toLowerCase()} postaja)` : name,
      yard: (name: string, mobile: boolean, hours: string | null) =>
        [name, mobile ? 'mobilno dvorište' : null, hours].filter(Boolean).join(' · '),
      island: 'Zeleni otok',
      stop: (name: string | null, lines: string[]) =>
        `${name ?? 'Stajalište'}${lines.length ? ` · ${lines.length === 1 ? 'linija' : 'linije'} ${lines.join(', ')}` : ''}`,
    },
  },
  search: {
    label: 'Upišite adresu u Zagrebu',
    placeholder: 'npr. Ilica 1',
    hint: 'Upišite barem 3 znaka.',
    loading: 'Tražim adrese…',
    empty: 'Nema adresa za taj upit. Pokušajte s nazivom ulice.',
    error: 'Pretraga trenutno ne radi. Pokušajte ponovno za trenutak.',
    results: (n: number) => `${n} ${n === 1 ? 'prijedlog' : 'prijedloga'}`,
    kind: { address: 'adresa', street: 'ulica', place: 'naselje' },
  },
  examples: {
    title: 'Ili isprobajte primjer',
    items: [
      { label: 'Trg bana Josipa Jelačića 6', note: 'Centar', lat: 45.813406, lon: 15.977322 },
      {
        label: 'Ulica Vladimira Ruždjaka 20',
        note: 'Savica, uz Savu',
        lat: 45.790284,
        lon: 15.994318,
      },
      { label: 'Sljemenska cesta 8', note: 'Sljeme', lat: 45.899054, lon: 15.947436 },
    ],
  },
  card: {
    title: 'Okolišni profil',
    loading: 'Učitavanje profila adrese…',
    error: 'Profil adrese trenutno se ne može učitati.',
    outside: 'Ova je točka izvan Grada Zagreba. EkoAdresa za sada pokriva samo Zagreb.',
    retry: 'Pokušaj ponovno',
    newSearch: 'Nova pretraga',
    pinnedPoint: 'Odabrana točka na karti',
  },
  ekoskor: {
    name: 'EkoSkor',
    outOf: 'od 100',
    aria: (score: number) => `EkoSkor ${score} od 100`,
    missing: 'Premalo dostupnih slojeva za EkoSkor (potrebna su barem 3 od 5).',
    explain: 'Ponderirani prosjek pet slojeva ispod.',
  },
  status: {
    green: 'Dobro',
    yellow: 'Umjereno',
    red: 'Loše',
    unavailable: 'Nedostupno',
  } satisfies Record<Status, string>,
  source: {
    prefix: 'Izvor:',
    stale: (iso: string) =>
      `Servis ne odgovara; prikazan zadnji spremljeni podatak od ${formatDate(iso)}.`,
  },
  layers: {
    flood: {
      title: 'Poplave',
      sentence: (l: FloodLayer) => {
        if (l.zone === 'none') return 'Adresa je izvan svih zona opasnosti od poplava.';
        const zone = {
          low: 'male vjerojatnosti',
          medium: 'srednje vjerojatnosti (poplava jednom u 100 godina)',
          high: 'velike vjerojatnosti',
        }[l.zone];
        const depth = l.depth_class ? `, ${l.depth_class}` : '';
        return `Adresa je u zoni opasnosti od poplava ${zone}${depth}.`;
      },
    },
    noise: {
      title: 'Buka',
      sentence: (l: NoiseLayer) => {
        if (l.lden_db_min === null)
          return `Buka je ${band(null, l.lden_db_max)} dB, ispod najniže razine na karti buke.`;
        const night = `noću ${band(l.lnight_db_min, l.lnight_db_max)} dB (SZO: do 45)`;
        const source = l.loudest_source
          ? ` Najglasniji izvor: ${NOISE_SOURCE[l.loudest_source]}.`
          : '';
        const facade = l.facade_m ? ' Očitano uz pročelje zgrade.' : '';
        return `Cjelodnevna buka ${band(l.lden_db_min, l.lden_db_max)} dB (SZO: do 53), ${night}.${source}${facade}`;
      },
    },
    air: {
      title: 'Zrak',
      sentence: (l: AirLayer) =>
        `Postaja ${l.station.name} (${formatDistance(l.station.distance_m)}): prosjek PM10 ${formatNumber(l.pm10_mean_ug_m3)} µg/m³ (SZO: do 15).`,
      period: (l: AirLayer) =>
        `Prosjek dnevnih mjerenja od ${formatDate(l.period_from)} do ${formatDate(l.period_to)}`,
    },
    waste: {
      title: 'Otpad',
      sentence: (l: WasteLayer) =>
        `Reciklažno dvorište ${formatDistance(l.yard_distance_m)}, zeleni otok ${formatDistance(l.island_distance_m)} (zračnom linijom).`,
      period: () => 'Reciklažna dvorišta: podaci iz 2022. Zeleni otoci: OpenStreetMap.',
    },
    mobility: {
      title: 'Zelena mobilnost',
      sentence: (l: MobilityLayer) => {
        const near = `${l.stops_300m} ${stopsWord(l.stops_300m)} ZET-a do 300 m, ${l.stops_500m} do 500 m.`;
        const name = l.nearest_stop.name ?? '';
        return `${near} Najbliže: ${name} (${formatDistance(l.nearest_stop.distance_m)}).`;
      },
    },
    unavailable: (l: UnavailableLayer) =>
      l.reason === 'timeout'
        ? 'Servis nije odgovorio na vrijeme. Ostali slojevi su prikazani.'
        : 'Podaci trenutno nisu dostupni. Ostali slojevi su prikazani.',
  },
} as const;
