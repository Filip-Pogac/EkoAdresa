/** All UI strings (Croatian). Never inline strings in components. */
import type {
  AirLayer,
  DhmzReading,
  FloodLayer,
  GreenLayer,
  MobilityLayer,
  NoiseLayer,
  NoiseSource,
  Pollutant,
  Status,
  UnavailableLayer,
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
    mapTitle: 'Ili odaberite točku na karti',
    showMap: 'Prikaži kartu Zagreba',
  },
  nav: {
    label: 'Glavna navigacija',
    compare: 'Usporedi',
    city: 'Za grad',
    sources: 'Izvori',
    howWeScore: 'Kako računamo?',
  },
  compare: {
    title: 'Usporedba dviju adresa',
    intro: 'Odaberite dvije adrese i pogledajte po čemu se razlikuju.',
    start: 'Usporedi s drugom adresom',
    slot: { a: 'Adresa A', b: 'Adresa B' },
    searchLabel: { a: 'Prva adresa', b: 'Druga adresa' },
    change: 'Promijeni',
    loading: 'Uspoređujem adrese…',
    error: 'Usporedba se trenutno ne može učitati.',
    outside: (slot: string) =>
      `${slot} je izvan Grada Zagreba. EkoAdresa za sada pokriva samo Zagreb.`,
    better: 'Bolje',
    same: 'Jednaka ocjena',
    notCompared: 'Nije moguće usporediti: sloj nije dostupan za obje adrese.',
    ekoskorDiff: (diff: number | null, a: string, b: string) => {
      if (diff === null) return 'EkoSkor nije dostupan za obje adrese.';
      if (diff === 0) return 'Obje adrese imaju jednak EkoSkor.';
      const n = Math.abs(diff);
      const word =
        n % 10 === 1 && n % 100 !== 11
          ? 'bod'
          : [2, 3, 4].includes(n % 10) && ![12, 13, 14].includes(n % 100)
            ? 'boda'
            : 'bodova';
      return `${diff > 0 ? b : a} ima EkoSkor viši za ${n} ${word}.`;
    },
    layersTitle: 'Razlike po slojevima',
  },
  howWeScore: {
    title: 'Kako računamo EkoSkor?',
    close: 'Zatvori',
    intro:
      'EkoSkor je broj od 0 do 100. Svaki od pet slojeva dobiva ocjenu od 0 do 100, a EkoSkor je njihov ponderirani prosjek, zaokružen na cijeli broj. Ocjene slojeva prikazane su na kartici, pa EkoSkor svatko može sam izračunati.',
    tableCaption: 'Ponder i pragovi po slojevima',
    columns: {
      layer: 'Sloj',
      weight: 'Ponder',
      best: '100 bodova',
      mid: '50 bodova',
      worst: '0 bodova',
    },
    rows: [
      {
        layer: 'Poplave',
        weight: '20 %',
        best: 'izvan svih zona opasnosti',
        mid: 'zona male vjerojatnosti',
        worst: 'zona srednje ili velike vjerojatnosti',
      },
      {
        layer: 'Buka (Lden, najglasniji izvor)',
        weight: '20 %',
        best: 'do 53 dB (smjernica SZO)',
        mid: '54–64 dB',
        worst: '65 dB ili više',
      },
      {
        layer: 'Zrak (PM10, najbliža gradska postaja, sij.–kol. 2023.)',
        weight: '20 %',
        best: 'do 15 µg/m³ (smjernica SZO)',
        mid: '27,5 µg/m³ (linearno)',
        worst: '40 µg/m³ ili više (granica EU)',
      },
      {
        layer: 'Zelena mobilnost: javni prijevoz (4/5 sloja), perona ZET-a',
        weight: '20 %',
        best: '3 ili više do 300 m',
        mid: 'barem jedan do 500 m',
        worst: 'nijedan do 500 m',
      },
      {
        layer: 'Zelena mobilnost: bicikl (1/5 sloja), najbliža staza ili stanica javnih bicikala',
        weight: '',
        best: 'do 200 m',
        mid: '600 m (linearno)',
        worst: '1 km ili dalje',
      },
      {
        layer: 'Zelenilo: najbliži park ili šuma od barem 0,5 ha',
        weight: '20 %',
        best: 'do 300 m (preporuka SZO-a za Europu) ili unutar njega',
        mid: '650 m (linearno)',
        worst: '1 km ili dalje',
      },
    ],
    lightsTitle: 'Semafor po sloju',
    lights: 'Dobro: ocjena 67–100. Umjereno: 34–66. Loše: 0–33. Uz boju je uvijek i tekst i ikona.',
    rulesTitle: 'Pravila',
    rules: [
      'Buka: ako je točka unutar zgrade, gdje karta buke nema vrijednosti, uzima se najglasnija vrijednost do 15 m oko točke (ili do 30 m), kao pročelje zgrade najizloženije buci (Direktiva 2002/49/EZ).',
      'Ako sloj nije dostupan, izostavlja se, a ponderi ostalih slojeva preračunavaju se na 100 %. Uz manje od 3 dostupna sloja EkoSkor se ne računa.',
      'Udaljenosti su zračne, ne pješačke rute.',
    ],
    limitsTitle: 'Ograničenja',
    limits: [
      'Karte buke i poplava strateške su karte na razini grada; pojedina zgrada može odstupati.',
      'Zrak opisuje najbližu od 6 gradskih postaja, ne zrak točno na adresi, i podaci su iz 2023.',
      'Parkovi i šume su iz OpenStreetMapa i popis možda nije potpun. Biciklističke staze su gradski podaci iz 2022.',
      'EkoSkor je orijentacija, a ne stručna procjena ni pravni, osiguravateljni ili savjet o nekretninama.',
    ],
    sourcesLink: 'Svi izvori podataka',
  },
  sources: {
    title: 'Izvori podataka',
    intro:
      'Svi podaci u EkoAdresi dolaze iz javno objavljenih skupova podataka. Licencija je navedena onako kako ju je naveo izdavač.',
    loading: 'Učitavanje popisa izvora…',
    error: 'Popis izvora trenutno se ne može učitati.',
    retry: 'Pokušaj ponovno',
    publisher: 'Izdavač',
    licence: 'Licencija',
    noLicence: 'nije navedena u metapodacima',
    dataAsOf: 'Datum podataka',
    usedFor: 'Koristimo za',
    access: {
      live: 'Upit javnom servisu; odgovor se privremeno sprema',
      snapshot: 'Spremljena snimka podataka',
    },
    links: 'Poveznice',
  },
  city: {
    title: 'EkoSkor za cijeli Zagreb',
    intro:
      'Isti izračun kao na kartici adrese, na mreži ćelija 250 × 250 m. Svaka ćelija prikazuje vrijednost u svom središtu. Kliknite na ćeliju za detalje.',
    loading: 'Učitavanje karte grada…',
    error: 'Karta grada trenutno se ne može učitati.',
    retry: 'Pokušaj ponovno',
    legend: 'EkoSkor ćelije',
    noteNoise:
      'Napomena: karta grada za buku još ne primjenjuje pravilo pročelja zgrade, pa ćelije sa središtem unutar zgrade mogu izgledati tiše. Kartica adrese ga primjenjuje.',
    noPopulation: 'Podaci o broju stanovnika po ćeliji nisu dostupni, pa ih ne prikazujemo.',
    popup: (score: number) => `EkoSkor ${score}`,
    popupLayers: (s: Record<'flood' | 'noise' | 'air' | 'mobility' | 'green', number>) =>
      `Poplave ${s.flood} · Buka ${s.noise} · Zrak ${s.air} · Mobilnost ${s.mobility} · Zelenilo ${s.green}`,
    openProfile: 'Otvori profil ove točke',
  },
  map: {
    label: 'Karta Zagreba',
    loading: 'Učitavanje karte…',
    error: 'Karta se trenutno ne može učitati. Ostali podaci i dalje rade.',
    retry: 'Pokušaj ponovno',
    radius: 'Krug od 500 m oko adrese',
    clickHint: 'Kliknite bilo gdje na karti za EkoSkor te točke.',
    layersTitle: 'Slojevi na karti',
    overlays: {
      flood: 'Poplave',
      noise: 'Buka',
      parks: 'Parkovi i šume',
      bike_paths: 'Biciklističke staze',
      bike_stations: 'Stanice javnih bicikala',
      bike_parking: 'Parkirališta za bicikle',
      air_stations: 'Mjerne postaje zraka',
      recycling_yards: 'Reciklažna dvorišta',
      green_islands: 'Zeleni otoci',
      stops: 'Stajališta ZET-a',
    },
    attribution: {
      flood: 'Hrvatske vode',
      noise: 'Grad Zagreb',
      parks: '© OpenStreetMap contributors',
      bike_paths: 'Grad Zagreb',
      bike_stations: 'Grad Zagreb',
      bike_parking: 'Grad Zagreb',
      air_stations: 'Grad Zagreb',
      recycling_yards: 'Grad Zagreb',
      green_islands: '© OpenStreetMap contributors',
      stops: 'Grad Zagreb, ZET',
    },
    legend: {
      flood: 'Poplave, scenarij male vjerojatnosti (najveći obuhvat). Boja je dubina vode:',
      noise:
        'Buka Lden, svi izvori. Gdje se izvori preklapaju, karta crta jedan od njih; kartica adrese uzima najglasniji.',
      parks: 'Parkovi, šume, javni vrtovi i zaštićena područja od barem 0,5 ha',
    },
    overlayError: (name: string) => `${name}: dio sloja trenutno se ne može učitati.`,
    popup: {
      station: (name: string, type: string | null) =>
        type ? `${name} (${type.toLowerCase()} postaja)` : name,
      yard: (name: string, mobile: boolean, hours: string | null) =>
        [name, mobile ? 'mobilno dvorište' : null, hours].filter(Boolean).join(' · '),
      island: 'Zeleni otok',
      bikeStation: (name: string | null, racks: unknown, location: string | null) =>
        [
          name ?? 'Stanica javnih bicikala',
          typeof racks === 'number' ? `${racks} stalaka` : null,
          location,
        ]
          .filter(Boolean)
          .join(' · '),
      bikeParking: (name: string | null, racks: unknown, location: string | null) =>
        [
          name ?? 'Parkiralište za bicikle',
          typeof racks === 'number' ? `${racks} mjesta` : null,
          location,
        ]
          .filter(Boolean)
          .join(' · '),
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
    greenAreaNote:
      'Točka odabrana na karti, unutar parka ili šume; nema adrese do 150 m. Izvor: © OpenStreetMap contributors.',
    nearestNote: (m: number) =>
      m === 0
        ? 'Točka odabrana na karti, na samoj adresi.'
        : `Najbliža adresa točki odabranoj na karti (${formatDistance(m)} zračnom linijom). Podaci se odnose na odabranu točku.`,
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
      /** Last 24 h at the nearest DHMZ station, with its own status (credit required by DHMZ). */
      dhmzTitle: 'Zadnja 24 sata',
      dhmzNote:
        'Ocjena prema dnevnim smjernicama SZO-a (2021.) za najlošiju tvar; ne ulazi u EkoSkor, koji koristi višemjesečni prosjek.',
      dhmzTooFewHours: 'Premalo satnih mjerenja za dnevni prosjek.',
      dhmz: (r: DhmzReading) => {
        const name = { pm10: 'PM10', pm2_5: 'PM2,5', no2: 'NO₂', o3: 'O₃' } as const;
        const who = { pm10: 45, pm2_5: 15, no2: 25, o3: null } as const; // WHO 2021, 24 h
        const parts = r.values.map((v) => {
          const limit = who[v.pollutant];
          return `${name[v.pollutant]} ${formatNumber(v.mean_24h_ug_m3)} µg/m³${limit ? ` (SZO: do ${limit})` : ''}`;
        });
        const last = r.values[0]?.latest_at_local ?? '';
        const [d, t] = last.split('T');
        const [, m, day] = (d ?? '').split('-');
        const when = d
          ? ` Zadnje mjerenje ${Number(day)}. ${Number(m)}. u ${Number((t ?? '0').slice(0, 2))} h.`
          : '';
        return `Državna postaja ${r.station.name} (${formatDistance(r.station.distance_m)}), prosjek: ${parts.join(', ')}.${when} Nevalidirani podaci (Izvor: DHMZ).`;
      },
      history: {
        show: 'Prikaži mjerenja po danima',
        hide: 'Sakrij mjerenja',
        loading: 'Učitavanje grafa…',
        pollutantsLegend: 'Onečišćujuća tvar',
        pollutant: { pm10: 'PM10', pm2_5: 'PM2,5', no2: 'NO₂', o3: 'O₃' } satisfies Record<
          Pollutant,
          string
        >,
        unit: 'µg/m³',
        guideline: (v: number) => `Smjernica SZO (2021.) za dnevni prosjek: ${v} µg/m³`,
        noGuideline: 'Za O₃ SZO daje smjernicu za 8-satni prosjek, ne dnevni, pa je graf nema.',
        summary: (from: string, to: string, max: number, maxDate: string) =>
          `Od ${formatDate(from)} do ${formatDate(to)} najviša dnevna vrijednost bila je ${formatNumber(max)} µg/m³ (${formatDate(maxDate)}).`,
        above: (n: number, limit: number) =>
          n === 0 ? `Nijedan dan iznad ${limit} µg/m³.` : `Dana iznad ${limit} µg/m³: ${n}.`,
        missing: (n: number) => `Dana bez mjerenja: ${n} (praznine na grafu).`,
        tableCaption: (pollutant: string) => `Dnevne vrijednosti, ${pollutant}`,
        date: 'Datum',
        value: 'Vrijednost (µg/m³)',
        noValue: 'nema mjerenja',
      },
    },
    mobility: {
      title: 'Zelena mobilnost',
      sentence: (l: MobilityLayer) => {
        const near = `${l.stops_300m} ${stopsWord(l.stops_300m)} ZET-a do 300 m, ${l.stops_500m} do 500 m.`;
        const name = l.nearest_stop.name ?? '';
        return `${near} Najbliže: ${name} (${formatDistance(l.nearest_stop.distance_m)}).`;
      },
      bike: (l: MobilityLayer) => {
        const b = l.nearest_bike_path;
        const s = l.nearest_bike_station;
        const stationName = s.name
          ? ` (${s.name}${s.racks === null ? '' : `, ${s.racks} stalaka`})`
          : '';
        return `Biciklistička staza ${formatDistance(b.distance_m)}${b.name ? ` (${b.name})` : ''}. Stanica javnih bicikala ${formatDistance(s.distance_m)}${stationName}.`;
      },
      parts: (l: MobilityLayer) =>
        `Ocjena: javni prijevoz ${l.transit_score} (4/5), bicikl ${l.bike_score} (1/5, računa se bliža od staze i stanice). Udaljenosti zračnom linijom.`,
    },
    green: {
      title: 'Zelenilo',
      sentence: (l: GreenLayer) => {
        const g = l.nearest;
        const what = g.name ?? (g.kind === 'park' ? 'park' : 'šuma');
        return g.distance_m === 0
          ? `Adresa je unutar zelene površine: ${what}.`
          : `Najbliži park ili šuma ${formatDistance(g.distance_m)} (zračnom linijom): ${what}.`;
      },
      note: () =>
        'Parkovi, šume, javni vrtovi i zaštićena područja od barem 0,5 ha. SZO za Europu preporučuje takvu površinu do 300 m od stana.',
    },
    unavailable: (l: UnavailableLayer) =>
      l.reason === 'timeout'
        ? 'Servis nije odgovorio na vrijeme. Ostali slojevi su prikazani.'
        : 'Podaci trenutno nisu dostupni. Ostali slojevi su prikazani.',
  },
} as const;
