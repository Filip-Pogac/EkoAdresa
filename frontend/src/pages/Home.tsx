import { AddressSearch } from '../components/search/AddressSearch';
import { ExampleAddresses } from '../components/search/ExampleAddresses';
import { hr } from '../i18n/hr';

export function Home() {
  return (
    <main className="mx-auto flex w-full max-w-2xl flex-1 flex-col justify-center gap-8 px-4 py-10">
      <div className="flex flex-col gap-2">
        <h1 className="text-4xl font-bold text-primary">{hr.app.name}</h1>
        <p className="text-xl">{hr.app.tagline}</p>
        <p className="text-ink-muted">{hr.app.pilot}</p>
      </div>
      <AddressSearch autoFocus />
      <ExampleAddresses />
    </main>
  );
}
