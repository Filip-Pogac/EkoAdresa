import { useSearchParams } from 'react-router';
import { ApiError } from '../api/client';
import type { GeocodeResult } from '../api/types';
import { ErrorState } from '../components/common/ErrorState';
import { CompareView, CompareViewSkeleton } from '../components/compare/CompareView';
import { AddressSearch } from '../components/search/AddressSearch';
import { useCompare } from '../hooks/useCompare';
import { usePlaceTitle } from '../hooks/usePlaceTitle';
import { hr } from '../i18n/hr';
import { comparePath, parseCompareParams, type Place } from '../routes';

type Slot = 'a' | 'b';

interface SlotPickerProps {
  slot: Slot;
  place: Place | null;
  onPick: (r: GeocodeResult) => void;
  onClear: () => void;
}

function PlaceName({ place }: { place: Place }) {
  const { title, note } = usePlaceTitle(place);
  return (
    <>
      <p className="font-semibold">{title}</p>
      {note && <p className="text-sm text-ink-muted">{note}</p>}
    </>
  );
}

function SlotPicker({ slot, place, onPick, onClear }: SlotPickerProps) {
  if (!place) return <AddressSearch label={hr.compare.searchLabel[slot]} onSelect={onPick} />;
  return (
    <div className="flex min-h-14 items-center justify-between gap-3 self-end rounded-lg border border-border bg-surface px-4 py-2">
      <div>
        <p className="text-sm text-ink-muted">{hr.compare.slot[slot]}</p>
        <PlaceName place={place} />
      </div>
      <button
        type="button"
        onClick={onClear}
        className="min-h-12 shrink-0 font-semibold text-accent underline"
      >
        {hr.compare.change}
      </button>
    </div>
  );
}

export function Compare() {
  const [params, setParams] = useSearchParams();
  const { a, b } = parseCompareParams(params);
  const { data, error, isPending, refetch } = useCompare(a, b);

  const update = (next: { a: Place | null; b: Place | null }) => {
    setParams(new URLSearchParams(comparePath(next.a, next.b).split('?')[1] ?? ''));
  };
  const pick = (slot: Slot) => (r: GeocodeResult) =>
    update({ a, b, [slot]: { lat: r.lat, lon: r.lon, label: r.label } });
  const clear = (slot: Slot) => () => update({ a, b, [slot]: null });

  const labels = {
    a: a?.label ?? hr.compare.slot.a,
    b: b?.label ?? hr.compare.slot.b,
  };

  let result = null;
  if (a && b) {
    const detail = error instanceof ApiError && error.status === 422 ? error.detail : null;
    if (isPending) result = <CompareViewSkeleton />;
    else if (detail === 'outside_pilot_area:a' || detail === 'outside_pilot_area:b')
      result = (
        <p role="alert" className="rounded-lg border border-border bg-surface p-6">
          {hr.compare.outside(detail.endsWith(':a') ? labels.a : labels.b)}
        </p>
      );
    else if (error)
      result = (
        <ErrorState
          message={hr.compare.error}
          retryLabel={hr.card.retry}
          onRetry={() => void refetch()}
        />
      );
    else result = <CompareView comparison={data} labels={labels} />;
  }

  return (
    <main className="mx-auto flex w-full max-w-5xl flex-col gap-6 px-4 py-6">
      <div className="flex flex-col gap-1">
        <h1 className="text-3xl font-bold">{hr.compare.title}</h1>
        <p className="text-ink-muted">{hr.compare.intro}</p>
      </div>
      <div className="grid gap-4 sm:grid-cols-2">
        <SlotPicker slot="a" place={a} onPick={pick('a')} onClear={clear('a')} />
        <SlotPicker slot="b" place={b} onPick={pick('b')} onClear={clear('b')} />
      </div>
      {result}
    </main>
  );
}
