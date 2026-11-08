import type { Layers, LayerName } from '../../api/types';
import { hr } from '../../i18n/hr';
import { AirHistory } from './AirHistory';
import { DhmzToday } from './DhmzToday';
import { layerSentences } from './layerText';
import { StatusBadge } from './StatusBadge';

export function LayerRow({ name, layers }: { name: LayerName; layers: Layers }) {
  const layer = layers[name];
  const [main, ...notes] = layerSentences(name, layers);
  const stale = 'stale' in layer && layer.stale ? hr.source.stale(layer.fetched_at) : null;
  return (
    <li className="flex flex-col gap-1 border-t border-border py-4 first:border-t-0">
      <div className="flex flex-wrap items-center justify-between gap-x-4 gap-y-1">
        <h3 className="text-lg font-semibold">{hr.layers[name].title}</h3>
        <StatusBadge status={layer.status} />
      </div>
      <p>{main}</p>
      {notes.map((note) => (
        <p key={note} className="text-sm text-ink-muted">
          {note}
        </p>
      ))}
      {stale && <p className="text-sm font-semibold text-ink">{stale}</p>}
      {name === 'air' && layers.air.status !== 'unavailable' && layers.air.dhmz?.values.length ? (
        <DhmzToday reading={layers.air.dhmz} />
      ) : null}
      {name === 'air' && layers.air.status !== 'unavailable' && (
        <AirHistory history={layers.air.history} />
      )}
    </li>
  );
}
