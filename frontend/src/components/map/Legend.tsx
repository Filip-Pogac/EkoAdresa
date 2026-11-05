import { hr } from '../../i18n/hr';
import { FLOOD_DEPTHS, NOISE_BANDS, POINT_STYLE, type OverlayId } from './overlays';

function Swatches({ items }: { items: { label: string; colour: string }[] }) {
  return (
    <ul className="flex flex-wrap gap-x-4 gap-y-1">
      {items.map((item) => (
        <li key={item.label} className="flex items-center gap-2 text-sm">
          <span
            className="size-4 shrink-0 rounded-sm border border-border"
            style={{ background: item.colour }}
            aria-hidden="true"
          />
          {item.label}
        </li>
      ))}
    </ul>
  );
}

/** Legend for the active overlays; every colour has a text label next to it. */
export function Legend({ active }: { active: Set<OverlayId> }) {
  const points = (Object.keys(POINT_STYLE) as (keyof typeof POINT_STYLE)[]).filter((id) =>
    active.has(id),
  );
  if (active.size === 0) return null;
  return (
    <div className="flex flex-col gap-3 text-ink">
      {active.has('flood') && (
        <div className="flex flex-col gap-1">
          <p className="text-sm">{hr.map.legend.flood}</p>
          <Swatches items={FLOOD_DEPTHS} />
        </div>
      )}
      {active.has('noise') && (
        <div className="flex flex-col gap-1">
          <p className="text-sm">{hr.map.legend.noise}</p>
          <Swatches items={NOISE_BANDS} />
        </div>
      )}
      {points.length > 0 && (
        <ul className="flex flex-wrap gap-x-4 gap-y-1">
          {points.map((id) => (
            <li key={id} className="flex items-center gap-2 text-sm">
              <span
                className="size-4 shrink-0 rounded-full border-2 border-white"
                style={{ background: POINT_STYLE[id].colour }}
                aria-hidden="true"
              />
              {hr.map.overlays[id]}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
