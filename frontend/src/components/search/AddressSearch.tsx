import { useId, useState } from 'react';
import type { KeyboardEvent } from 'react';
import { useNavigate } from 'react-router';
import type { GeocodeResult } from '../../api/types';
import { MIN_QUERY_LENGTH, useGeocode } from '../../hooks/useGeocode';
import { hr } from '../../i18n/hr';
import { addressPath } from '../../routes';

/** Address autocomplete (ARIA 1.2 combobox): arrows move, Enter picks, Escape closes. */
export function AddressSearch({ autoFocus = false }: { autoFocus?: boolean }) {
  const [text, setText] = useState('');
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(-1);
  const navigate = useNavigate();
  const ids = useId();
  const listId = `${ids}-list`;
  const { data, isError, isFetching, enabled, settled } = useGeocode(text);
  const results = enabled ? (data?.results ?? []) : [];

  const typed = text.trim().length;
  let message: string | null = null;
  if (typed > 0 && typed < MIN_QUERY_LENGTH) message = hr.search.hint;
  else if (isError) message = hr.search.error;
  else if (enabled && !data && isFetching) message = hr.search.loading;
  else if (enabled && settled && !isFetching && results.length === 0) message = hr.search.empty;
  const expanded = open && (results.length > 0 || message !== null);

  const choose = (r: GeocodeResult) => {
    setOpen(false);
    navigate(addressPath(r.lat, r.lon, r.label));
  };

  const onKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setOpen(true);
      setActive((i) => Math.min(i + 1, results.length - 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setActive((i) => Math.max(i - 1, -1));
    } else if (e.key === 'Enter') {
      const pick = results[active] ?? results[0];
      if (pick) {
        e.preventDefault();
        choose(pick);
      }
    } else if (e.key === 'Escape') {
      if (expanded) setOpen(false);
      else setText('');
    }
  };

  return (
    <div className="relative">
      <label htmlFor={`${ids}-input`} className="mb-2 block text-lg font-semibold">
        {hr.search.label}
      </label>
      <input
        id={`${ids}-input`}
        type="text"
        role="combobox"
        aria-expanded={expanded}
        aria-controls={listId}
        aria-autocomplete="list"
        aria-activedescendant={expanded && active >= 0 ? `${ids}-opt-${active}` : undefined}
        autoComplete="off"
        spellCheck={false}
        // autofocus only on the home page, where search is the one action
        autoFocus={autoFocus}
        placeholder={hr.search.placeholder}
        value={text}
        onChange={(e) => {
          setText(e.target.value);
          setActive(-1);
          setOpen(true);
        }}
        onFocus={() => setOpen(true)}
        onBlur={() => setOpen(false)}
        onKeyDown={onKeyDown}
        className="min-h-14 w-full rounded-lg border-2 border-border bg-surface px-4 text-lg text-ink placeholder:text-ink-muted focus:border-primary"
      />
      <div
        className={`absolute inset-x-0 top-full z-20 mt-2 overflow-hidden rounded-lg border border-border bg-surface shadow-lg ${expanded ? '' : 'hidden'}`}
      >
        <ul id={listId} role="listbox" aria-label={hr.search.label}>
          {results.map((r, i) => (
            <li
              key={`${r.label}-${r.lat}-${r.lon}`}
              id={`${ids}-opt-${i}`}
              role="option"
              aria-selected={i === active}
              // mousedown, not click: fires before the input's blur closes the list
              onMouseDown={(e) => {
                e.preventDefault();
                choose(r);
              }}
              onMouseEnter={() => setActive(i)}
              className={`flex min-h-12 cursor-pointer items-center justify-between gap-3 px-4 py-2 ${i === active ? 'bg-primary text-primary-ink' : ''}`}
            >
              <span>{r.label}</span>
              <span className={`text-sm ${i === active ? '' : 'text-ink-muted'}`}>
                {hr.search.kind[r.kind]}
              </span>
            </li>
          ))}
        </ul>
        {message && <p className="px-4 py-3 text-ink-muted">{message}</p>}
      </div>
      <p className="sr-only" aria-live="polite">
        {open && results.length > 0 ? hr.search.results(results.length) : (message ?? '')}
      </p>
    </div>
  );
}
