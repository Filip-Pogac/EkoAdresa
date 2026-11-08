import type { Comparison, LayerName } from '../../api/types';
import { hr } from '../../i18n/hr';
import { layerSentences } from '../card/layerText';
import { LayerPoints } from '../card/LayerPoints';
import { StatusBadge } from '../card/StatusBadge';

interface DiffRowProps {
  name: LayerName;
  comparison: Comparison;
  labels: { a: string; b: string };
}

function BetterBadge() {
  return (
    <span className="inline-flex items-center gap-1 rounded-full bg-primary px-3 py-1 text-sm font-semibold text-primary-ink">
      <svg viewBox="0 0 24 24" aria-hidden="true" className="size-4">
        <path
          d="M12 19V5M6 11l6-6 6 6"
          fill="none"
          stroke="currentColor"
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
      {hr.compare.better}
    </span>
  );
}

/** One layer for both addresses; the better side gets a border and a "Bolje" label. */
export function DiffRow({ name, comparison, labels }: DiffRowProps) {
  const diff = comparison.layers[name];
  const sides = [
    { key: 'a' as const, profile: comparison.a, label: labels.a },
    { key: 'b' as const, profile: comparison.b, label: labels.b },
  ];
  const comparable = diff.score_a !== null && diff.score_b !== null;
  return (
    <li className="flex flex-col gap-3 border-t border-border py-4 first:border-t-0">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h3 className="text-lg font-semibold">{hr.layers[name].title}</h3>
        {comparable && diff.better === null && (
          <span className="text-sm font-semibold text-ink-muted">{hr.compare.same}</span>
        )}
      </div>
      <div className="grid gap-3 sm:grid-cols-2">
        {sides.map(({ key, profile, label }) => {
          const better = diff.better === key;
          const [main] = layerSentences(name, profile.layers);
          return (
            <div
              key={key}
              className={`flex flex-col gap-2 rounded-lg border-2 p-3 ${better ? 'border-primary' : 'border-border'}`}
            >
              <div className="flex flex-wrap items-center justify-between gap-2">
                <span className="text-sm font-semibold text-ink-muted">{label}</span>
                {better && <BetterBadge />}
              </div>
              <div className="flex items-center gap-2">
                <StatusBadge status={profile.layers[name].status} />
                {'score' in profile.layers[name] && (
                  <LayerPoints score={profile.layers[name].score} />
                )}
              </div>
              <p>{main}</p>
            </div>
          );
        })}
      </div>
      {!comparable && <p className="text-sm text-ink-muted">{hr.compare.notCompared}</p>}
    </li>
  );
}
