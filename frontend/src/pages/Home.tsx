import { lazy, Suspense } from 'react';
import { useNavigate } from 'react-router';
import { Skeleton } from '../components/common/Skeleton';
import { LoadOnIntent } from '../components/common/LoadOnIntent';
import { AddressSearch } from '../components/search/AddressSearch';
import { ExampleAddresses } from '../components/search/ExampleAddresses';
import { hr } from '../i18n/hr';
import { addressPath } from '../routes';

// MapLibre is the biggest dependency: loaded only once the user interacts with the page
// near the map, or presses "Prikaži kartu" (LoadOnIntent), so the first screen and the
// search box are never held up by it (Lighthouse, CLAUDE.md §2.6)
const AddressMap = lazy(() =>
  import('../components/map/AddressMap').then((m) => ({ default: m.AddressMap })),
);

const mapLoading = <Skeleton label={hr.map.loading} className="h-80 w-full lg:h-[60dvh]" />;

/** Before the map loads: same size, a button to load it now (keyboard and screen readers). */
function MapPlaceholder({ load }: { load: () => void }) {
  return (
    <div className="flex h-80 w-full items-center justify-center rounded-lg border border-border bg-surface lg:h-[60dvh]">
      <button
        type="button"
        onClick={load}
        className="min-h-12 rounded-lg border border-primary px-5 font-semibold text-primary"
      >
        {hr.app.showMap}
      </button>
    </div>
  );
}

/** Three ways in: type an address, pick an example, or click anywhere on the map. */
export function Home() {
  const navigate = useNavigate();
  return (
    <main className="mx-auto flex w-full max-w-6xl flex-1 flex-col gap-8 px-4 py-10 lg:flex-row lg:items-start">
      <div className="flex flex-col gap-8 lg:w-[28rem] lg:shrink-0 lg:pt-8">
        <div className="flex flex-col gap-2">
          <h1 className="text-4xl font-bold text-primary">{hr.app.name}</h1>
          <p className="text-xl">{hr.app.tagline}</p>
          <p className="text-ink-muted">{hr.app.pilot}</p>
        </div>
        <AddressSearch autoFocus />
        <ExampleAddresses />
      </div>
      <section aria-labelledby="home-map-title" className="flex flex-1 flex-col gap-3">
        <h2 id="home-map-title" className="text-lg font-semibold">
          {hr.app.mapTitle}
        </h2>
        <LoadOnIntent placeholder={(load) => <MapPlaceholder load={load} />}>
          <Suspense fallback={mapLoading}>
            <AddressMap layers={false} onPick={(lat, lon) => navigate(addressPath(lat, lon))} />
          </Suspense>
        </LoadOnIntent>
      </section>
    </main>
  );
}
