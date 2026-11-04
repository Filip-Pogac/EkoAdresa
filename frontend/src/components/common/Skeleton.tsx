interface SkeletonProps {
  label: string;
  className?: string;
}

/** Placeholder block shown while content loads. `label` is announced to screen readers. */
export function Skeleton({ label, className = '' }: SkeletonProps) {
  return (
    <div
      role="status"
      aria-live="polite"
      className={`animate-pulse rounded-lg bg-skeleton motion-reduce:animate-none ${className}`}
    >
      <span className="sr-only">{label}</span>
    </div>
  );
}
