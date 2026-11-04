import { AddressMap } from './components/map/AddressMap';
import { hr } from './i18n/hr';

export function App() {
  return (
    <div className="mx-auto flex min-h-dvh max-w-6xl flex-col gap-4 p-4">
      <header>
        <h1 className="text-2xl font-bold text-primary">{hr.app.name}</h1>
        <p className="text-ink-muted">{hr.app.tagline}</p>
      </header>
      <main className="flex flex-1 flex-col">
        <AddressMap />
      </main>
    </div>
  );
}
