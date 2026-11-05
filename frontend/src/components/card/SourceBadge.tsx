import { useSources } from '../../hooks/useSources';
import { hr } from '../../i18n/hr';

/** "Izvor: <publisher>, <dataset>" for a source_id; falls back to the id while loading. */
export function SourceBadge({ sourceId }: { sourceId: string }) {
  const { data } = useSources();
  const source = data?.[sourceId];
  return (
    <p className="text-sm text-ink-muted">
      {hr.source.prefix} {source ? `${source.publisher}, ${source.name}` : sourceId}
    </p>
  );
}
