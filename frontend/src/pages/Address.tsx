import { lazy, Suspense } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router';
import { ApiError } from '../api/client';
import { AddressCard, AddressCardSkeleton } from '../components/card/AddressCard';
import { ErrorState } from '../components/common/ErrorState';
import { Skeleton } from '../components/common/Skeleton';
import { AddressSearch } from '../components/search/AddressSearch';
import { useProfile } from '../hooks/useProfile';
import { hr } from '../i18n/hr';
import { addressPath, comparePath, parseAddressParams } from '../routes';

// MapLibre is the biggest dependency: loaded only when a map is shown, so the home page
// stays light and the card can render before the map (Lighthouse, CLAUDE.md §2.6)
const AddressMap = lazy(() =>
  import('../components/map/AddressMap').then((m) => ({ default: m.AddressMap })),
);

function NewSearchLink() {
  return (
    <Link to="/" className="inline-flex min-h-12 items-center font-semibold text-accent underline">
      {hr.card.newSearch}
    </Link>
  );
}

function ProfilePanel({ lat, lon }: { lat: number; lon: number }) {
  const { data, error, isPending, refetch } = useProfile(lat, lon);
  if (isPending) return <AddressCardSkeleton />;
  if (error) {
    if (error instanceof ApiError && error.status === 422)
      return (
        <div
          role="alert"
          className="flex flex-col gap-2 rounded-lg border border-border bg-surface p-6"
        >
          <p>{hr.card.outside}</p>
          <NewSearchLink />
        </div>
      );
    return (
      <ErrorState
        message={hr.card.error}
        retryLabel={hr.card.retry}
        onRetry={() => void refetch()}
      />
    );
  }
  return <AddressCard profile={data} />;
}

export function Address() {
  const [params] = useSearchParams();
  const place = parseAddressParams(params);
  const navigate = useNavigate();
  if (!place)
    return (
      <main className="mx-auto w-full max-w-2xl px-4 py-10">
        <p>{hr.card.error}</p>
        <NewSearchLink />
      </main>
    );

  return (
    <main className="mx-auto flex w-full max-w-6xl flex-1 flex-col gap-4 px-4 py-4">
      <AddressSearch />
      <div className="flex flex-wrap items-center justify-between gap-x-4 gap-y-2">
        <h1 className="text-2xl font-bold">{place.label ?? hr.card.pinnedPoint}</h1>
        <Link
          to={comparePath(place, null)}
          className="inline-flex min-h-12 items-center rounded-lg bg-primary px-5 font-semibold text-primary-ink"
        >
          {hr.compare.start}
        </Link>
      </div>
      {/* Map first: on top on a phone, left of the card on desktop (CLAUDE.md §2.3) */}
      <div className="flex flex-1 flex-col gap-4 lg:flex-row lg:items-start">
        <div className="flex lg:sticky lg:top-4 lg:flex-1">
          <Suspense fallback={<Skeleton label={hr.map.loading} className="h-80 w-full" />}>
            <AddressMap
              point={{ lat: place.lat, lon: place.lon }}
              onPick={(lat, lon) => navigate(addressPath(lat, lon))}
            />
          </Suspense>
        </div>
        <div className="lg:w-[28rem] lg:shrink-0">
          <ProfilePanel lat={place.lat} lon={place.lon} />
        </div>
      </div>
    </main>
  );
}
