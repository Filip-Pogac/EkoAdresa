interface ErrorStateProps {
  message: string;
  retryLabel: string;
  onRetry: () => void;
}

export function ErrorState({ message, retryLabel, onRetry }: ErrorStateProps) {
  return (
    <div
      role="alert"
      className="flex h-full flex-col items-center justify-center gap-4 rounded-lg border border-border bg-surface p-6 text-center"
    >
      <p className="max-w-sm text-ink">{message}</p>
      <button
        type="button"
        onClick={onRetry}
        className="min-h-12 rounded-lg bg-primary px-5 font-semibold text-primary-ink"
      >
        {retryLabel}
      </button>
    </div>
  );
}
