import { useQuery } from '@tanstack/react-query';
import { api } from '../api/client';
import type { Source } from '../api/types';

/** Source registry by id (GET /api/sources), fetched once per session. */
export function useSources() {
  return useQuery({
    queryKey: ['sources'],
    queryFn: ({ signal }) => api.sources(signal),
    staleTime: Infinity,
    select: (sources): Record<string, Source> => Object.fromEntries(sources.map((s) => [s.id, s])),
  });
}
