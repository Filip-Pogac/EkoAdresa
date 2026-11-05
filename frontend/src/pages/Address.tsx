import { Link, useSearchParams } from 'react-router';
import { ApiError } from '../api/client';
import { AddressCard, AddressCardSkeleton } from '../components/card/AddressCard';
import { ErrorState } from '../components/common/ErrorState';
import { AddressMap } from '../components/map/AddressMap';
import { AddressSearch } from '../components/search/AddressSearch';
import { useProfile } from '../hooks/useProfile';
import { hr } from '../i18n/hr';
import { parseAddressParams } from '../routes';

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
      <h1 className="text-2xl font-bold">{place.label ?? hr.card.pinnedPoint}</h1>
      <div className="flex flex-1 flex-col gap-4 lg:flex-row-reverse lg:items-start">
        <div className="lg:w-[28rem] lg:shrink-0">
          <ProfilePanel lat={place.lat} lon={place.lon} />
        </div>
        <div className="flex h-80 lg:sticky lg:top-4 lg:h-[calc(100dvh-2rem)] lg:flex-1">
          <AddressMap point={{ lat: place.lat, lon: place.lon }} />
        </div>
      </div>
    </main>
  );
}
