import type { LayerName, Profile } from '../../api/types';
import { hr } from '../../i18n/hr';
import { Skeleton } from '../common/Skeleton';
import { EkoSkorRing } from './EkoSkorRing';
import { LayerRow } from './LayerRow';

const LAYER_ORDER: LayerName[] = ['flood', 'noise', 'air', 'waste', 'mobility'];

export function AddressCard({ profile }: { profile: Profile }) {
  return (
    <section
      aria-labelledby="card-title"
      className="flex flex-col gap-4 rounded-lg border border-border bg-surface p-5"
    >
      <h2 id="card-title" className="sr-only">
        {hr.card.title}
      </h2>
      <EkoSkorRing score={profile.ekoskor} />
      <p className="text-center text-ink-muted">
        {profile.ekoskor === null ? hr.ekoskor.missing : hr.ekoskor.explain}
      </p>
      <ul>
        {LAYER_ORDER.map((name) => (
          <LayerRow key={name} name={name} layers={profile.layers} />
        ))}
      </ul>
    </section>
  );
}

export function AddressCardSkeleton() {
  return (
    <div className="flex flex-col gap-4 rounded-lg border border-border bg-surface p-5">
      <Skeleton label={hr.card.loading} className="mx-auto size-[168px] !rounded-full" />
      {LAYER_ORDER.map((name) => (
        <div
          key={name}
          className="flex flex-col gap-2 border-t border-border pt-4"
          aria-hidden="true"
        >
          <div className="h-6 w-40 animate-pulse rounded bg-skeleton motion-reduce:animate-none" />
          <div className="h-4 w-full animate-pulse rounded bg-skeleton motion-reduce:animate-none" />
        </div>
      ))}
    </div>
  );
}
