import { hr } from '../../i18n/hr';
import { OVERLAY_IDS, type OverlayId } from './overlays';

interface LayerToggleProps {
  active: Set<OverlayId>;
  failed: Set<OverlayId>;
  onToggle: (id: OverlayId) => void;
}

/** Checkboxes for the map overlays: native inputs, so keyboard and screen readers just work. */
export function LayerToggle({ active, failed, onToggle }: LayerToggleProps) {
  return (
    <fieldset className="flex flex-col gap-2">
      <legend className="mb-1 font-semibold">{hr.map.layersTitle}</legend>
      <div className="flex flex-wrap gap-2">
        {OVERLAY_IDS.map((id) => (
          <label
            key={id}
            className="flex min-h-12 cursor-pointer items-center gap-2 rounded-lg border border-border bg-surface px-3 has-[:checked]:border-primary"
          >
            <input
              type="checkbox"
              checked={active.has(id)}
              onChange={() => onToggle(id)}
              className="size-5 accent-[var(--color-primary)]"
            />
            {hr.map.overlays[id]}
          </label>
        ))}
      </div>
      {[...failed].map((id) => (
        <p key={id} role="alert" className="text-sm font-semibold">
          {hr.map.overlayError(hr.map.overlays[id])}
        </p>
      ))}
    </fieldset>
  );
}
