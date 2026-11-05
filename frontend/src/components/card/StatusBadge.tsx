import type { Status } from '../../api/types';
import { hr } from '../../i18n/hr';

const DISC: Record<Status, string> = {
  green: 'bg-status-green text-white',
  yellow: 'bg-status-amber text-[#14211a]', // dark ink on amber (CLAUDE.md §2.3)
  red: 'bg-status-red text-white',
  unavailable: 'bg-border text-ink',
};

/** Icon shape per status, so the status never depends on colour alone. */
function Glyph({ status }: { status: Status }) {
  const common = {
    fill: 'none',
    stroke: 'currentColor',
    strokeWidth: 3,
    strokeLinecap: 'round',
  } as const;
  switch (status) {
    case 'green':
      return <path d="M6 12.5l4 4 8-9" {...common} strokeLinejoin="round" />;
    case 'yellow':
      return <path d="M7 12h10" {...common} />;
    case 'red':
      return <path d="M7.5 7.5l9 9M16.5 7.5l-9 9" {...common} />;
    case 'unavailable':
      return (
        <path
          d="M9.5 9.5a2.5 2.5 0 1 1 3.5 2.3c-.6.3-1 .8-1 1.5M12 17h.01"
          {...common}
          strokeWidth={2.5}
        />
      );
  }
}

export function StatusBadge({ status }: { status: Status }) {
  return (
    <span className="inline-flex items-center gap-2 font-semibold text-ink">
      <span
        className={`grid size-7 shrink-0 place-items-center rounded-full ${DISC[status]}`}
        aria-hidden="true"
      >
        <svg viewBox="0 0 24 24" className="size-5">
          <Glyph status={status} />
        </svg>
      </span>
      {hr.status[status]}
    </span>
  );
}
