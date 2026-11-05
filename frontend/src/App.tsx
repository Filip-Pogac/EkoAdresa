import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter, Link, NavLink, Route, Routes } from 'react-router';
import { HowWeScoreButton } from './components/common/HowWeScoreModal';
import { hr } from './i18n/hr';
import { Address } from './pages/Address';
import { City } from './pages/City';
import { Compare } from './pages/Compare';
import { Home } from './pages/Home';
import { Sources } from './pages/Sources';

const queryClient = new QueryClient({
  defaultOptions: { queries: { refetchOnWindowFocus: false } },
});

const NAV = [
  { to: '/usporedba', label: hr.nav.compare },
  { to: '/grad', label: hr.nav.city },
  { to: '/izvori', label: hr.nav.sources },
];

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <div className="flex min-h-dvh flex-col">
          <header className="border-b border-border bg-surface">
            <div className="mx-auto flex w-full max-w-6xl flex-wrap items-center justify-between gap-x-4 px-4">
              <Link
                to="/"
                aria-label={hr.app.home}
                className="flex min-h-12 items-center text-lg font-bold text-primary"
              >
                {hr.app.name}
              </Link>
              <nav aria-label={hr.nav.label}>
                <ul className="flex flex-wrap items-center gap-x-4">
                  {NAV.map((item) => (
                    <li key={item.to}>
                      <NavLink
                        to={item.to}
                        className={({ isActive }) =>
                          `flex min-h-12 items-center font-semibold ${isActive ? 'text-primary underline underline-offset-4' : 'text-ink'}`
                        }
                      >
                        {item.label}
                      </NavLink>
                    </li>
                  ))}
                  <li>
                    <HowWeScoreButton variant="nav" />
                  </li>
                </ul>
              </nav>
            </div>
          </header>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/adresa" element={<Address />} />
            <Route path="/usporedba" element={<Compare />} />
            <Route path="/grad" element={<City />} />
            <Route path="/izvori" element={<Sources />} />
          </Routes>
        </div>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
