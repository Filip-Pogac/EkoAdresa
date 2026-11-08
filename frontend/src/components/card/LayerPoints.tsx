import { hr } from '../../i18n/hr';

/** A layer's points next to its status badge ("76/100"), so "Dobro" is not read as 100. */
export function LayerPoints({ score }: { score: number }) {
  return (
    <span className="text-sm font-semibold text-ink-muted">
      <span aria-hidden="true">{hr.layers.points(score)}</span>
      <span className="sr-only">{hr.layers.pointsLabel(score)}</span>
    </span>
  );
}
