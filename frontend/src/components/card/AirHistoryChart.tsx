import { useId, useState } from 'react';
import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import type { AirValue, Pollutant } from '../../api/types';
import { formatNumber } from '../../format';
import { hr } from '../../i18n/hr';

const ORDER: Pollutant[] = ['pm10', 'pm2_5', 'no2', 'o3'];
/** WHO global air quality guidelines 2021, 24-hour mean, µg/m³. O3 has only an 8-hour one. */
const WHO_24H: Partial<Record<Pollutant, number>> = { pm10: 45, pm2_5: 15, no2: 25 };

const shortDate = (iso: string) => {
  const [, m, d] = iso.split('-');
  return `${Number(d)}. ${Number(m)}.`;
};

interface Point {
  date: string;
  value: number | null;
}

/** Daily values of the nearest City station, one pollutant at a time. Default export: lazy. */
export default function AirHistoryChart({ history }: { history: AirValue[] }) {
  const pollutants = ORDER.filter((p) => history.some((v) => v.pollutant === p));
  const [pollutant, setPollutant] = useState<Pollutant>(pollutants[0] ?? 'pm10');
  const name = useId();
  const t = hr.layers.air.history;

  // Every date in the period, so a day without a measurement is a gap, not a straight line
  const dates = [...new Set(history.map((v) => v.date))].sort();
  const byDate = new Map(
    history.filter((v) => v.pollutant === pollutant).map((v) => [v.date, v.value_ug_m3]),
  );
  const data: Point[] = dates.map((date) => ({ date, value: byDate.get(date) ?? null }));
  const measured = data.filter((d): d is { date: string; value: number } => d.value !== null);
  const max = measured.reduce<(typeof measured)[number] | undefined>(
    (a, b) => (a === undefined || b.value > a.value ? b : a),
    undefined,
  );
  const limit = WHO_24H[pollutant];
  const first = dates[0];
  const last = dates[dates.length - 1];
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  return (
    <div className="flex flex-col gap-3">
      <fieldset>
        <legend className="sr-only">{t.pollutantsLegend}</legend>
        <div className="flex flex-wrap gap-2">
          {pollutants.map((p) => (
            <label
              key={p}
              className="flex min-h-12 min-w-12 cursor-pointer items-center justify-center rounded-lg border border-border px-3 font-semibold has-[:checked]:border-primary has-[:checked]:bg-primary has-[:checked]:text-primary-ink has-[:focus-visible]:outline-3 has-[:focus-visible]:outline-accent"
            >
              <input
                type="radio"
                name={name}
                value={p}
                checked={p === pollutant}
                onChange={() => setPollutant(p)}
                className="sr-only"
              />
              {t.pollutant[p]}
            </label>
          ))}
        </div>
      </fieldset>

      {max && first && last && (
        <p>
          {t.summary(first, last, max.value, max.date)}{' '}
          {limit !== undefined && t.above(measured.filter((d) => d.value > limit).length, limit)}{' '}
          {measured.length < dates.length && t.missing(dates.length - measured.length)}
        </p>
      )}

      <div className="h-56 w-full" aria-hidden="true">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: -16 }}>
            <CartesianGrid stroke="var(--color-border)" vertical={false} />
            <XAxis
              dataKey="date"
              tickFormatter={shortDate}
              tick={{ fill: 'var(--color-ink-muted)', fontSize: 13 }}
              stroke="var(--color-border)"
              minTickGap={16}
            />
            <YAxis
              tick={{ fill: 'var(--color-ink-muted)', fontSize: 13 }}
              stroke="var(--color-border)"
              // round up to a multiple of 10 so the ticks are round numbers
              domain={[
                0,
                (dataMax: number) => Math.ceil((Math.max(dataMax, limit ?? 0) * 1.1) / 10) * 10,
              ]}
              allowDecimals={false}
            />
            <Tooltip
              formatter={(value) => [
                `${formatNumber(Number(value))} ${t.unit}`,
                t.pollutant[pollutant],
              ]}
              labelFormatter={(label) => shortDate(String(label))}
              contentStyle={{
                background: 'var(--color-surface)',
                border: '1px solid var(--color-border)',
                color: 'var(--color-ink)',
              }}
            />
            {limit !== undefined && (
              <ReferenceLine y={limit} stroke="var(--color-ink-muted)" strokeDasharray="6 4" />
            )}
            <Line
              type="monotone"
              dataKey="value"
              stroke="var(--color-accent)"
              strokeWidth={2.5}
              dot={{ r: 2.5, fill: 'var(--color-accent)' }}
              connectNulls={false}
              isAnimationActive={!reduceMotion}
              animationDuration={250}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
      <p className="text-sm text-ink-muted">
        {limit !== undefined ? (
          <>
            <span
              aria-hidden="true"
              className="mr-2 inline-block w-6 border-t-2 border-dashed border-ink-muted align-middle"
            />
            {t.guideline(limit)}
          </>
        ) : (
          t.noGuideline
        )}
      </p>

      <table className="sr-only">
        <caption>{t.tableCaption(t.pollutant[pollutant])}</caption>
        <thead>
          <tr>
            <th scope="col">{t.date}</th>
            <th scope="col">{t.value}</th>
          </tr>
        </thead>
        <tbody>
          {data.map((d) => (
            <tr key={d.date}>
              <td>{shortDate(d.date)}</td>
              <td>{d.value === null ? t.noValue : formatNumber(d.value)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
