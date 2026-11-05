import { useEffect, useState } from 'react';
import { hr } from '../../i18n/hr';

const SIZE = 168;
const STROKE = 14;
const R = (SIZE - STROKE) / 2;
const CIRCUMFERENCE = 2 * Math.PI * R;

/** EkoSkor 0-100 as a ring; fills once on mount (CSS transition, off with reduced motion). */
export function EkoSkorRing({ score }: { score: number | null }) {
  const [shown, setShown] = useState(0);
  useEffect(() => {
    const id = requestAnimationFrame(() => setShown(score ?? 0));
    return () => cancelAnimationFrame(id);
  }, [score]);

  return (
    <div className="flex w-full flex-col items-center gap-2">
      {/* SIZE px at most, smaller in a narrow column (two rings side by side on a phone) */}
      <div
        className="relative aspect-square w-full"
        style={{ maxWidth: SIZE }}
        role="img"
        aria-label={score === null ? hr.ekoskor.missing : hr.ekoskor.aria(score)}
      >
        <svg
          viewBox={`0 0 ${SIZE} ${SIZE}`}
          className="h-full w-full -rotate-90"
          aria-hidden="true"
        >
          <circle
            cx={SIZE / 2}
            cy={SIZE / 2}
            r={R}
            fill="none"
            strokeWidth={STROKE}
            className="stroke-border"
          />
          <circle
            cx={SIZE / 2}
            cy={SIZE / 2}
            r={R}
            fill="none"
            strokeWidth={STROKE}
            strokeLinecap="round"
            className="stroke-primary transition-[stroke-dashoffset] duration-[250ms] ease-out"
            strokeDasharray={CIRCUMFERENCE}
            strokeDashoffset={CIRCUMFERENCE * (1 - shown / 100)}
          />
        </svg>
        <div
          className="absolute inset-0 flex flex-col items-center justify-center"
          aria-hidden="true"
        >
          <span className="text-4xl font-bold tabular-nums sm:text-5xl">{score ?? '–'}</span>
          <span className="text-sm text-ink-muted">{hr.ekoskor.outOf}</span>
        </div>
      </div>
      <p className="text-lg font-semibold">{hr.ekoskor.name}</p>
    </div>
  );
}
