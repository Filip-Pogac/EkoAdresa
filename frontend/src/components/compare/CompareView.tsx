import type { Comparison } from '../../api/types';
import { hr } from '../../i18n/hr';
import { EkoSkorRing } from '../card/EkoSkorRing';
import { LAYER_ORDER } from '../card/layerText';
import { DiffRow } from './DiffRow';

interface CompareViewProps {
  comparison: Comparison;
  labels: { a: string; b: string };
}

export function CompareView({ comparison, labels }: CompareViewProps) {
  const diff = comparison.ekoskor_diff;
  const higher = diff === null || diff === 0 ? null : diff > 0 ? 'b' : 'a';
  return (
    <section
      aria-labelledby="compare-result"
      className="flex flex-col gap-4 rounded-lg border border-border bg-surface p-5"
    >
      <div className="grid grid-cols-2 gap-4">
        {(['a', 'b'] as const).map((key) => (
          <div
            key={key}
            className={`flex flex-col items-center gap-2 rounded-lg border-2 p-3 ${
              higher === key ? 'border-primary' : 'border-transparent'
            }`}
          >
            <p className="text-center font-semibold">{labels[key]}</p>
            <EkoSkorRing score={comparison[key].ekoskor} />
          </div>
        ))}
      </div>
      <p className="text-center text-lg font-semibold">
        {hr.compare.ekoskorDiff(diff, labels.a, labels.b)}
      </p>
      <h2 id="compare-result" className="text-xl font-bold">
        {hr.compare.layersTitle}
      </h2>
      <ul>
        {LAYER_ORDER.map((name) => (
          <DiffRow key={name} name={name} comparison={comparison} labels={labels} />
        ))}
      </ul>
    </section>
  );
}

export function CompareViewSkeleton() {
  return (
    <div className="grid grid-cols-2 gap-4 rounded-lg border border-border bg-surface p-5">
      {[0, 1].map((i) => (
        <div
          key={i}
          aria-hidden="true"
          className="mx-auto aspect-square w-full max-w-[168px] animate-pulse rounded-full bg-skeleton motion-reduce:animate-none"
        />
      ))}
      <p role="status" className="sr-only">
        {hr.compare.loading}
      </p>
    </div>
  );
}
