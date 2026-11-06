import type { DhmzReading } from '../../api/types';
import { hr } from '../../i18n/hr';
import { StatusBadge } from './StatusBadge';

/** Last 24 h at the nearest DHMZ station, with its own status; kept apart from EkoSkor. */
export function DhmzToday({ reading }: { reading: DhmzReading }) {
  const t = hr.layers.air;
  return (
    <section
      aria-label={t.dhmzTitle}
      className="mt-1 flex flex-col gap-1 rounded-lg border border-border p-3 text-sm"
    >
      <div className="flex flex-wrap items-center justify-between gap-x-4 gap-y-1">
        <h4 className="font-semibold">{t.dhmzTitle}</h4>
        <StatusBadge status={reading.status} />
      </div>
      <p>{t.dhmz(reading)}</p>
      <p className="text-ink-muted">
        {reading.status === 'unavailable' ? t.dhmzTooFewHours : t.dhmzNote}
      </p>
    </section>
  );
}
