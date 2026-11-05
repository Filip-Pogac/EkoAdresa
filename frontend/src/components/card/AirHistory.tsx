import { lazy, Suspense, useId, useState } from 'react';
import type { AirValue } from '../../api/types';
import { hr } from '../../i18n/hr';
import { Skeleton } from '../common/Skeleton';

// Recharts is large: it is loaded only when someone opens the chart
const AirHistoryChart = lazy(() => import('./AirHistoryChart'));

/** "Show daily measurements" disclosure under the air row. */
export function AirHistory({ history }: { history: AirValue[] }) {
  const [open, setOpen] = useState(false);
  const panelId = useId();
  if (history.length === 0) return null;
  const t = hr.layers.air.history;
  return (
    <div className="flex flex-col gap-3">
      <button
        type="button"
        aria-expanded={open}
        aria-controls={panelId}
        onClick={() => setOpen((o) => !o)}
        className="flex min-h-12 items-center gap-2 self-start font-semibold text-accent underline"
      >
        <svg
          viewBox="0 0 24 24"
          aria-hidden="true"
          className={`size-5 transition-transform duration-150 ${open ? 'rotate-90' : ''}`}
        >
          <path d="M9 6l6 6-6 6" fill="none" stroke="currentColor" strokeWidth="2.5" />
        </svg>
        {open ? t.hide : t.show}
      </button>
      {open && (
        <div id={panelId}>
          <Suspense fallback={<Skeleton label={t.loading} className="h-72 w-full" />}>
            <AirHistoryChart history={history} />
          </Suspense>
        </div>
      )}
    </div>
  );
}
