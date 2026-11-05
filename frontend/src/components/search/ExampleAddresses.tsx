import { Link } from 'react-router';
import { hr } from '../../i18n/hr';
import { addressPath } from '../../routes';

export function ExampleAddresses() {
  return (
    <section aria-labelledby="examples-title" className="flex flex-col gap-3">
      <h2 id="examples-title" className="text-ink-muted">
        {hr.examples.title}
      </h2>
      <ul className="grid gap-3 sm:grid-cols-3">
        {hr.examples.items.map((ex) => (
          <li key={ex.label}>
            <Link
              to={addressPath(ex.lat, ex.lon, ex.label)}
              className="flex min-h-12 flex-col rounded-lg border border-border bg-surface px-4 py-3 transition-colors duration-150 hover:border-primary"
            >
              <span className="font-semibold">{ex.label}</span>
              <span className="text-sm text-ink-muted">{ex.note}</span>
            </Link>
          </li>
        ))}
      </ul>
    </section>
  );
}
