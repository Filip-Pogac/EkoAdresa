import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter, Link, Route, Routes } from 'react-router';
import { hr } from './i18n/hr';
import { Address } from './pages/Address';
import { Home } from './pages/Home';

const queryClient = new QueryClient({
  defaultOptions: { queries: { refetchOnWindowFocus: false } },
});

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <div className="flex min-h-dvh flex-col">
          <header className="border-b border-border bg-surface">
            <div className="mx-auto flex w-full max-w-6xl items-center px-4">
              <Link
                to="/"
                aria-label={hr.app.home}
                className="flex min-h-12 items-center text-lg font-bold text-primary"
              >
                {hr.app.name}
              </Link>
            </div>
          </header>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/adresa" element={<Address />} />
          </Routes>
        </div>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
