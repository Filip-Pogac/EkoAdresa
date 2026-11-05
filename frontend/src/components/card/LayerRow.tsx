import type { Layers, LayerName } from '../../api/types';
import { hr } from '../../i18n/hr';
import { SourceBadge } from './SourceBadge';
import { StatusBadge } from './StatusBadge';

function sentences(name: LayerName, layers: Layers): string[] {
  switch (name) {
    case 'flood': {
      const l = layers.flood;
      return l.status === 'unavailable'
        ? [hr.layers.unavailable(l)]
        : [hr.layers.flood.sentence(l)];
    }
    case 'noise': {
      const l = layers.noise;
      return l.status === 'unavailable'
        ? [hr.layers.unavailable(l)]
        : [hr.layers.noise.sentence(l)];
    }
    case 'air': {
      const l = layers.air;
      return l.status === 'unavailable'
        ? [hr.layers.unavailable(l)]
        : [hr.layers.air.sentence(l), hr.layers.air.period(l)];
    }
    case 'waste': {
      const l = layers.waste;
      return l.status === 'unavailable'
        ? [hr.layers.unavailable(l)]
        : [hr.layers.waste.sentence(l), hr.layers.waste.period()];
    }
    case 'mobility': {
      const l = layers.mobility;
      return l.status === 'unavailable'
        ? [hr.layers.unavailable(l)]
        : [hr.layers.mobility.sentence(l)];
    }
  }
}

export function LayerRow({ name, layers }: { name: LayerName; layers: Layers }) {
  const layer = layers[name];
  const [main, ...notes] = sentences(name, layers);
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
      <SourceBadge sourceId={layer.source_id} />
    </li>
  );
}
