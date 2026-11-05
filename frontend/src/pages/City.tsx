import { HEATMAP_CLASSES } from '../components/city/heatmapClasses';
import { HeatmapView } from '../components/city/HeatmapView';
import { ErrorState } from '../components/common/ErrorState';
import { Skeleton } from '../components/common/Skeleton';
import { useHeatmap } from '../hooks/useHeatmap';
import { hr } from '../i18n/hr';

export function City() {
  const { data, error, isPending, refetch } = useHeatmap();
  return (
    <main className="mx-auto flex w-full max-w-6xl flex-col gap-4 px-4 py-6">
      <div className="flex flex-col gap-1">
        <h1 className="text-3xl font-bold">{hr.city.title}</h1>
        <p className="text-ink-muted">{hr.city.intro}</p>
      </div>
      {isPending && <Skeleton label={hr.city.loading} className="h-[70dvh] w-full" />}
      {error && (
        <ErrorState
          message={hr.city.error}
          retryLabel={hr.city.retry}
          onRetry={() => void refetch()}
        />
      )}
      {data && <HeatmapView data={data} />}
      <div className="flex flex-col gap-2">
        <p className="font-semibold">{hr.city.legend}</p>
        <ul className="flex flex-wrap gap-x-4 gap-y-1">
          {HEATMAP_CLASSES.map((c) => (
            <li key={c.from} className="flex items-center gap-2 text-sm">
              <span
                aria-hidden="true"
                className="size-4 rounded-sm border border-border"
                style={{ background: c.colour }}
              />
              {c.from}–{c.to}
            </li>
          ))}
        </ul>
        <p className="text-sm text-ink-muted">{hr.city.noteNoise}</p>
        <p className="text-sm text-ink-muted">{hr.city.noPopulation}</p>
      </div>
    </main>
  );
}
