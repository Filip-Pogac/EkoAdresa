import { useQuery } from '@tanstack/react-query';
import { api, ApiError } from '../api/client';

export function useProfile(lat: number, lon: number) {
  return useQuery({
    queryKey: ['profile', lat, lon],
    queryFn: ({ signal }) => api.profile(lat, lon, signal),
    staleTime: 10 * 60_000,
    // 422 = outside the pilot area: retrying cannot help
    retry: (count, error) => !(error instanceof ApiError && error.status < 500) && count < 2,
  });
}
