import { useQuery } from '@tanstack/react-query';
import { api } from '../api/client';
import { ErrorState } from '../components/common/ErrorState';
import { Skeleton } from '../components/common/Skeleton';
import { hr } from '../i18n/hr';

const t = hr.sources;

export function Sources() {
  const { data, error, isPending, refetch } = useQuery({
    queryKey: ['sources'],
    queryFn: ({ signal }) => api.sources(signal),
    staleTime: Infinity,
  });

  return (
    <main className="mx-auto flex w-full max-w-4xl flex-col gap-6 px-4 py-6">
      <div className="flex flex-col gap-1">
        <h1 className="text-3xl font-bold">{t.title}</h1>
        <p className="text-ink-muted">{t.intro}</p>
      </div>
      {isPending && <Skeleton label={t.loading} className="h-64 w-full" />}
      {error && (
        <ErrorState message={t.error} retryLabel={t.retry} onRetry={() => void refetch()} />
      )}
      {data && (
        <ul className="flex flex-col gap-4">
          {data.map((s) => (
            <li
              key={s.id}
              className="flex flex-col gap-2 rounded-lg border border-border bg-surface p-5"
            >
              <h2 className="text-lg font-semibold">{s.name}</h2>
              <dl className="grid gap-x-4 gap-y-1 sm:grid-cols-[10rem_1fr]">
                <dt className="text-ink-muted">{t.publisher}</dt>
                <dd>{s.publisher}</dd>
                <dt className="text-ink-muted">{t.usedFor}</dt>
                <dd>{s.used_for}</dd>
                <dt className="text-ink-muted">{t.licence}</dt>
                <dd>{s.licence ?? t.noLicence}</dd>
                <dt className="text-ink-muted">{t.dataAsOf}</dt>
                <dd>
                  {s.data_as_of} · {t.access[s.access]}
                </dd>
                <dt className="text-ink-muted">{t.links}</dt>
                <dd className="flex flex-col">
                  {s.urls.map((url) => (
                    <a
                      key={url}
                      href={url}
                      rel="noreferrer"
                      target="_blank"
                      className="break-all text-accent underline"
                    >
                      {url}
                    </a>
                  ))}
                </dd>
              </dl>
              <p className="text-sm text-ink-muted">
                <code>{s.id}</code>
              </p>
            </li>
          ))}
        </ul>
      )}
    </main>
  );
}
