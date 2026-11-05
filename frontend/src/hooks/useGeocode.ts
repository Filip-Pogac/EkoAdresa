import { keepPreviousData, useQuery } from '@tanstack/react-query';
import { api } from '../api/client';
import { useDebounced } from './useDebounced';

export const MIN_QUERY_LENGTH = 3; // backend /api/geocode min_length

/** Address suggestions for the typed text, debounced; disabled under 3 characters. */
export function useGeocode(text: string) {
  const q = useDebounced(text.trim(), 200);
  const enabled = q.length >= MIN_QUERY_LENGTH;
  const query = useQuery({
    queryKey: ['geocode', q],
    queryFn: ({ signal }) => api.geocode(q, signal),
    enabled,
    placeholderData: keepPreviousData,
    staleTime: Infinity, // the address index is a fixed snapshot
  });
  return { ...query, enabled, settled: q === text.trim() };
}
