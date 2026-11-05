import { useId, useRef } from 'react';
import { Link } from 'react-router';
import { hr } from '../../i18n/hr';

const t = hr.howWeScore;

const VARIANT = {
  nav: 'font-semibold text-ink',
  link: 'font-semibold text-accent underline',
};

/** "Kako računamo?" button + native <dialog> (focus trap, Escape and backdrop for free). */
export function HowWeScoreButton({ variant = 'link' }: { variant?: keyof typeof VARIANT }) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const titleId = useId(); // the button can appear twice on a page (header and card)
  const close = () => dialogRef.current?.close();
  return (
    <>
      <button
        type="button"
        onClick={() => dialogRef.current?.showModal()}
        className={`min-h-12 ${VARIANT[variant]}`}
      >
        {hr.nav.howWeScore}
      </button>
      <dialog
        ref={dialogRef}
        aria-labelledby={titleId}
        // click on the backdrop (the dialog element itself, outside its content) closes it
        onClick={(e) => {
          if (e.target === dialogRef.current) close();
        }}
        className="m-auto max-h-[90dvh] w-[min(48rem,calc(100vw-2rem))] rounded-lg border border-border bg-surface p-0 text-ink backdrop:bg-black/50"
      >
        <div className="flex flex-col gap-5 p-6">
          <div className="flex items-start justify-between gap-4">
            <h2 id={titleId} className="text-2xl font-bold">
              {t.title}
            </h2>
            <button
              type="button"
              onClick={close}
              className="min-h-12 min-w-12 shrink-0 rounded-lg border border-border px-3 font-semibold"
            >
              {t.close}
            </button>
          </div>
          <p>{t.intro}</p>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[36rem] border-collapse text-left text-sm">
              <caption className="mb-2 text-left font-semibold">{t.tableCaption}</caption>
              <thead>
                <tr className="border-b-2 border-border">
                  {Object.values(t.columns).map((c) => (
                    <th key={c} scope="col" className="py-2 pr-3">
                      {c}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {t.rows.map((r) => (
                  <tr key={r.layer} className="border-b border-border align-top">
                    <th scope="row" className="py-2 pr-3 font-semibold">
                      {r.layer}
                    </th>
                    <td className="py-2 pr-3">{r.weight}</td>
                    <td className="py-2 pr-3">{r.best}</td>
                    <td className="py-2 pr-3">{r.mid}</td>
                    <td className="py-2">{r.worst}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <section className="flex flex-col gap-1">
            <h3 className="font-semibold">{t.lightsTitle}</h3>
            <p>{t.lights}</p>
          </section>
          <section className="flex flex-col gap-1">
            <h3 className="font-semibold">{t.rulesTitle}</h3>
            <ul className="list-disc pl-5">
              {t.rules.map((r) => (
                <li key={r}>{r}</li>
              ))}
            </ul>
          </section>
          <section className="flex flex-col gap-1">
            <h3 className="font-semibold">{t.limitsTitle}</h3>
            <ul className="list-disc pl-5">
              {t.limits.map((r) => (
                <li key={r}>{r}</li>
              ))}
            </ul>
          </section>
          <Link to="/izvori" onClick={close} className="font-semibold text-accent underline">
            {t.sourcesLink}
          </Link>
        </div>
      </dialog>
    </>
  );
}
