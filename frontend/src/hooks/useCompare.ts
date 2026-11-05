import { useQuery } from '@tanstack/react-query';
import { api, ApiError, type LatLon } from '../api/client';

export function useCompare(a: LatLon | null, b: LatLon | null) {
  return useQuery({
    queryKey: ['compare', a?.lat, a?.lon, b?.lat, b?.lon],
    queryFn: ({ signal }) => {
      if (!a || !b) throw new Error('both points required'); // never: query is disabled
      return api.compare(a, b, signal);
    },
    enabled: a !== null && b !== null,
    staleTime: 10 * 60_000,
    // 422 = a point outside the pilot area: retrying cannot help
    retry: (count, error) => !(error instanceof ApiError && error.status < 500) && count < 2,
  });
}
